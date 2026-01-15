#!/bin/bash

# Freight Route Optimizer - Startup Script for macOS/Linux
# This script starts both the API server and React frontend

echo "=========================================="
echo " Freight Route Optimizer - Starting..."
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if freight-ui directory exists
if [ ! -d "freight-ui" ]; then
    echo "Frontend directory 'freight-ui' not found!"
    echo "Would you like to create a new React TypeScript project? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Creating React TypeScript application..."
        npx create-react-app freight-ui --template typescript
        
        # Install additional dependencies
        echo ""
        echo "Installing additional dependencies..."
        cd freight-ui
        npm install axios react-router-dom @types/react-router-dom
        cd ..
        
        echo ""
        echo "✓ Frontend application created successfully!"
        echo ""
    else
        echo "Exiting. Please create the frontend manually."
        exit 1
    fi
fi

# Check if node_modules exists in freight-ui
if [ ! -d "freight-ui/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd freight-ui
    npm install
    cd ..
fi

# Start the Flask API server in the background
echo "Starting API server on port 5000..."
if [ -d ".venv" ]; then
    # Use virtual environment if it exists
    .venv/bin/python api_server.py &
else
    # Fall back to system python
    python3 api_server.py &
fi
API_PID=$!

# Wait a moment for API to initialize
sleep 3

# Start the React frontend
echo "Starting React frontend on port 3000..."
cd freight-ui

# Set environment variable to prevent auto-opening browser
export BROWSER=none

# Start React in the background
npm start &
FRONTEND_PID=$!

# Wait for React to compile
echo ""
echo "Waiting for React to compile (10 seconds)..."
sleep 10

# Open browser (macOS specific)
echo ""
echo "Opening browser at http://localhost:3000"
if command -v open &> /dev/null; then
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
fi

echo ""
echo "=========================================="
echo " Both servers are running!"
echo " - API Server:  http://localhost:5000"
echo " - Frontend:    http://localhost:3000"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop all servers..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    # Kill any remaining processes on ports 5000 and 3000
    lsof -ti:5000 | xargs kill -9 2>/dev/null
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    echo "Servers stopped."
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Wait for processes
wait

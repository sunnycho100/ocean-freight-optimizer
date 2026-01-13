# Google Maps Integration - "View Route" Feature

## Overview

The application now includes a **"View Route on Google Maps"** button that opens directions in a new tab - **no API key required, no billing, no setup!**

## How It Works

### User Experience
1. Select a destination and container type
2. Click "Apply" to see routes
3. In the route information panel (next to the table), click **"View Route on Google Maps"**
4. Google Maps opens in a new tab with driving directions from the POD to your destination

### Technical Details

**Location Cleaning:**
- Automatically removes region codes (HB, NW, BY, etc.) from location strings
- Example: "BREMERHAVEN, HB, GERMANY" → "BREMERHAVEN, GERMANY"
- Ensures Google Maps gets clean, recognizable city/country pairs

**URL Generation:**
- Uses Google Maps public URL API (no authentication needed)
- Format: `https://www.google.com/maps/dir/?api=1&origin=...&destination=...&travelmode=driving`
- Properly URL-encodes all special characters
- Opens with `noopener,noreferrer` for security

## Testing

### Browser Console Test
Open your browser's developer console and run:
```javascript
testGoogleMapsUrl()
```

This will output test results for:
- Le Havre, France → Bremerhaven, Germany
- BREMERHAVEN, HB, GERMANY → VALENCE, DROME, FRANCE
- MUENSTER, NW, GERMANY → ROTTERDAM, NETHERLANDS

### Manual Testing
1. Start the app (`.\start.bat`)
2. Select any destination
3. Click "View Route on Google Maps"
4. Verify Google Maps opens with correct route

## Files

- **`freight-ui/src/utils/googleMapsHelper.ts`** - Core utility functions
- **`freight-ui/src/utils/googleMapsHelper.test.ts`** - Unit tests
- **`freight-ui/src/components/RouteMap.tsx`** - Route viewer component
- **`freight-ui/src/styles/app.css`** - Styling for route info panel

## Benefits

✅ **No API Key Required** - Uses public Google Maps interface  
✅ **No Billing** - Completely free, no usage limits  
✅ **No Setup** - Works immediately out of the box  
✅ **Clean URLs** - Removes internal region codes for better results  
✅ **Secure** - Opens in new tab with proper security attributes  
✅ **Reusable** - Helper functions can be used anywhere in the app  

## Example URLs Generated

**Le Havre → Bremerhaven:**
```
https://www.google.com/maps/dir/?api=1&origin=Le+Havre%2C+France&destination=Bremerhaven%2C+Germany&travelmode=driving
```

**Muenster → Valence:**
```
https://www.google.com/maps/dir/?api=1&origin=MUENSTER%2C+GERMANY&destination=VALENCE%2C+FRANCE&travelmode=driving
```


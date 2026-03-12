import pandas as pd

# Verify the mock hapag file matches expected format
df = pd.read_excel('downloads/hapag_surcharges.xlsx', header=None, skiprows=4)
df.columns = ['From', 'To', 'Via', 'Description', 'Curr.', '20STD', '40STD', '40HC', 'Transport Remarks']

print("Shape:", df.shape)
print("Columns:", list(df.columns))
print()

# Check destinations
destinations = sorted(df['To'].unique().tolist())
print(f"Destinations ({len(destinations)}):")
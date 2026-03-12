import pandas as pd

df = pd.read_excel('downloads/ONE_Inland_Rate_Processed_20260311_183220.xlsx')

summary = df.groupby(['Destination','Container Type & Size']).agg(
    avg_inland=('Rate', 'mean'),
    min_inland=('Rate', 'min'),
    max_inland=('Rate', 'max'),
    avg_ocean=('Ocean Rate', 'mean'),
    pods=('POD', lambda x: ', '.join(x.unique()))
).reset_index()

for dest in ['VALENCE, DROME, FRANCE', 'MUENSTER, NW, GERMANY', 'OEGSTGEEST, NETHERLANDS', 'TEVEROLA, ITALY', 'KOBIERZYCE, POLAND', 'KOMAROM, HUNGARY', 'BAUMGARTENBERG, AUSTRIA', 'TAMPERE, FINLAND']:
    sub = summary[summary['Destination']==dest]
    if not sub.empty:
        print(f'=== {dest} ===')
        for _, r in sub.iterrows():
            print(f'  {r["Container Type & Size"]}: inland {r["min_inland"]}-{r["max_inland"]} (avg {r["avg_inland"]:.0f}), ocean avg {r["avg_ocean"]:.0f}')
            print(f'    PODs: {r["pods"]}')
        print()

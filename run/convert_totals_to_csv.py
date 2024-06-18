import json
import pandas as pd

# Load JSON data
with open('optimization_results.json', 'r') as file:
    data = json.load(file)

# Flatten the data and convert it to a DataFrame
rows = []
for entry in data:
    year = entry['year']
    CO2_price = entry['CO2_price']
    total_results = entry['results'].get('Total', {})
    row = {
        'year': year,
        'CO2_price': CO2_price,
        'total_cost': total_results.get('costs', None),
        'EU_TS_penalty': total_results.get('penalties', {}).get('EU TS', None),
        'FuelEU_penalty': total_results.get('penalties', {}).get('FuelEU', None)
    }
    rows.append(row)

# Create DataFrame
df = pd.DataFrame(rows)

# Save DataFrame to CSV
df.to_csv('total_output_results.csv', index=False)

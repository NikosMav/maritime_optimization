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
    for location in ['Intra', 'Inter', 'Berth']:
        scenario_results = entry['results'].get(location, {})
        row = {
            'year': year,
            'CO2_price': CO2_price,
            'location': location,
            'total_cost': scenario_results.get('costs', {}).get('total', None),
            'EU_TS_penalty': scenario_results.get('penalties', {}).get('EU TS', None),
            'FuelEU_penalty': scenario_results.get('penalties', {}).get('FuelEU', None)
        }
        if 'amounts' in scenario_results:
            for fuel, amount in scenario_results['amounts'].items():
                row[f'amount_{fuel}'] = amount
        rows.append(row)

# Create DataFrame
df = pd.DataFrame(rows)

# Save DataFrame to CSV
df.to_csv('output_results.csv', index=False)

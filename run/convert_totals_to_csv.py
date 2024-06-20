import json
import pandas as pd

# Load JSON data
with open('optimization_results.json', 'r') as file:
    data = json.load(file)

# Flatten the data and convert it to a DataFrame
rows = []
scenario_count = 0
for entry in data:
    scenario = entry['scenario']
    results = entry['results']
    year = scenario['year']
    CO2_price = scenario['CO2_price']
    total_results = results.get('Total', {})
    OPS_at_berth = scenario.get('OPS_at_berth', False)
    
    row = {
        'year': year,
        'CO2_price': CO2_price,
        'total_cost': total_results.get('costs', None),
        'EU_TS_penalty': total_results.get('penalties', {}).get('EU TS', None),
        'FuelEU_penalty': total_results.get('penalties', {}).get('FuelEU', None),
        'OPS_penalty': total_results.get('penalties', {}).get('OPS', None),
        'scenario': scenario_count % 4 + 1,  # Add a scenario identifier (0, 1, 2, 3)
        'OPS_at_berth': OPS_at_berth
    }
    rows.append(row)
    scenario_count += 1

# Create DataFrame
df = pd.DataFrame(rows)

# Save DataFrame to CSV
df.to_csv('total_output_results.csv', index=False)

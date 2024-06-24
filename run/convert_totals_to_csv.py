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

    # Handling different data types for total costs
    total_cost = total_results.get('costs', 0)
    if isinstance(total_cost, dict):
        total_cost = total_cost.get('total', 0)

    # Retrieve penalties
    EU_TS_penalty = total_results.get('penalties', {}).get('EU TS', 0)
    FuelEU_penalty = total_results.get('penalties', {}).get('FuelEU', 0)
    OPS_penalty = total_results.get('penalties', {}).get('OPS', 0)
    # Retrieve the OPS cost if available
    berth_results = results.get('Berth', {})
    OPS_cost = berth_results.get('OPS_cost', 0)
    
    # Fuel costs are calculated by subtracting all of the penalties and if OPS is enabled, then the OPS penalty and the OPS cost.
    fuel_costs = total_cost - (EU_TS_penalty + FuelEU_penalty + OPS_penalty + OPS_cost)

    row = {
        'year': year,
        'CO2_price': CO2_price,
        'total_cost': total_cost,
        'fuel_costs': fuel_costs,
        'EU_TS_penalty': EU_TS_penalty,
        'FuelEU_penalty': FuelEU_penalty,
        'OPS_penalty': OPS_penalty,
        'OPS_cost': OPS_cost,
        'scenario': scenario_count % 4 + 1,  # Add a scenario identifier (1, 2, 3, 4)
        'OPS_at_berth': OPS_at_berth
    }
    rows.append(row)
    scenario_count += 1

# Create DataFrame
df = pd.DataFrame(rows)

# Save DataFrame to CSV
df.to_csv('total_output_results.csv', index=False)

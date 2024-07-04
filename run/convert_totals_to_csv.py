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
    total_cost = results.get('total_cost', 0)
    FuelEU_penalty = results.get('FuelEU_penalty', 0)
    EU_ETS_penalty = results.get('EU_ETS_penalty', 0)
    OPS_cost = results.get('OPS_cost', 0)
    OPS_penalty = results.get('OPS_penalty', 0)
    OPS_at_berth = scenario.get('OPS_at_berth', False)

    # Calculate fuel costs
    fuel_costs = total_cost - (FuelEU_penalty + EU_ETS_penalty + OPS_cost + OPS_penalty)

    # Retrieve total fuel amounts
    fuel_amounts = results.get('fuel_amounts', {})

    # Create a row for each fuel type for detailed breakdown in the CSV
    for fuel, total_amount in fuel_amounts.items():
        row = {
            'year': year,
            'CO2_price': CO2_price,
            'total_cost': total_cost,
            'fuel_costs': fuel_costs,
            'EU_ETS_penalty': EU_ETS_penalty,
            'FuelEU_penalty': FuelEU_penalty,
            'OPS_penalty': OPS_penalty,
            'OPS_cost': OPS_cost,
            'fuel_type': fuel,
            'total_fuel_amount': total_amount,
            'scenario': scenario_count % 4 + 1,  # Add a scenario identifier (1, 2, 3, 4)
            'OPS_at_berth': OPS_at_berth
        }
        rows.append(row)
    scenario_count += 1

# Create DataFrame
df = pd.DataFrame(rows)

# Save DataFrame to CSV
df.to_csv('total_output_results.csv', index=False)

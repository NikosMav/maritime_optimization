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

    # Retrieve penalties and OPS costs
    EU_ETS_penalty = total_results.get('penalties', {}).get('EU ETS', 0)
    FuelEU_penalty = total_results.get('penalties', {}).get('FuelEU', 0)
    OPS_penalty = total_results.get('penalties', {}).get('OPS', 0)
    berth_results = results.get('Berth', {})
    OPS_cost = berth_results.get('OPS_cost', 0)

    # Calculate total fuel amounts from Intra, Inter, and possibly Berth
    fuel_totals = {}
    for trip_type in ['Intra', 'Inter', 'Berth']:
        if trip_type in results:
            for fuel, amount in results[trip_type].get('amounts', {}).items():
                if fuel in fuel_totals:
                    fuel_totals[fuel] += amount
                else:
                    fuel_totals[fuel] = amount

    # Calculate the fuel costs
    fuel_costs = total_cost - (EU_ETS_penalty + FuelEU_penalty + OPS_penalty + OPS_cost)

    # Create a row for each fuel type for detailed breakdown in the CSV
    for fuel, total_amount in fuel_totals.items():
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

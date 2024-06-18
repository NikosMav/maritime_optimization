import subprocess
import json
import ast

# Function to run a scenario
def run_scenario(scenario):
    cmd = ['python', '../code/optimize.py']
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Construct input for the subprocess
    inputs = (
        f"{scenario['year']}\n"
        f"{scenario['CO2_price']}\n"
        f"{scenario['Etotal_Intra']}\n"
        f"{scenario['MDO_tonnes_Intra']}\n"
        f"{len(scenario['fuel_types_Intra'])}\n"
        + "\n".join(scenario['fuel_types_Intra']) + "\n"
        f"{scenario['Etotal_Inter']}\n"
        f"{scenario['MDO_tonnes_Inter']}\n"
        f"{len(scenario['fuel_types_Inter'])}\n"
        + "\n".join(scenario['fuel_types_Inter']) + "\n"
        f"{scenario['Etotal_Berth']}\n"
    )

    output, errors = process.communicate(input=inputs)
    if process.returncode != 0:
        print("Error:", errors)

    return parse_output(output)

# Function to parse the output from optimize.py
def parse_output(output):
    results = {"Intra": {}, "Inter": {}, "Berth": {}}
    lines = output.splitlines()
    scenario_type = None

    for line in lines:
        line = line.strip()
        if "For intra-eu:" in line:
            scenario_type = "Intra"
        elif "For inter-eu:" in line:
            scenario_type = "Inter"
        elif "For Berth:" in line:
            scenario_type = "Berth"
        
        if scenario_type:
            if "Optimal fuel types" in line:
                results[scenario_type]["fuel_types"] = ast.literal_eval(line.split(':', 1)[1].strip())
            elif "Optimal percentages" in line:
                percentages = line.split(':', 1)[1].strip()
                results[scenario_type]["percentages"] = ast.literal_eval(percentages)
            elif "Optimal fuel amounts" in line:
                amounts = line.split(':', 1)[1].strip()
                results[scenario_type]["amounts"] = ast.literal_eval(amounts)
            elif "EU TS Penalty" in line or "FuelEU Penalty" in line:
                penalty_key = "EU TS" if "EU TS" in line else "FuelEU"
                penalty_value = float(line.split(':')[1].strip().split('€')[0])
                results[scenario_type]["penalties"] = results[scenario_type].get("penalties", {})
                results[scenario_type]["penalties"][penalty_key] = penalty_value
            elif "Optimal total cost" in line or "Total cost" in line:
                cost = float(line.split(':')[1].strip().split('€')[0])
                results[scenario_type]["costs"] = {"total": cost}

    return results

# Function to calculate total costs and penalties
def calculate_total_costs_and_penalties(results):
    total_costs = 0
    total_penalties = {
        "EU TS": 0,
        "FuelEU": 0
    }

    for trip_type in results:
        if "costs" in results[trip_type]:
            total_costs += results[trip_type]["costs"]["total"]
        if "penalties" in results[trip_type]:
            for penalty_type in results[trip_type]["penalties"]:
                total_penalties[penalty_type] += results[trip_type]["penalties"][penalty_type]

    return total_costs, total_penalties

# Base scenarios without year and CO2_price
base_scenarios = [
    {
        'Etotal_Intra': 300000000,
        'Etotal_Inter': 150000000,
        'Etotal_Berth': 70000000,
        'MDO_tonnes_Intra': 1500,
        'MDO_tonnes_Inter': 800,
        'fuel_types_Intra': ['VLSFO'],
        'fuel_types_Inter': ['VLSFO']
    },
    {
        'Etotal_Intra': 100000000,
        'Etotal_Inter': 50000000,
        'Etotal_Berth': 30000000,
        'MDO_tonnes_Intra': 1200,
        'MDO_tonnes_Inter': 600,
        'fuel_types_Intra': ['VLSFO', 'BIO-DIESEL'],
        'fuel_types_Inter': ['VLSFO', 'BIO-DIESEL']
    },
    {
        'Etotal_Intra': 45000000,
        'Etotal_Inter': 30000000,
        'Etotal_Berth': 17000000,
        'MDO_tonnes_Intra': 1000,
        'MDO_tonnes_Inter': 500,
        'fuel_types_Intra': ['LNG'],
        'fuel_types_Inter': ['LNG']
    },
    {
        'Etotal_Intra': 30000000,
        'Etotal_Inter': 15000000,
        'Etotal_Berth': 7000000,
        'MDO_tonnes_Intra': 600,
        'MDO_tonnes_Inter': 300,
        'fuel_types_Intra': ['E-METHANOL'],
        'fuel_types_Inter': ['E-METHANOL']
    }
]

# Results list
results = []

# Iterate over years and CO2 prices
for year in range(2025, 2051, 5):  # every 5 years
    for CO2_price in range(90, 191, 20):  # varying CO2 prices
        for base_scenario in base_scenarios:
            scenario = {**base_scenario, 'year': year, 'CO2_price': CO2_price}
            print(f"Running scenario for year {year} with CO2 price {CO2_price}")
            scenario_result = run_scenario(scenario)

            # Calculate total costs and penalties
            total_costs, total_penalties = calculate_total_costs_and_penalties(scenario_result)

            # Add summed up cost and penalties to the results
            scenario_result['Total'] = {
                'costs': total_costs,
                'penalties': total_penalties
            }

            results.append({
                'year': year,
                'CO2_price': CO2_price,
                'scenario': scenario,
                'results': scenario_result
            })

# Save the results to a JSON file
with open('optimization_results.json', 'w') as f:
    json.dump(results, f, indent=4)

print("All scenarios have been run. Check 'optimization_results.json' for the detailed results.")

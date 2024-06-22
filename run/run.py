import subprocess
import json
import ast

def run_scenario(scenario):
    cmd = ['python', '../code/optimize.py']
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    inputs = generate_input_from_scenario(scenario)
    output, errors = process.communicate(input=inputs)
    if process.returncode != 0:
        print("Error:", errors)
    return parse_output(output)

def generate_input_from_scenario(scenario):
    inputs = (
        f"{scenario['year']}\n"
        f"{scenario['CO2_price']}\n"
        f"{scenario['cost_per_MWh']}\n"
        f"{scenario['Etotal_Intra']}\n"
        f"{scenario['MDO_tonnes_Intra']}\n"
        f"{len(scenario['fuel_types_Intra'])}\n" + "\n".join(scenario['fuel_types_Intra']) + "\n"
        f"{scenario['Etotal_Inter']}\n"
        f"{scenario['MDO_tonnes_Inter']}\n"
        f"{len(scenario['fuel_types_Inter'])}\n" + "\n".join(scenario['fuel_types_Inter']) + "\n"
        f"{scenario['Etotal_Berth']}\n"
    )
    if scenario.get('OPS_at_berth', False):
        inputs += "yes\n" + f"{scenario['total_installed_power']}\n" + f"{scenario['established_power_demand']}\n" + f"{scenario['hours_at_berth']}\n"
    else:
        inputs += "no\n"
    return inputs

def parse_output(output):
    results = {"Intra": {}, "Inter": {}, "Berth": {}}
    lines = output.splitlines()
    trip_type = None

    for line in lines:
        line = line.strip()
        if "For intra-eu:" in line:
            trip_type = "Intra"
        elif "For inter-eu:" in line:
            trip_type = "Inter"
        elif "For Berth:" in line:
            trip_type = "Berth"

        if trip_type:
            if "Optimal fuel types" in line:
                results[trip_type]["fuel_types"] = ast.literal_eval(line.split(':', 1)[1].strip())
            elif "Optimal percentages" in line:
                results[trip_type]["percentages"] = ast.literal_eval(line.split(':', 1)[1].strip())
            elif "Optimal fuel amounts" in line:
                results[trip_type]["amounts"] = ast.literal_eval(line.split(':', 1)[1].strip())
            elif "EU TS Penalty" in line or "FuelEU Penalty" in line:
                penalty_key = "EU TS" if "EU TS" in line else "FuelEU"
                penalty_value = float(line.split(':')[1].strip().split('€')[0])
                results[trip_type]["penalties"] = results[trip_type].get("penalties", {})
                results[trip_type]["penalties"][penalty_key] = results[trip_type]["penalties"].get(penalty_key, 0) + penalty_value
            elif "OPS Penalty" in line:
                ops_penalty = float(line.split(':')[1].strip().split('€')[0])
                results[trip_type]["penalties"] = results[trip_type].get("penalties", {})
                results[trip_type]["penalties"]["OPS"] = results[trip_type]["penalties"].get("OPS", 0) + ops_penalty
            elif "OPS Cost" in line:
                ops_cost = float(line.split(':')[1].strip().split('€')[0])
                results[trip_type]["OPS_cost"] = ops_cost  # Store OPS cost separately
            elif "Optimal total cost" in line or "Total cost" in line:
                cost = float(line.split(':')[1].strip().split('€')[0])
                results[trip_type]["costs"] = {"total": cost}

    return results



def calculate_total_costs_and_penalties(results):
    total_costs = 0
    total_penalties = {}

    for trip_type, trip_results in results.items():
        if "costs" in trip_results:
            total_costs += trip_results["costs"]["total"]
        if "penalties" in trip_results:
            for penalty_type, penalty_value in trip_results["penalties"].items():
                total_penalties.setdefault(penalty_type, 0)
                total_penalties[penalty_type] += penalty_value

    return total_costs, total_penalties


# Base scenarios without year and CO2_price
base_scenarios = [
    {
        'Etotal_Intra': 14500000,
        'Etotal_Inter': 52000000,
        'Etotal_Berth': 14500000,
        'MDO_tonnes_Intra': 2,
        'MDO_tonnes_Inter': 250,
        'fuel_types_Intra': ['VLSFO'],
        'fuel_types_Inter': ['VLSFO']
    },
    {
        'Etotal_Intra': 14500000,
        'Etotal_Inter': 52000000,
        'Etotal_Berth': 14500000,
        'MDO_tonnes_Intra': 2,
        'MDO_tonnes_Inter': 250,
        'fuel_types_Intra': ['VLSFO', 'BIO-DIESEL'],
        'fuel_types_Inter': ['VLSFO', 'BIO-DIESEL']
    },
    {
        'Etotal_Intra': 14500000,
        'Etotal_Inter': 52000000,
        'Etotal_Berth': 14500000,
        'MDO_tonnes_Intra': 2,
        'MDO_tonnes_Inter': 250,
        'fuel_types_Intra': ['LNG'],
        'fuel_types_Inter': ['LNG']
    },
    {
        'Etotal_Intra': 14500000,
        'Etotal_Inter': 52000000,
        'Etotal_Berth': 14500000,
        'MDO_tonnes_Intra': 2,
        'MDO_tonnes_Inter': 250,
        'fuel_types_Intra': ['E-METHANOL'],
        'fuel_types_Inter': ['E-METHANOL']
    },

    # Base scenarios with OPS

    {
        'Etotal_Intra': 14500000,
        'Etotal_Inter': 52000000,
        'Etotal_Berth': 14500000,
        'MDO_tonnes_Intra': 2,
        'MDO_tonnes_Inter': 250,
        'fuel_types_Intra': ['VLSFO'],
        'fuel_types_Inter': ['VLSFO'],
        'OPS_at_berth': True,
        'total_installed_power': 1000,  # Example value
        'established_power_demand': 250,  # Example value
        'hours_at_berth': 48  # Example value
    },
    {
        'Etotal_Intra': 14500000,
        'Etotal_Inter': 52000000,
        'Etotal_Berth': 14500000,
        'MDO_tonnes_Intra': 2,
        'MDO_tonnes_Inter': 250,
        'fuel_types_Intra': ['VLSFO', 'BIO-DIESEL'],
        'fuel_types_Inter': ['VLSFO', 'BIO-DIESEL'],
        'OPS_at_berth': True,
        'total_installed_power': 1200,
        'established_power_demand': 300,
        'hours_at_berth': 48
    },
    {
        'Etotal_Intra': 14500000,
        'Etotal_Inter': 52000000,
        'Etotal_Berth': 14500000,
        'MDO_tonnes_Intra': 2,
        'MDO_tonnes_Inter': 250,
        'fuel_types_Intra': ['LNG'],
        'fuel_types_Inter': ['LNG'],
        'OPS_at_berth': True,
        'total_installed_power': 800,
        'established_power_demand': 200,
        'hours_at_berth': 48
    },
    {
        'Etotal_Intra': 14500000,
        'Etotal_Inter': 52000000,
        'Etotal_Berth': 14500000,
        'MDO_tonnes_Intra': 2,
        'MDO_tonnes_Inter': 250,
        'fuel_types_Intra': ['E-METHANOL'],
        'fuel_types_Inter': ['E-METHANOL'],
        'OPS_at_berth': True,
        'total_installed_power': 500,
        'established_power_demand': 125,
        'hours_at_berth': 48
    }
]

# Results list
results = []

# Constant cost per MWh
cost_per_MWh = 200.8

# Iterate over years and CO2 prices
for year in range(2025, 2051, 5):
    for CO2_price in range(90, 191, 20):
        scenario_count = 1
        for base_scenario in base_scenarios:
            if scenario_count > 4:
                scenario_count = 1
            scenario = {'year': year, 'CO2_price': CO2_price, 'cost_per_MWh': cost_per_MWh, **base_scenario}
            scenario_desc = "with OPS" if scenario.get("OPS_at_berth", False) else "without OPS"
            print(f"Running scenario {scenario_count} for year {year} with CO2 price {CO2_price} {scenario_desc}")
            scenario_count += 1
            scenario_result = run_scenario(scenario)  # Running scenario
            total_costs, total_penalties = calculate_total_costs_and_penalties(scenario_result)  # Calculate costs and penalties
            scenario_result['Total'] = {'costs': total_costs, 'penalties': total_penalties}
            results.append({
                'scenario': scenario,
                'results': scenario_result
            })

# Save the results to a JSON file
with open('optimization_results.json', 'w') as f:
    json.dump(results, f, indent=4)

print("All scenarios have been run. Check 'optimization_results.json' for the detailed results.")

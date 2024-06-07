import subprocess
import json
import ast

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
        f"{scenario['MDO_tonnes_Berth']}\n"
    )

    output, errors = process.communicate(input=inputs)
    if process.returncode != 0:
        print("Error:", errors)

    return parse_output(output)

import ast

def parse_output(output):
    results = {
        "Intra": {},
        "Inter": {},
        "Berth": {}
    }

    lines = output.splitlines()
    scenario_type = None  # Used to track the current scenario type

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
            elif "EU TS Penalty" in line:
                penalty_value = float(line.split(':')[1].strip().split('€')[0])
                results[scenario_type]["penalties"] = results[scenario_type].get("penalties", {})
                results[scenario_type]["penalties"]["EU TS"] = penalty_value
            elif "FuelEU Penalty" in line:
                penalty_value = float(line.split(':')[1].strip().split('€')[0])
                results[scenario_type]["penalties"] = results[scenario_type].get("penalties", {})
                results[scenario_type]["penalties"]["FuelEU"] = penalty_value
            elif "Optimal total cost" in line or "Total cost" in line:
                cost = float(line.split(':')[1].strip().split('€')[0])
                results[scenario_type]["costs"] = {"total": cost}

    return results



# Define scenarios
scenarios = [
    {
        'year': 2025,
        'CO2_price': 90,
        'Etotal_Intra': 546000000,
        'MDO_tonnes_Intra': 1400,
        'fuel_types_Intra': ['VLSFO'],
        'Etotal_Inter': 546000000,
        'MDO_tonnes_Inter': 1400,
        'fuel_types_Inter': ['VLSFO'],
        'Etotal_Berth': 50000000,
        'MDO_tonnes_Berth': 1500
    },
    {
        'year': 2025,
        'CO2_price': 90,
        'Etotal_Intra': 546000000,
        'MDO_tonnes_Intra': 1400,
        'fuel_types_Intra': ['VLSFO', 'BIO-DIESEL'],
        'Etotal_Inter': 546000000,
        'MDO_tonnes_Inter': 1400,
        'fuel_types_Inter': ['VLSFO', 'BIO-DIESEL'],
        'Etotal_Berth': 50000000,
        'MDO_tonnes_Berth': 1500
    },
    {
        'year': 2025,
        'CO2_price': 90,
        'Etotal_Intra': 100000000,
        'MDO_tonnes_Intra': 1200,
        'fuel_types_Intra': ['VLSFO'],
        'Etotal_Inter': 50000000,
        'MDO_tonnes_Inter': 600,
        'fuel_types_Inter': ['VLSFO'],
        'Etotal_Berth': 30000000,
        'MDO_tonnes_Berth': 700
    },
    {
        'year': 2030,
        'CO2_price': 120,
        'Etotal_Intra': 600000000,
        'MDO_tonnes_Intra': 1600,
        'fuel_types_Intra': ['BIO-DIESEL', 'LNG'],
        'Etotal_Inter': 300000000,
        'MDO_tonnes_Inter': 1600,
        'fuel_types_Inter': ['BIO-DIESEL', 'LNG'],
        'Etotal_Berth': 15000000,
        'MDO_tonnes_Berth': 1000
    },
    # Scenario with a focus on alternative fuels
    {
        'year': 2035,
        'CO2_price': 100,
        'Etotal_Intra': 450000000,
        'MDO_tonnes_Intra': 1000,
        'fuel_types_Intra': ['LNG', 'E-METHANOL'],
        'Etotal_Inter': 250000000,
        'MDO_tonnes_Inter': 1000,
        'fuel_types_Inter': ['LNG', 'E-METHANOL'],
        'Etotal_Berth': 10000000,
        'MDO_tonnes_Berth': 500
    },
    # Testing with a significantly different year and extreme CO2 price
    {
        'year': 2040,
        'CO2_price': 150,
        'Etotal_Intra': 700000000,
        'MDO_tonnes_Intra': 1800,
        'fuel_types_Intra': ['LNG', 'E-METHANOL'],
        'Etotal_Inter': 400000000,
        'MDO_tonnes_Inter': 1800,
        'fuel_types_Inter': ['LNG', 'E-METHANOL'],
        'Etotal_Berth': 20000000,
        'MDO_tonnes_Berth': 1300
    }
]

results = []

for scenario in scenarios:
    print(f"Running scenario: {scenario['year']} with CO2 price {scenario['CO2_price']}, Etotal_Intra {scenario['Etotal_Intra']}, Etotal_Inter {scenario['Etotal_Inter']}, Etotal_Berth {scenario['Etotal_Berth']}")
    result = run_scenario(scenario)
    results.append({
        'scenario': scenario,
        'results': result
    })

# Save the results to a JSON file for later analysis
with open('optimization_results.json', 'w') as f:
    json.dump(results, f, indent=4)

print("All scenarios have been run. Check 'optimization_results.json' for the detailed results.")

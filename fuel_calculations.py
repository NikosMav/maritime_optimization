import json

# Load WtW CO2e factors from a JSON file
def load_wtw_factors(filename='wtw_factors.json'):
    with open(filename, 'r') as file:
        wtw_factors = json.load(file)
    return {key.upper(): value for key, value in wtw_factors.items()}

# Load fuel data from JSON file
def load_fuel_data(filename='fuel_prices.json'):
    with open(filename, 'r') as file:
        fuel_data = json.load(file)
    return fuel_data

# Load fuel densities
def load_fuel_density(filename='fuel_density.json'):
    with open(filename, 'r') as file:
        return json.load(file)

# Constants from the equations
GHGi_target = 91.16 * 0.98  # Target GHGi

def calculate_fuel_costs(fuel_data, fuel_amounts_tonnes):
    total_fuel_costs = {'min': 0, 'max': 0, 'average': 0}
    for fuel_type, fuel_tonnes in fuel_amounts_tonnes.items():
        if fuel_type in fuel_data:
            prices = fuel_data[fuel_type]
            total_fuel_costs['min'] += prices['price_min'] * fuel_tonnes
            total_fuel_costs['max'] += prices['price_max'] * fuel_tonnes
            total_fuel_costs['average'] += ((prices['price_min'] + prices['price_max']) / 2) * fuel_tonnes
        else:
            raise ValueError(f"Fuel type '{fuel_type}' not found in the data.")
    return total_fuel_costs

def calculate_GHGi_actual(fuel_percentages, WtW_factors):
    total_GHG = sum((fuel_percentages[fuel] / 100) * WtW_factors[fuel] for fuel in fuel_percentages)
    GHGi_actual = total_GHG
    return GHGi_actual

def objective_function(GHGi_actual, E_total):
    CB = (GHGi_target - GHGi_actual) * E_total
    FuelEU = abs(CB) / (GHGi_actual * 41000) * 2400
    return CB, FuelEU

def calculate_costs_and_penalty(fuel_amounts_tonnes, E_total):
    fuel_data = load_fuel_data()
    wtw_factors = load_wtw_factors()

    journey_fuel_costs = calculate_fuel_costs(fuel_data, fuel_amounts_tonnes)

    total_fuel = sum(fuel_amounts_tonnes.values())
    fuel_percentages = {fuel: (amount / total_fuel) * 100 for fuel, amount in fuel_amounts_tonnes.items()}
    GHGi_actual = calculate_GHGi_actual(fuel_percentages, wtw_factors)
    CB, FuelEU = objective_function(GHGi_actual, E_total)

    print(f"Carbon Balance (CB): {CB:.2E} gCO2e")
    print(f"The FuelEU Penalty is: {FuelEU:.2f} €")
    return journey_fuel_costs, CB, FuelEU

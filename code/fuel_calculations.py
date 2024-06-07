import json

# Load WtW factors
def load_wtw_factors(filename='../json/wtw_factors.json'):
    with open(filename, 'r') as file:
        wtw_factors = json.load(file)
    return {key.upper(): value for key, value in wtw_factors.items()}

# Load fuel data
def load_fuel_data(filename='../json/fuel_prices.json'):
    with open(filename, 'r') as file:
        fuel_data = json.load(file)
    return fuel_data

# Load fuel densities
def load_fuel_density(filename='../json/fuel_density.json'):
    with open(filename, 'r') as file:
        return json.load(file)
    
# Load CO2 emission factors
def load_co2_emission_factors(filename='../json/co2_emission_factors.json'):
    with open(filename, 'r') as file:
        co2_factors = json.load(file)
    return {key.upper(): value for key, value in co2_factors.items()}

# Load GHG reduction targets
def load_ghgi_targets(filename='../json/ghgi_targets.json'):
    with open(filename, 'r') as file:
        ghgi_targets = json.load(file)
    return ghgi_targets

def set_GHGi_target(year):
    ghgi_targets = load_ghgi_targets()
    reference_value = ghgi_targets['reference_value']
    targets = ghgi_targets['targets']
    reduction_percentage = targets.get(str(year), 0)  # JSON keys are strings, ensure to match the type
    return reference_value * (1 - reduction_percentage / 100)

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

def calculate_fueleu(GHGi_actual, E_total, GHGi_target):
    CB = (GHGi_target - GHGi_actual) * E_total
    FuelEU = abs(CB) / (GHGi_actual * 41000) * 2400
    return CB, FuelEU

def calculate_CO2_emissions(fuel_amounts, co2_factors):
    total_CO2_emissions = 0
    for fuel, amount in fuel_amounts.items():
        # Ensure multiplication is correctly applying the tons CO2 per ton of fuel
        total_CO2_emissions += co2_factors.get(fuel.upper(), 0) * amount
    return total_CO2_emissions

def calculate_CO2_penalty(total_CO2_emissions, CO2_price_per_ton):
    CO2_penalty = total_CO2_emissions * CO2_price_per_ton
    return CO2_penalty

def calculate_costs_and_penalty(fuel_amounts_tonnes, E_total, year, CO2_price_per_ton):
    fuel_data = load_fuel_data()
    wtw_factors = load_wtw_factors()
    co2_factors = load_co2_emission_factors()

    journey_fuel_costs = calculate_fuel_costs(fuel_data, fuel_amounts_tonnes)
    total_CO2_emissions = calculate_CO2_emissions(fuel_amounts_tonnes, co2_factors)
    CO2_penalty = calculate_CO2_penalty(total_CO2_emissions, CO2_price_per_ton)
    #print(f"The EU TS Penalty is: {CO2_penalty:.2f} €")

    total_fuel = sum(fuel_amounts_tonnes.values())
    fuel_percentages = {fuel: (amount / total_fuel) * 100 for fuel, amount in fuel_amounts_tonnes.items()}
    GHGi_actual = calculate_GHGi_actual(fuel_percentages, wtw_factors)
    GHGi_target = set_GHGi_target(year)
    CB, FuelEU = calculate_fueleu(GHGi_actual, E_total, GHGi_target)
    #print(f"The FuelEU Penalty is: {FuelEU:.2f} €")

    return journey_fuel_costs, CB, FuelEU, CO2_penalty


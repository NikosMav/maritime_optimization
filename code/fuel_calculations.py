import json

############################## LOAD FUNCTIONS ##############################

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

###############################################################################

def calculate_fuel_costs(fuel_data, fuel_amounts_tonnes, year):
    total_fuel_costs = {'min': 0, 'max': 0, 'average': 0}
    for fuel_type, fuel_tonnes in fuel_amounts_tonnes.items():
        if fuel_type in fuel_data:
            # Try to get year-specific prices first
            prices = fuel_data[fuel_type].get(str(year))
            
            # If year-specific prices aren't available, use generic prices
            if not prices:
                if 'price_min' in fuel_data[fuel_type]:
                    # Generic prices exist
                    prices = fuel_data[fuel_type]
                else:
                    # No generic price; handle error
                    raise ValueError(f"No price data available for '{year}' or generic for '{fuel_type}'.")
            
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

def calculate_GHGi_target(year):
    ghgi_targets = load_ghgi_targets()
    reference_value = ghgi_targets['reference_value']
    targets = ghgi_targets['targets']
    reduction_percentage = targets.get(str(year), 0)  # JSON keys are strings, ensure to match the type
    adjusted_target = reference_value * (1 - reduction_percentage / 100)
    return adjusted_target

def calculate_Fuel_EU_Penalty(GHGi_actual, E_total, GHGi_target, fwind):
    CB = fwind * (GHGi_target - GHGi_actual) * E_total
    # Only calculate FuelEU penalty if CB is negative (non-compliant)
    if CB < 0:
        Fuel_EU_Penalty = abs(CB) / (GHGi_actual * 41000) * 2400
    else:
        Fuel_EU_Penalty = 0  # No penalty if compliant or better
    return CB, Fuel_EU_Penalty

# def Fuel_EU_Wrapper():

def calculate_CO2_emissions(fuel_amounts, co2_factors):
    total_CO2_emissions = 0
    for fuel, amount in fuel_amounts.items():
        # Ensure multiplication is correctly applying the tons CO2 per ton of fuel
        total_CO2_emissions += co2_factors.get(fuel.upper(), 0) * amount
    return total_CO2_emissions

def calculate_EU_ETS_Penalty(total_CO2_emissions, CO2_price_per_ton):
    EU_TS_Penalty = total_CO2_emissions * CO2_price_per_ton
    return EU_TS_Penalty

def calculate_costs_and_penalties(fuel_amounts_tonnes, E_total, year, CO2_price_per_ton, fwind):
    fuel_data = load_fuel_data()
    wtw_factors = load_wtw_factors()
    co2_factors = load_co2_emission_factors()

    # Include the year parameter when calculating fuel costs
    journey_fuel_costs = calculate_fuel_costs(fuel_data, fuel_amounts_tonnes, year)

    # Calculate EU ETS Penalty
    total_CO2_emissions = calculate_CO2_emissions(fuel_amounts_tonnes, co2_factors)
    EU_ETS_Penalty = calculate_EU_ETS_Penalty(total_CO2_emissions, CO2_price_per_ton)
     # If the year is 2025, apply a 30% reduction to the EU ETS Penalty
    if year == 2025:
        EU_ETS_Penalty *= 0.7

    total_fuel = sum(fuel_amounts_tonnes.values())
    fuel_percentages = {fuel: (amount / total_fuel) * 100 for fuel, amount in fuel_amounts_tonnes.items()}

    # Calculate compliance balance and FuelEU penalty
    GHGi_actual = calculate_GHGi_actual(fuel_percentages, wtw_factors)
    GHGi_target = calculate_GHGi_target(year)
    CB, Fuel_EU_Penalty = calculate_Fuel_EU_Penalty(GHGi_actual, E_total, GHGi_target, fwind)

    return journey_fuel_costs, CB, Fuel_EU_Penalty, EU_ETS_Penalty



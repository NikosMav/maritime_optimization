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

############################## FUEL EU PENENALTY ##############################
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

def calculate_total_Fuel_EU_Penalty(year, Etotal_Intra, Etotal_Inter, Etotal_Berth, fwind, fuel_percentages_intra, fuel_percentages_inter, fuel_percentages_berth):
    WtW_factors = load_wtw_factors()
    
    # Etotal_Inter gets halved only in the Fuel EU penalty calculation
    Etotal_Inter *= 0.5

    # Calculate total energy consumption
    summed_E_total = Etotal_Intra + Etotal_Inter + Etotal_Berth
    
    # Calculate weighted average GHGi_actual
    GHGi_actual_intra = calculate_GHGi_actual(fuel_percentages_intra, WtW_factors)
    GHGi_actual_inter = calculate_GHGi_actual(fuel_percentages_inter, WtW_factors)
    GHGi_actual_berth = calculate_GHGi_actual(fuel_percentages_berth, WtW_factors)
    
    weighted_GHGi_actual = (
        (GHGi_actual_intra * Etotal_Intra) +
        (GHGi_actual_inter * Etotal_Inter) +
        (GHGi_actual_berth * Etotal_Berth)
    ) / summed_E_total
    
    GHGi_target = calculate_GHGi_target(year)
    
    # Calculate the total FuelEU penalty
    total_CB, total_Fuel_EU_penalty = calculate_Fuel_EU_Penalty(weighted_GHGi_actual, summed_E_total, GHGi_target, fwind)
    
    return total_CB, total_Fuel_EU_penalty
###############################################################################

############################## FUEL COSTS ##############################
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
###############################################################################

############################## EU ETS PENALTY ##############################
def calculate_CO2_emissions(fuel_amounts, co2_factors):
    total_CO2_emissions = 0
    for fuel, amount in fuel_amounts.items():
        # Ensure multiplication is correctly applying the tons CO2 per ton of fuel
        total_CO2_emissions += co2_factors.get(fuel.upper(), 0) * amount
    return total_CO2_emissions

def calculate_EU_ETS_Penalty(total_CO2_emissions, CO2_price_per_ton):
    EU_TS_Penalty = total_CO2_emissions * CO2_price_per_ton
    return EU_TS_Penalty
###############################################################################

def calculate_total_fuel_costs_and_EU_ETS_penalties(year, CO2_price_per_ton, fuel_amounts_intra, fuel_amounts_inter, fuel_amounts_berth):
    fuel_data = load_fuel_data()
    co2_factors = load_co2_emission_factors()

    # Calculate fuel costs and EU ETS penalties for Intra trip
    fuel_costs_intra = calculate_fuel_costs(fuel_data, fuel_amounts_intra, year)
    total_CO2_emissions_intra = calculate_CO2_emissions(fuel_amounts_intra, co2_factors)
    eu_ets_penalty_intra = calculate_EU_ETS_Penalty(total_CO2_emissions_intra, CO2_price_per_ton)

    # Calculate fuel costs and EU ETS penalties for Inter trip
    fuel_costs_inter = calculate_fuel_costs(fuel_data, fuel_amounts_inter, year)
    total_CO2_emissions_inter = calculate_CO2_emissions(fuel_amounts_inter, co2_factors)/2.0
    eu_ets_penalty_inter = calculate_EU_ETS_Penalty(total_CO2_emissions_inter, CO2_price_per_ton)

    # Calculate fuel costs and EU ETS penalties for Berth trip
    fuel_costs_berth = calculate_fuel_costs(fuel_data, fuel_amounts_berth, year)
    total_CO2_emissions_berth = calculate_CO2_emissions(fuel_amounts_berth, co2_factors)
    eu_ets_penalty_berth = calculate_EU_ETS_Penalty(total_CO2_emissions_berth, CO2_price_per_ton)

    # Sum up the costs and penalties
    total_fuel_costs = {
        'min': fuel_costs_intra['min'] + fuel_costs_inter['min'] + fuel_costs_berth['min'],
        'max': fuel_costs_intra['max'] + fuel_costs_inter['max'] + fuel_costs_berth['max'],
        'average': fuel_costs_intra['average'] + fuel_costs_inter['average'] + fuel_costs_berth['average']
    }
    
    total_CO2_emissions = total_CO2_emissions_intra + total_CO2_emissions_inter + total_CO2_emissions_berth
    total_eu_ets_penalty = eu_ets_penalty_intra + eu_ets_penalty_inter + eu_ets_penalty_berth
    
    # If the year is 2025, apply a 30% reduction to the total EU ETS Penalty
    if year == 2025:
        total_eu_ets_penalty *= 0.7

    return total_fuel_costs, total_eu_ets_penalty, total_CO2_emissions

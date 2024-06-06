import argparse
from scipy.optimize import minimize
from fuel_calculations import calculate_costs_and_penalty, load_wtw_factors, load_fuel_data, load_fuel_density

# Pre-load all necessary data
fuel_density = load_fuel_density()
wtw_factors = load_wtw_factors()
fuel_data = load_fuel_data()

def calculate_fuel_amounts(percentages, E_total, densities, fixed_fuel, fixed_amount):
    fuel_amounts = {}
    remaining_E_total = E_total - fixed_amount * densities[fixed_fuel]
    for fuel, percentage in percentages.items():
        if fuel != fixed_fuel:
            fuel_amounts[fuel] = (percentage / 100) * remaining_E_total / densities[fuel]
    fuel_amounts[fixed_fuel] = fixed_amount
    return fuel_amounts

def objective_function(x, E_total, fuel_types, densities, fixed_fuel, fixed_amount, trip_type, year, CO2_price_per_ton):
    percentages = {fuel_types[i]: x[i] for i in range(len(fuel_types))}
    percentages[fixed_fuel] = 100 - sum(x)  # Ensure total is 100%
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, densities, fixed_fuel, fixed_amount)
    if trip_type == "inter-eu":
        E_total = E_total / 2
    journey_fuel_costs, _, FuelEU, CO2_penalty  = calculate_costs_and_penalty(fuel_amounts, E_total, year, CO2_price_per_ton)

    #Fuel costs and Fuel eu pen and Eu ts pen
    return journey_fuel_costs['average'] + FuelEU + CO2_penalty

def find_optimal_fuel_mix(E_total, selected_fuels, MDO_tonnes, trip_type, year, CO2_price_per_ton):
    fixed_fuel = 'MDO'
    fixed_amount = MDO_tonnes
    if fixed_fuel in selected_fuels:
        selected_fuels.remove(fixed_fuel)
    
    initial_guess = [100 / len(selected_fuels)] * len(selected_fuels)
    bounds = [(0, 100) for _ in selected_fuels]
    constraints = {'type': 'eq', 'fun': lambda x: sum(x) - 100}
    best_result = minimize(
        objective_function, initial_guess,
        args=(E_total, selected_fuels, fuel_density, fixed_fuel, fixed_amount, trip_type, year, CO2_price_per_ton),
        bounds=bounds, constraints=constraints
    )

    percentages = {selected_fuels[i]: best_result.x[i] for i in range(len(selected_fuels))}
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, fuel_density, fixed_fuel, fixed_amount)
    energy_contents = calculate_energy_content(fuel_amounts, fuel_density)
    total_energy = sum(energy_contents.values())
    actual_percentages = {fuel: (energy_contents[fuel] / total_energy) * 100 for fuel in energy_contents}

    if trip_type == "inter-eu":
        E_total = E_total / 2
    _, _, FuelEU, CO2_penalty = calculate_costs_and_penalty(fuel_amounts, E_total, year, CO2_price_per_ton)

    print(f"For {trip_type}:")
    print(f"Optimal fuel types {trip_type}:", selected_fuels + [fixed_fuel])
    print(f"Optimal percentages {trip_type}:", actual_percentages)
    print(f"Optimal fuel amounts (tonnes) {trip_type}:", fuel_amounts)
    print(f"EU TS Penalty {trip_type}: {CO2_penalty:.2f} €")
    print(f"FuelEU Penalty {trip_type}: {FuelEU:.2f} €")
    print(f"Optimal total cost {trip_type}: {best_result.fun:.3f} €")

def berth_scenario(E_total, MDO_tonnes, year, CO2_price_per_ton):
    fuel_amounts = {'MDO': MDO_tonnes}
    journey_fuel_costs, _, FuelEU, CO2_penalty = calculate_costs_and_penalty(fuel_amounts, E_total, year, CO2_price_per_ton)
    print("For Berth:")
    print(f"Fuel amount (tonnes) berth: {MDO_tonnes:.2f}")
    print(f"EU TS Penalty berth: {CO2_penalty:.2f} €")
    print(f"FuelEU Penalty berth: {FuelEU:.2f} €")
    print(f"Total cost berth: {journey_fuel_costs['average']:.2f} €")

def get_user_input():
    year = int(input("Enter the target year for GHGi compliance (e.g., 2025, 2030): "))

    CO2_price_per_ton = float(input("Enter the CO2 price per ton (€): "))

    E_totals = {}
    MDO_tonnes = {}
    selected_fuels = {}
    trip_types = ['intra-eu', 'inter-eu', 'berth']

    for trip_type in trip_types:
        E_totals[trip_type] = float(input(f"Enter the total energy (MJ) required for {trip_type.replace('-', ' ').title()}: "))
        MDO_tonnes[trip_type] = float(input(f"Enter the MDO used (in tonnes) for {trip_type.replace('-', ' ').title()}: "))
        
        if trip_type != 'berth':
            available_fuels = list(fuel_density.keys())
            print("Available fuels:", ", ".join(available_fuels))
            num_fuels = int(input(f"Enter the number of fuel types to consider for {trip_type.replace('-', ' ').title()}: "))
            selected_fuels[trip_type] = []
            for _ in range(num_fuels):
                fuel = input(f"Enter a fuel type for {trip_type.replace('-', ' ').title()}: ").upper()
                if fuel in available_fuels:
                    selected_fuels[trip_type].append(fuel)
                else:
                    print("Invalid fuel type! Available types are:", ", ".join(available_fuels))
                    break  # Break on invalid fuel type to prevent further errors

    return year, CO2_price_per_ton, E_totals, MDO_tonnes, selected_fuels

def calculate_energy_content(fuel_amounts, densities):
    """ Calculate the total energy content based on the amount and density of fuels. """
    return {fuel: amounts * densities[fuel] for fuel, amounts in fuel_amounts.items()}


if __name__ == "__main__":
    year, CO2_price_per_ton, E_totals, MDO_tonnes, selected_fuels = get_user_input()
    for trip_type in ['intra-eu', 'inter-eu']:
        if selected_fuels.get(trip_type):
            find_optimal_fuel_mix(E_totals[trip_type], selected_fuels[trip_type], MDO_tonnes[trip_type], trip_type, year, CO2_price_per_ton)
    if MDO_tonnes['berth'] > 0:
        berth_scenario(E_totals['berth'], MDO_tonnes['berth'], year, CO2_price_per_ton)

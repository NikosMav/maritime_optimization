import json
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

def objective_function(x, E_total, fuel_types, densities, fixed_fuel, fixed_amount, trip_type, year):
    percentages = {fuel_types[i]: x[i] for i in range(len(fuel_types))}
    percentages[fixed_fuel] = 100 - sum(x)  # Ensure total is 100%
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, densities, fixed_fuel, fixed_amount)
    if trip_type == "inter-eu":
        E_total = E_total / 2
    journey_fuel_costs, _, FuelEU = calculate_costs_and_penalty(fuel_amounts, E_total, year)
    return journey_fuel_costs['average'] + FuelEU

def find_optimal_fuel_mix(E_total, selected_fuels, MDO_tonnes, trip_type, year):
    fixed_fuel = 'MDO'
    fixed_amount = MDO_tonnes
    if fixed_fuel in selected_fuels:
        selected_fuels.remove(fixed_fuel)
    
    initial_guess = [100 / len(selected_fuels)] * len(selected_fuels)
    bounds = [(0, 100) for _ in selected_fuels]
    constraints = {'type': 'eq', 'fun': lambda x: sum(x) - 100}
    best_result = minimize(
        objective_function, initial_guess,
        args=(E_total, selected_fuels, fuel_density, fixed_fuel, fixed_amount, trip_type, year),
        bounds=bounds, constraints=constraints
    )

    percentages = {selected_fuels[i]: best_result.x[i] for i in range(len(selected_fuels))}
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, fuel_density, fixed_fuel, fixed_amount)
    energy_contents = calculate_energy_content(fuel_amounts, fuel_density)
    total_energy = sum(energy_contents.values())
    
    actual_percentages = {fuel: (energy_contents[fuel] / total_energy) * 100 for fuel in energy_contents}

    print("Optimal fuel types:", selected_fuels + [fixed_fuel])
    print("Optimal percentages:", actual_percentages)
    print("Optimal fuel amounts in tonnes:", fuel_amounts)
    print("Optimal total cost including FuelEU penalty: {:.3f} €".format(best_result.fun))

def berth_scenario(E_total, MDO_tonnes, year):
    fuel_amounts = {'MDO': MDO_tonnes}
    journey_fuel_costs, _, FuelEU = calculate_costs_and_penalty(fuel_amounts, E_total, year)
    print("Berth scenario using only MDO:")
    print(f"Fuel amount (tonnes): {MDO_tonnes:.2f}")
    print(f"Total cost: €{journey_fuel_costs['average']:.2f}")
    print(f"FuelEU penalty: €{FuelEU:.2f}")

def get_user_input():
    year = int(input("Enter the target year for GHGi compliance (e.g., 2025, 2030): "))
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

    return year, E_totals, MDO_tonnes, selected_fuels

def calculate_energy_content(fuel_amounts, densities):
    """ Calculate the total energy content based on the amount and density of fuels. """
    return {fuel: amounts * densities[fuel] for fuel, amounts in fuel_amounts.items()}


if __name__ == "__main__":
    year, E_totals, MDO_tonnes, selected_fuels = get_user_input()
    for trip_type in ['intra-eu', 'inter-eu']:
        if selected_fuels.get(trip_type):
            find_optimal_fuel_mix(E_totals[trip_type], selected_fuels[trip_type], MDO_tonnes[trip_type], trip_type, year)
    if MDO_tonnes['berth'] > 0:
        berth_scenario(E_totals['berth'], MDO_tonnes['berth'], year)

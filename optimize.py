import json
from scipy.optimize import minimize
from fuel_calculations import calculate_costs_and_penalty, load_wtw_factors, load_fuel_data, load_fuel_density

# Pre-load all necessary data
fuel_density = load_fuel_density()
wtw_factors = load_wtw_factors()
fuel_data = load_fuel_data()

# Function to handle the "Berth" scenario
def berth_scenario(E_total):
    # Assume MDO is the only fuel type used at berth
    fuel_amounts = {'MDO': E_total / fuel_density['MDO']}
    return calculate_costs_and_penalty(fuel_amounts, E_total)

# Objective function for the optimization
def objective_function(x, E_total, trip_type, fuel_types, densities, fixed_fuel, fixed_amount):
    percentages = {fuel_types[i]: x[i] for i in range(len(fuel_types))}
    percentages[fixed_fuel] = 100 - sum(x)  # Adjust to ensure total percentages sum to 100
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, densities, fixed_fuel, fixed_amount)
    # Adjust E_total for penalty calculation based on trip type
    penalty_E_total = E_total / 2 if trip_type == 'inter-eu' else E_total
    journey_fuel_costs, _, FuelEU = calculate_costs_and_penalty(fuel_amounts, penalty_E_total)
    # Objective is to minimize the average cost plus FuelEU penalty
    return journey_fuel_costs['average'] + FuelEU

# Function to find the best fuel combination or handle berth
def find_optimal_fuel_mix(E_total, selected_fuels, trip_type):
    if trip_type == 'berth':
        fixed_amount = float(input("Enter the amount of MDO used (in tonnes): "))
        fuel_amounts = {'MDO': fixed_amount}
        journey_fuel_costs, CB, FuelEU = calculate_costs_and_penalty(fuel_amounts, E_total)
        print("Berth scenario using only MDO:")
        print(f"Fuel amount (tonnes): {fixed_amount:.2f}")
        print(f"Total cost: €{journey_fuel_costs['average']:.2f}")
        print(f"FuelEU penalty: €{FuelEU:.2f}")
        return

    fixed_fuel = 'MDO'
    fixed_amount = float(input("Enter the fixed amount of MDO used (in tonnes): "))
    selected_fuels.remove(fixed_fuel)  # Ensuring MDO is not in the optimization fuels
    initial_guess = [100 / len(selected_fuels)] * len(selected_fuels)
    bounds = [(0, 100) for _ in selected_fuels]
    constraints = {'type': 'eq', 'fun': lambda x: sum(x) - 100}

    best_result = minimize(
        objective_function, initial_guess,
        args=(E_total, trip_type, selected_fuels, fuel_density, fixed_fuel, fixed_amount),
        bounds=bounds, constraints=constraints
    )

    # Recalculate to confirm percentages and amounts after optimization
    percentages = {selected_fuels[i]: best_result.x[i] for i in range(len(selected_fuels))}
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, fuel_density, fixed_fuel, fixed_amount)
    percentages = calculate_percentages(fuel_amounts, fuel_density)

    print(f"Optimal fuel types: {selected_fuels + [fixed_fuel]}")
    print(f"Optimal percentages: {{ {', '.join([f'{fuel}: {percentage:.3f}%' for fuel, percentage in percentages.items()])} }}")
    print(f"Optimal fuel amounts in tonnes: {{ {', '.join([f'{fuel}: {amount:.3f} t' for fuel, amount in fuel_amounts.items()])} }}")
    print(f"Optimal total cost including FuelEU penalty: {best_result.fun:.3f} €")

# Calculate percentages based on fuel amounts
def calculate_percentages(fuel_amounts, densities):
    fuel_energies = {fuel: amount * densities[fuel] for fuel, amount in fuel_amounts.items()}
    total_energy = sum(fuel_energies.values())
    return {fuel: (energy / total_energy) * 100 for fuel, energy in fuel_energies.items()}

# Calculate fuel amounts based on percentages
def calculate_fuel_amounts(percentages, E_total, densities, fixed_fuel, fixed_amount):
    fuel_amounts = {}
    remaining_E_total = E_total - fixed_amount * densities[fixed_fuel]
    for fuel, percentage in percentages.items():
        if fuel != fixed_fuel:
            fuel_amounts[fuel] = (percentage / 100) * remaining_E_total / densities[fuel]
    fuel_amounts[fixed_fuel] = fixed_amount
    return fuel_amounts

# Get user input for fuel types, E_total, and trip type
def get_user_input():
    E_total = float(input("Enter the total energy (MJ) required: "))
    trip_type = input("Enter the trip type (Intra-EU / Inter-EU / Berth): ").strip().lower()
    available_fuels = list(fuel_density.keys())
    print("Available fuels:", ", ".join(available_fuels))
    num_fuels = int(input("Enter the number of fuel types to consider: "))  # Correctly placed int conversion
    selected_fuels = []
    for _ in range(num_fuels):  # Iterate over a range, not an int directly
        while True:
            fuel = input("Enter a fuel type: ").upper()
            if fuel in available_fuels:
                selected_fuels.append(fuel)
                break
            print("Invalid fuel type! Available types are:", ", ".join(available_fuels))
    return E_total, selected_fuels, trip_type


if __name__ == "__main__":
    E_total, selected_fuels, trip_type = get_user_input()
    find_optimal_fuel_mix(E_total, selected_fuels, trip_type)


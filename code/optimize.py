from scipy.optimize import minimize
from fuel_calculations import calculate_costs_and_penalties, load_fuel_density

# Pre-load all necessary data
fuel_density = load_fuel_density()

def calculate_fuel_amounts(percentages, E_total, densities, fixed_fuel, fixed_amount):
    fuel_amounts = {}
    remaining_E_total = E_total - fixed_amount * densities[fixed_fuel]
    for fuel, percentage in percentages.items():
        if fuel != fixed_fuel:
            fuel_amounts[fuel] = (percentage / 100) * remaining_E_total / densities[fuel]
    fuel_amounts[fixed_fuel] = fixed_amount
    return fuel_amounts

def objective_function(x, E_total, fuel_types, densities, fixed_fuel, fixed_amount, trip_type, year, CO2_price_per_ton, fwind):
    percentages = {fuel_types[i]: x[i] for i in range(len(fuel_types))}
    percentages[fixed_fuel] = 100 - sum(x)  # Ensure total is 100%
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, densities, fixed_fuel, fixed_amount)

    # Halve E_total for inter-eu
    if trip_type == "inter-eu":
        E_total *= 0.5

    journey_fuel_costs, _, Fuel_EU_Penalty, EU_TS_Penalty = calculate_costs_and_penalties(fuel_amounts, E_total, year, CO2_price_per_ton, fwind)

    # Halve EU_TS_Penalty for inter-eu
    if trip_type == "inter-eu":
        EU_TS_Penalty *= 0.5

    # Sum Fuel costs, Fuel_EU_Penalty, and EU_TS_Penalty
    return journey_fuel_costs['average'] + Fuel_EU_Penalty + EU_TS_Penalty

def find_optimal_fuel_mix(E_total, selected_fuels, MDO_tonnes, trip_type, year, CO2_price_per_ton, fwind):
    fixed_fuel = 'MDO'      # it is fixed since every trip type has MDO
    fixed_amount = MDO_tonnes
    # Checking if MDO is in selected_fuels and remove it
    if fixed_fuel in selected_fuels:
        selected_fuels.remove(fixed_fuel)
    
    initial_guess = [100 / len(selected_fuels)] * len(selected_fuels)
    bounds = [(0, 100) for _ in selected_fuels]
    constraints = {'type': 'eq', 'fun': lambda x: sum(x) - 100}
    best_result = minimize(
        objective_function, initial_guess,
        args=(E_total, selected_fuels, fuel_density, fixed_fuel, fixed_amount, trip_type, year, CO2_price_per_ton, fwind),
        bounds=bounds, constraints=constraints
    )

    percentages = {selected_fuels[i]: best_result.x[i] for i in range(len(selected_fuels))}
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, fuel_density, fixed_fuel, fixed_amount)
    energy_contents = calculate_energy_content(fuel_amounts, fuel_density)
    total_energy = sum(energy_contents.values())
    actual_percentages = {fuel: (energy_contents[fuel] / total_energy) * 100 for fuel in energy_contents}

    # Halve the Etotal for inter 
    if trip_type == "inter-eu":
        E_total *= 0.5

    # Get the final penalties
    _, _, Fuel_EU_Penalty, EU_TS_Penalty = calculate_costs_and_penalties(fuel_amounts, E_total, year, CO2_price_per_ton, fwind)

    # Halve the EU_TS_Penalty for inter
    if trip_type == "inter-eu":
        EU_TS_Penalty *= 0.5

    print(f"For {trip_type}:")
    print(f"Optimal fuel types {trip_type}:", selected_fuels + [fixed_fuel])
    print(f"Optimal percentages {trip_type}:", actual_percentages)
    print(f"Optimal fuel amounts (tonnes) {trip_type}:", fuel_amounts)
    print(f"EU TS Penalty {trip_type}: {EU_TS_Penalty:.2f} €")
    print(f"FuelEU Penalty {trip_type}: {Fuel_EU_Penalty:.2f} €")
    print(f"Optimal total cost {trip_type}: {best_result.fun:.3f} €")

def berth_scenario(E_total, year, CO2_price_per_ton, OPS_at_berth, total_installed_power, established_power_demand, hours_at_berth, cost_per_MWh, fwind):
    MJ_to_MWh = 0.0002777778  # Conversion factor from MJ to MWh
    fuel_amounts = {'MDO': 0}# Initialize to zero initially

    if OPS_at_berth:
        # When OPS is used, assume no MDO is used and no emissions are produced at berth
        print("OPS is used at berth. No MDO usage and no direct emissions.")
        journey_fuel_costs = {'min': 0, 'max': 0, 'average': 0}
        Fuel_EU_Penalty = 0
        EU_TS_Penalty = 0

        # Calculate OPS penalty
        OPS_penalty = 1.5 * established_power_demand * hours_at_berth
        # Calculate OPS cost using the energy demand
        E_OPS = E_total
        OPS_cost = E_OPS * MJ_to_MWh * cost_per_MWh
    else:
        # Standard calculation if OPS is not used
        MDO_density = fuel_density['MDO']
        MDO_tonnes = E_total / MDO_density  # Calculate MDO_tonnes from E_total and MDO_density
        fuel_amounts['MDO'] = MDO_tonnes
        journey_fuel_costs, _, Fuel_EU_Penalty, EU_TS_Penalty = calculate_costs_and_penalties(fuel_amounts, E_total, year, CO2_price_per_ton, fwind)
        OPS_penalty = 0
        OPS_cost = 0

    # Output the results for berth
    print("For Berth:")
    print(f"Fuel amounts (tonnes) berth: ", fuel_amounts)
    print(f"EU TS Penalty berth: {EU_TS_Penalty:.2f} €")
    print(f"FuelEU Penalty berth: {Fuel_EU_Penalty:.2f} €")
    if OPS_at_berth:
        print(f"OPS Penalty berth: {OPS_penalty:.2f} €")
        print(f"OPS Cost berth: {OPS_cost:.2f} €")
        # Calculate the total cost for berth including the OPS penalty
        total_berth_cost = journey_fuel_costs['average'] + EU_TS_Penalty + Fuel_EU_Penalty + OPS_penalty + OPS_cost
    else:
        # Calculate the total cost for berth without the OPS penalty
        total_berth_cost = journey_fuel_costs['average'] + EU_TS_Penalty + Fuel_EU_Penalty

    print(f"Total cost berth: {total_berth_cost:.2f} €")

def get_user_input():
    year = int(input("Enter the target year for GHGi compliance (e.g., 2025, 2030): "))
    CO2_price_per_ton = float(input("Enter the CO2 price per ton (€): "))
    cost_per_MWh = float(input("Enter the cost per MWh (€): "))
    # use_wind = input("Is wind-assisted propulsion used? (yes/no): ").strip().lower() == 'yes'
    fwind = 1.0
    # if use_wind:
    #     Pwind_Pprop = float(input("Enter the ratio of Pwind/Pprop (fwind): "))
    #     fwind = max(0.95, min(0.99, Pwind_Pprop))

    E_totals = {}
    MDO_tonnes = {}
    selected_fuels = {}
    OPS_flags = {}
    OPS_details = {}
    trip_types = ['intra-eu', 'inter-eu', 'berth']

    for trip_type in trip_types:
        E_totals[trip_type] = float(input(f"Enter the total energy (MJ) required for {trip_type.replace('-', ' ').title()}: "))
        if trip_type != 'berth':
            MDO_tonnes[trip_type] = float(input(f"Enter the MDO used (in tonnes) for {trip_type.replace('-', ' ').title()}: "))
            available_fuels = list(fuel_density.keys())
            print("Available fuels:", ", ".join(available_fuels))
            num_fuels = int(input(f"Enter the number of different fuel types to use for {trip_type.replace('-', ' ').title()} (please enter a number): "))
            selected_fuels[trip_type] = []
            for _ in range(num_fuels):
                fuel = input(f"Enter a fuel type for {trip_type.replace('-', ' ').title()}: ").upper()
                if fuel in available_fuels:
                    selected_fuels[trip_type].append(fuel)
                else:
                    print("Invalid fuel type! Available types are:", ", ".join(available_fuels))
                    break
        else:
            OPS_use = input("Is OPS used at berth? (yes/no): ").strip().lower() == 'yes'
            OPS_flags[trip_type] = OPS_use
            if OPS_use:
                total_installed_power = float(input("Enter the total installed power (MW) for the ship: "))
                established_power_demand = float(input("Enter the established power demand at berth (MW): "))
                hours_at_berth = int(input("Enter the number of hours at berth: "))
                OPS_details[trip_type] = {
                    'total_installed_power': total_installed_power,
                    'established_power_demand': established_power_demand,
                    'hours_at_berth': hours_at_berth
                }

    return year, CO2_price_per_ton, cost_per_MWh, E_totals, MDO_tonnes, selected_fuels, OPS_flags, OPS_details, fwind

def calculate_energy_content(fuel_amounts, densities):
    # Calculate the total energy content based on the amount and density of fuels.
    return {fuel: amounts * densities[fuel] for fuel, amounts in fuel_amounts.items()}


if __name__ == "__main__":
    year, CO2_price_per_ton, cost_per_MWh, E_totals, MDO_tonnes, selected_fuels, OPS_flags, OPS_details, fwind = get_user_input()

    for trip_type in ['intra-eu', 'inter-eu']:
        if selected_fuels.get(trip_type):
            find_optimal_fuel_mix(E_totals[trip_type], selected_fuels[trip_type], MDO_tonnes[trip_type], trip_type, year, CO2_price_per_ton, fwind)

    if E_totals['berth'] > 0:
        OPS_at_berth = OPS_flags.get('berth', False)
        if OPS_at_berth:
            ops_info = OPS_details.get('berth', {})
            berth_scenario(E_totals['berth'], year, CO2_price_per_ton, OPS_at_berth, ops_info['total_installed_power'], ops_info['established_power_demand'], ops_info['hours_at_berth'], cost_per_MWh, fwind)
        else:
            berth_scenario(E_totals['berth'], year, CO2_price_per_ton, OPS_at_berth, 0, 0, 0, cost_per_MWh, fwind)


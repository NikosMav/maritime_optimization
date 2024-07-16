from scipy.optimize import differential_evolution
from scipy.optimize import NonlinearConstraint
from fuel_calculations import (
                            calculate_total_Fuel_EU_Penalty, calculate_total_fuel_costs_and_EU_ETS_penalties,
                            load_fuel_density
                        )

# Pre-load all necessary data
fuel_density = load_fuel_density()

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
            else:
                OPS_details[trip_type] = {
                    'total_installed_power': 0,
                    'established_power_demand': 0,
                    'hours_at_berth': 0
                }

    return year, CO2_price_per_ton, cost_per_MWh, E_totals, MDO_tonnes, selected_fuels, OPS_flags, OPS_details, fwind

def calculate_fuel_amounts(percentages, E_total, densities, fixed_fuel, fixed_amount):
    energy_from_MDO = fixed_amount * densities[fixed_fuel]  # Assuming density is in MJ/tonne
    remaining_E_total = E_total - energy_from_MDO

    fuel_amounts = {fixed_fuel: fixed_amount}
    for fuel, percentage in percentages.items():
        if fuel != fixed_fuel:
            energy_content_per_tonne = densities[fuel]  # Assuming densities are correctly set in MJ/tonne
            required_energy = (percentage / 100) * remaining_E_total
            fuel_amounts[fuel] = required_energy / energy_content_per_tonne

    return fuel_amounts

def objective_function(x, E_totals, fuel_types, densities, fixed_fuel, MDO_tonnes, OPS_flags, OPS_details, year, CO2_price_per_ton, fwind, cost_per_MWh):
    percentages = {fuel_types[i]: x[i] for i in range(len(fuel_types))}
    percentages[fixed_fuel] = 100 - sum(x)  # Ensure total is 100%

    # Separate fuel amounts for each trip type
    fuel_amounts_intra = calculate_fuel_amounts(percentages, E_totals['intra-eu'], densities, fixed_fuel, MDO_tonnes['intra-eu'])
    fuel_amounts_inter = calculate_fuel_amounts(percentages, E_totals['inter-eu'], densities, fixed_fuel, MDO_tonnes['inter-eu'])
    
    if OPS_flags['berth']:
        fuel_amounts_berth, OPS_penalty, OPS_cost = berth_scenario(E_totals['berth'], OPS_flags['berth'], 
                                            OPS_details['berth']['total_installed_power'],
                                            OPS_details['berth']['established_power_demand'],
                                            OPS_details['berth']['hours_at_berth'], cost_per_MWh)
    else:
        fuel_amounts_berth, OPS_penalty, OPS_cost = berth_scenario(E_totals['berth'], OPS_flags['berth'], 0, 0, 0, cost_per_MWh)

    # Calculate total fuel costs and EU ETS penalties
    total_fuel_costs, total_EU_ETS_penalty, c02 = calculate_total_fuel_costs_and_EU_ETS_penalties(
        year, CO2_price_per_ton, fuel_amounts_intra, fuel_amounts_inter, fuel_amounts_berth
    )

    # Calculate total Fuel EU penalty
    fuel_percentages_intra = {fuel: amount / sum(fuel_amounts_intra.values()) * 100 for fuel, amount in fuel_amounts_intra.items()}
    fuel_percentages_inter = {fuel: amount / sum(fuel_amounts_inter.values()) * 100 for fuel, amount in fuel_amounts_inter.items()}
    
    if OPS_flags['berth']:
        fuel_percentages_berth = {'MDO': 0}  # No MDO usage if OPS is used
    else:
        fuel_percentages_berth = {fuel: amount / sum(fuel_amounts_berth.values()) * 100 for fuel, amount in fuel_amounts_berth.items()}

    total_CB, total_Fuel_EU_penalty = calculate_total_Fuel_EU_Penalty(
        year, E_totals['intra-eu'], E_totals['inter-eu'], E_totals['berth'], fwind,
        fuel_percentages_intra, fuel_percentages_inter, fuel_percentages_berth
    )

    # Calculate total cost
    total_cost = total_fuel_costs['average'] + total_Fuel_EU_penalty + total_EU_ETS_penalty + OPS_cost + OPS_penalty

    return total_cost

def total_energy_constraint(x, E_total, fuel_types, densities, fixed_fuel, fixed_amount):
    percentages = {fuel_types[i]: x[i] for i in range(len(fuel_types))}
    percentages[fixed_fuel] = 100 - sum(x)  # Ensure total is 100%
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, densities, fixed_fuel, fixed_amount)
    total_energy_provided = sum(amount * densities[fuel] for fuel, amount in fuel_amounts.items())
    return total_energy_provided - E_total

def optimize_fuel_mix(E_totals, fuel_types, densities, fixed_fuel, MDO_tonnes, OPS_flags, OPS_details, year, CO2_price_per_ton, fwind, cost_per_MWh):
    print(fuel_types)
    bounds = [(0, 100) for _ in fuel_types]

    # Define the constraint for total energy
    constraint_fun = lambda x: total_energy_constraint(x, sum(E_totals.values()), fuel_types, densities, fixed_fuel, sum(MDO_tonnes.values()))
    energy_constraint = NonlinearConstraint(constraint_fun, lb=0, ub=0)

    result = differential_evolution(
        objective_function,
        bounds,
        args=(E_totals, fuel_types, densities, fixed_fuel, MDO_tonnes, OPS_flags, OPS_details, year, CO2_price_per_ton, fwind, cost_per_MWh),
        constraints=(energy_constraint,),
        strategy='best1bin',  # Try different strategy
        maxiter=10000,  # Increased iterations
        popsize=10,  # Larger population size
        tol=0.0001,
        mutation=(0.5, 1.5),  # Adjust mutation
        recombination=0.9,  # Higher recombination
        seed=None,
        callback=None,
        disp=True,
        polish=True,
        init='latinhypercube',  # Different initialization strategy
        workers=8,
        atol=0
    )

    # Extract the optimal percentages
    optimal_percentages = result.x

    percentages = {fuel_types[i]: optimal_percentages[i] for i in range(len(fuel_types))}
    percentages[fixed_fuel] = 100 - sum(optimal_percentages)  # Ensure total is 100%

    # Separate fuel amounts for each trip type
    fuel_amounts_intra = calculate_fuel_amounts(percentages, E_totals['intra-eu'], densities, fixed_fuel, MDO_tonnes['intra-eu'])
    fuel_amounts_inter = calculate_fuel_amounts(percentages, E_totals['inter-eu'], densities, fixed_fuel, MDO_tonnes['inter-eu'])
    
    if OPS_flags['berth']:
        fuel_amounts_berth, OPS_penalty, OPS_cost = berth_scenario(E_totals['berth'], OPS_flags['berth'], 
                                            OPS_details['berth']['total_installed_power'],
                                            OPS_details['berth']['established_power_demand'],
                                            OPS_details['berth']['hours_at_berth'], cost_per_MWh)
    else:
        fuel_amounts_berth, OPS_penalty, OPS_cost = berth_scenario(E_totals['berth'], OPS_flags['berth'], 0, 0, 0, cost_per_MWh)

    total_fuel_amounts = {}
    for fuel_amounts in [fuel_amounts_intra, fuel_amounts_inter, fuel_amounts_berth]:
        for fuel, amount in fuel_amounts.items():
            if fuel in total_fuel_amounts:
                total_fuel_amounts[fuel] += amount
            else:
                total_fuel_amounts[fuel] = amount

    # Calculate total fuel costs and EU ETS penalties
    total_fuel_costs, total_EU_ETS_penalty, c02 = calculate_total_fuel_costs_and_EU_ETS_penalties(
        year, CO2_price_per_ton, fuel_amounts_intra, fuel_amounts_inter, fuel_amounts_berth
    )

    # Calculate total Fuel EU penalty
    fuel_percentages_intra = {fuel: amount / sum(fuel_amounts_intra.values()) * 100 for fuel, amount in fuel_amounts_intra.items()}
    fuel_percentages_inter = {fuel: amount / sum(fuel_amounts_inter.values()) * 100 for fuel, amount in fuel_amounts_inter.items()}
    
    if OPS_flags['berth']:
        fuel_percentages_berth = {'MDO': 0}  # No MDO usage if OPS is used
    else:
        fuel_percentages_berth = {fuel: amount / sum(fuel_amounts_berth.values()) * 100 for fuel, amount in fuel_amounts_berth.items()}

    total_CB, total_Fuel_EU_penalty = calculate_total_Fuel_EU_Penalty(
        year, E_totals['intra-eu'], E_totals['inter-eu'], E_totals['berth'], fwind,
        fuel_percentages_intra, fuel_percentages_inter, fuel_percentages_berth
    )

    # Calculate total cost
    total_cost = total_fuel_costs['average'] + total_Fuel_EU_penalty + total_EU_ETS_penalty + OPS_cost + OPS_penalty

    print(f"Optimal fuel amounts (tonnes): {total_fuel_amounts}")
    print(f"Total CB: {total_CB}")
    print(f"Final FuelEU penalty: {total_Fuel_EU_penalty}")
    print(f"Final EU ETS penalty: {total_EU_ETS_penalty}")
    print(f"OPS cost: {OPS_cost}")
    print(f"OPS penalty: {OPS_penalty}")
    print(f"Optimal total cost: {total_cost}")

    return result

def berth_scenario(E_total, OPS_use, total_installed_power, established_power_demand, hours_at_berth, cost_per_MWh):
    MJ_to_MWh = 0.0002777778  # Conversion factor from MJ to MWh
    fuel_amounts = {'MDO': 0} # Initialize to zero initially

    if OPS_use:
        # When OPS is used, assume no MDO is used and no emissions are produced at berth
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
        OPS_penalty = 0
        OPS_cost = 0

    return fuel_amounts, OPS_penalty, OPS_cost

if __name__ == "__main__":
    year, CO2_price_per_ton, cost_per_MWh, E_totals, MDO_tonnes, selected_fuels, OPS_flags, OPS_details, fwind = get_user_input()

    fuel_types = list(set([fuel for trip_fuels in selected_fuels.values() for fuel in trip_fuels]))

    result = optimize_fuel_mix(E_totals, fuel_types, fuel_density, "MDO", MDO_tonnes, OPS_flags, OPS_details, year, CO2_price_per_ton, fwind, cost_per_MWh)

    #print(f"Optimized result: {result}")


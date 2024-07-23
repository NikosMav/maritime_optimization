from scipy.optimize import differential_evolution, NonlinearConstraint, minimize
from fuel_calculations import (
                            calculate_total_Fuel_EU_Penalty, calculate_total_fuel_costs_and_EU_ETS_penalties,
                            load_fuel_density, load_fuel_data
                        )
import pandas as pd

fuel_densities = load_fuel_density()
def get_user_input_FAST():
    fwind = 1.0
    fuel_amounts = {}
    selected_fuels = {}
    E_totals = {}
    OPS_details = {}
    OPS_flags = {}
    fuel_types = ['HFO', 'VLSFO', 'MDO', 'BIO-DIESEL', 'LNG', 'E-METHANOL']

    trip_types = ['intra-eu', 'inter-eu', 'berth']
    with open("C:\\Users\\Lenovo\\Desktop\\skatouts9\\maritime_optimization\\code\\fast.nigga", 'r') as file:
            year = int(file.readline().strip())
            CO2_price_per_ton = float(file.readline().strip())
            cost_per_MWh = float(file.readline().strip())
            fuel_prices = file.readline().strip().lower() == 'yes'
            for trip_type in trip_types:
                OPS_flags[trip_type] = False
                if(trip_type == 'berth'):
                    ops = file.readline().strip().lower()
                    OPS_details[trip_type] = {
                    'total_installed_power': 0,
                    'established_power_demand': 0,
                    'hours_at_berth': 0
                    }
                    berth_fuel_amounts = {fuel: float(file.readline().strip()) for fuel in fuel_densities}
                    fuel_amounts[trip_type] = berth_fuel_amounts
                    E_totals[trip_type] = sum(berth_fuel_amounts[fuel] * fuel_densities[fuel] for fuel in berth_fuel_amounts)
                else:
                    fuel_amounts[trip_type] = {}
                    available_fuels = list(fuel_densities.keys())
                    for fuel in available_fuels:
                        fuel_amounts[trip_type][fuel] = float(file.readline().strip())
                    E_totals[trip_type] = sum(fuel_amounts[trip_type][fuel] * fuel_densities[fuel] for fuel in fuel_amounts[trip_type])
                    selected_fuels[trip_type] = [fuel for fuel in available_fuels if fuel_amounts[trip_type][fuel] > 0]

            return year, CO2_price_per_ton, cost_per_MWh, E_totals, fuel_amounts, selected_fuels, OPS_flags, OPS_details, fwind, fuel_densities


def get_user_input():
    year = int(input("Enter the target year for GHGi compliance (e.g., 2025, 2030): "))
    CO2_price_per_ton = float(input("Enter the CO2 price per ton (€): "))
    cost_per_MWh = float(input("Enter the cost per MWh (€): "))
    fwind = 1.0

    # Use default fuel prices or user-specified
    use_default_prices = input("Do you want to use Fuel Maritime Optimization Fuel Price? (yes/no): ").strip().lower() == 'yes'
    
    #TODO
    if not use_default_prices:
        fuel_types = ['HFO', 'VLSFO', 'MDO', 'BIO-DIESEL', 'LNG', 'E-METHANOL']
        fuel_prices = {fuel: float(input(f"Fuel Price - {fuel}: ")) for fuel in fuel_types}
    else:
        fuel_prices = load_fuel_data()

    E_totals = {}
    fuel_amounts = {}
    selected_fuels = {}
    OPS_flags = {}
    OPS_details = {}
    trip_types = ['intra-eu', 'inter-eu', 'berth']

    for trip_type in trip_types:
        if trip_type == 'berth':
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
                fuel_amounts[trip_type] = {}
                E_totals[trip_type] = total_installed_power * established_power_demand * hours_at_berth
            else:
                OPS_details[trip_type] = {
                    'total_installed_power': 0,
                    'established_power_demand': 0,
                    'hours_at_berth': 0
                }
                berth_fuel_amounts = {fuel: float(input(f"Berth - {fuel}: ")) for fuel in fuel_densities}
                fuel_amounts[trip_type] = berth_fuel_amounts
                E_totals[trip_type] = sum(berth_fuel_amounts[fuel] * fuel_densities[fuel] for fuel in berth_fuel_amounts)
        else:
            fuel_amounts[trip_type] = {}
            available_fuels = list(fuel_densities.keys())
            print(f"Enter fuel amounts for {trip_type.replace('-', ' ').title()} in tonnes:")
            for fuel in available_fuels:
                amount = float(input(f"{fuel}: "))
                fuel_amounts[trip_type][fuel] = amount
            E_totals[trip_type] = sum(fuel_amounts[trip_type][fuel] * fuel_densities[fuel] for fuel in fuel_amounts[trip_type])
            selected_fuels[trip_type] = [fuel for fuel in available_fuels if fuel_amounts[trip_type][fuel] > 0]

    return year, CO2_price_per_ton, cost_per_MWh, E_totals, fuel_amounts, selected_fuels, OPS_flags, OPS_details, fwind, fuel_densities

def calculate_fuel_amounts(percentages, E_total, densities):
    fuel_amounts = {}
    for fuel, percentage in percentages.items():
        energy_content_per_tonne = densities[fuel]  # Assuming densities are correctly set in MJ/tonne
        required_energy = (percentage / 100) * E_total
        fuel_amounts[fuel] = required_energy / energy_content_per_tonne
    return fuel_amounts

def objective_function(x, E_totals, fuel_types, densities, OPS_flags, OPS_details, year, CO2_price_per_ton, fwind, cost_per_MWh):
    percentages = {fuel_types[i]: x[i] for i in range(len(fuel_types))}
    percentages_sum = sum(percentages.values())
    if percentages_sum > 100:  # Ensure the percentages sum to 100
        percentages = {fuel: (percentage / percentages_sum) * 100 for fuel, percentage in percentages.items()}
    else:
        percentages = {fuel: percentage for fuel, percentage in percentages.items()}

    # Separate fuel amounts for each trip type
    fuel_amounts_intra = calculate_fuel_amounts(percentages, E_totals['intra-eu'], densities)
    fuel_amounts_inter = calculate_fuel_amounts(percentages, E_totals['inter-eu'], densities)
    
    if OPS_flags['berth']:
        fuel_amounts_berth, OPS_penalty, OPS_cost = berth_scenario(percentages, E_totals['berth'], densities, OPS_flags['berth'], 
                                            OPS_details['berth']['total_installed_power'],
                                            OPS_details['berth']['established_power_demand'],
                                            OPS_details['berth']['hours_at_berth'], cost_per_MWh)
    else:
        fuel_amounts_berth, OPS_penalty, OPS_cost = berth_scenario(percentages, E_totals['berth'], densities, OPS_flags['berth'], 0, 0, 0, cost_per_MWh)

    # Calculate total fuel costs and EU ETS penalties
    total_fuel_costs, total_EU_ETS_penalty, _  = calculate_total_fuel_costs_and_EU_ETS_penalties(
        year, CO2_price_per_ton, fuel_amounts_intra, fuel_amounts_inter, fuel_amounts_berth
    )

    # Calculate total Fuel EU penalty
    fuel_percentages_intra = {fuel: amount / sum(fuel_amounts_intra.values()) * 100 for fuel, amount in fuel_amounts_intra.items()}
    fuel_percentages_inter = {fuel: amount / sum(fuel_amounts_inter.values()) * 100 for fuel, amount in fuel_amounts_inter.items()}
    
    if OPS_flags['berth']:
        fuel_percentages_berth = {fuel: 0 for fuel in fuel_types}
    else:
        fuel_percentages_berth = {fuel: amount / sum(fuel_amounts_berth.values()) * 100 for fuel, amount in fuel_amounts_berth.items()}

    _, total_Fuel_EU_penalty = calculate_total_Fuel_EU_Penalty(
        year, E_totals['intra-eu'], E_totals['inter-eu'], E_totals['berth'], fwind,
        fuel_percentages_intra, fuel_percentages_inter, fuel_percentages_berth
    )

    # Calculate total cost
    total_cost = total_fuel_costs['average'] + total_Fuel_EU_penalty + total_EU_ETS_penalty + OPS_cost + OPS_penalty

    return total_cost

def total_energy_constraint(x, E_total, fuel_types, densities):
    percentages = {fuel_types[i]: x[i] for i in range(len(fuel_types))}
    percentages_sum = sum(percentages.values())
    if percentages_sum > 100:  # Ensure the percentages sum to 100
        percentages = {fuel: (percentage / percentages_sum) * 100 for fuel, percentage in percentages.items()}
    else:
        percentages = {fuel: percentage for fuel, percentage in percentages.items()}
        
    fuel_amounts = calculate_fuel_amounts(percentages, E_total, densities)
    total_energy_provided = sum(amount * densities[fuel] for fuel, amount in fuel_amounts.items())
    return total_energy_provided - E_total

def optimize_fuel_mix(E_totals, fuel_types, densities, OPS_flags, OPS_details, year, CO2_price_per_ton, fwind, cost_per_MWh):
    bounds = [(0, 100) for _ in fuel_types]

    # # Define the constraint for total energy
    # constraint_fun = lambda x: total_energy_constraint(x, sum(E_totals.values()), fuel_types, densities)
    # energy_constraint = NonlinearConstraint(constraint_fun, lb=0, ub=0)

    # Define the constraints for total energy for each trip type
    constraints = []
    for trip_type in E_totals.keys():
        constraint_fun = lambda x, trip_type=trip_type: total_energy_constraint(x, E_totals[trip_type], fuel_types, densities)
        energy_constraint = NonlinearConstraint(constraint_fun, lb=0, ub=0)
        constraints.append(energy_constraint)
    if fuel_types == ['HFO', 'MDO', 'VLSFO']:
        # Define an initial guess for the percentages (e.g., equally distributed)
        initial_guess = [100 / len(fuel_types)] * len(fuel_types)

        # Print the initial percentages before minimization
        initial_percentages = {fuel_types[i]: initial_guess[i] for i in range(len(fuel_types))}
        print("Initial Percentages:", initial_percentages)
    else:    
        result = differential_evolution(
            objective_function,
            bounds,
            args=(E_totals, fuel_types, densities, OPS_flags, OPS_details, year, CO2_price_per_ton, fwind, cost_per_MWh),
            constraints=(energy_constraint,),
            strategy='best1bin',  # Try different strategy
            maxiter=3000,  # Increased iterations
            popsize=250,  # Larger population size
            tol=0.01,
            mutation=(0.1, 1.9),  # Adjust mutation
            recombination=0.9,  # Higher recombination
            seed=None,
            callback=None,
            # disp=True,
            polish=True,
            init='latinhypercube',  # Different initialization strategy
            atol=0,
            # workers=4
        )

        # Extract the optimal percentages
        optimal_percentages = result.x

    percentages = {fuel_types[i]: optimal_percentages[i] for i in range(len(fuel_types))}
    percentages_sum = sum(percentages.values())
    if percentages_sum > 100:  # Ensure the percentages sum to 100
        percentages = {fuel: (percentage / percentages_sum) * 100 for fuel, percentage in percentages.items()}
    else:
        percentages = {fuel: percentage for fuel, percentage in percentages.items()}

    # Separate fuel amounts for each trip type
    fuel_amounts_intra = calculate_fuel_amounts(percentages, E_totals['intra-eu'], densities)
    fuel_amounts_inter = calculate_fuel_amounts(percentages, E_totals['inter-eu'], densities)
    
    if OPS_flags['berth']:
        fuel_amounts_berth, OPS_penalty, OPS_cost = {}, 0, 0
    else:
        fuel_amounts_berth = calculate_fuel_amounts(percentages, E_totals['berth'], densities)
        OPS_penalty, OPS_cost = 0, 0

    total_fuel_amounts = {}
    for fuel_amounts in [fuel_amounts_intra, fuel_amounts_inter, fuel_amounts_berth]:
        for fuel, amount in fuel_amounts.items():
            if fuel in total_fuel_amounts:
                total_fuel_amounts[fuel] += amount
            else:
                total_fuel_amounts[fuel] = amount

    # Calculate total fuel costs and EU ETS penalties
    total_fuel_costs, total_EU_ETS_penalty, total_CO2_emissions = calculate_total_fuel_costs_and_EU_ETS_penalties(
        year, CO2_price_per_ton, fuel_amounts_intra, fuel_amounts_inter, fuel_amounts_berth
    )

    # Calculate total Fuel EU penalty
    fuel_percentages_intra = {fuel: amount / sum(fuel_amounts_intra.values()) * 100 for fuel, amount in fuel_amounts_intra.items()}
    fuel_percentages_inter = {fuel: amount / sum(fuel_amounts_inter.values()) * 100 for fuel, amount in fuel_amounts_inter.items()}
    
    if OPS_flags['berth']:
        fuel_percentages_berth = {fuel: 0 for fuel in fuel_types}
    else:
        fuel_percentages_berth = {fuel: amount / sum(fuel_amounts_berth.values()) * 100 for fuel, amount in fuel_amounts_berth.items()}

    total_CB, total_Fuel_EU_penalty = calculate_total_Fuel_EU_Penalty(
        year, E_totals['intra-eu'], E_totals['inter-eu'], E_totals['berth'], fwind,
        fuel_percentages_intra, fuel_percentages_inter, fuel_percentages_berth,True
    )

    # Calculate total cost
    total_cost = total_fuel_costs['average'] + total_Fuel_EU_penalty + total_EU_ETS_penalty + OPS_cost + OPS_penalty
    fuel_costs = total_cost - total_Fuel_EU_penalty - total_EU_ETS_penalty - OPS_cost - OPS_penalty

    # Print results
    print("\n--- Optimization Results ---")
    print(f"Intra EU energy [MJ]: {E_totals['intra-eu']}")
    print(f"Inter EU energy [MJ]: {E_totals['inter-eu']}")
    print(f"Berth EU energy [MJ]: {E_totals['berth']}")
    print(f"Total Applicable Energy [MJ]: {sum(E_totals.values())}")
    print(f"Optimal fuel amounts (tonnes): {total_fuel_amounts}")
    print(f"Optimal fuel amounts for Intra EU (tonnes): {fuel_amounts_intra}")
    print(f"Optimal fuel amounts for Inter EU (tonnes): {fuel_amounts_inter}")
    print(f"Optimal fuel amounts for Berth (tonnes): {fuel_amounts_berth}")
    print(f"AFTER OPTIMIZATION Intra EU energy [MJ]: {sum(fuel_amounts_intra[fuel] * fuel_densities[fuel] for fuel in fuel_types)}")
    print(f"AFTER OPTIMIZATION Inter EU energy [MJ]: {sum(fuel_amounts_inter[fuel] * fuel_densities[fuel] for fuel in fuel_types)}")
    print(f"AFTER OPTIMIZATION Berth EU energy [MJ]: {sum(fuel_amounts_berth[fuel] * fuel_densities[fuel] for fuel in fuel_types)}")
    print(f"Total CB: {total_CB}")
    print(f"Final FuelEU penalty: {total_Fuel_EU_penalty}")
    print(f"Final EU ETS penalty: {total_EU_ETS_penalty}")
    print(f"EU ETS Allowances [tonnes]: {total_CO2_emissions}")
    print(f"OPS cost: {OPS_cost}")
    print(f"OPS penalty: {OPS_penalty}")
    print(f"Fuel costs: {fuel_costs}")
    print(f"Optimal total cost: {total_cost}")
    
    # df = pd.read_csv('../graphs/data.csv')
    new_row = {'year': year, 'CO2_price': CO2_price_per_ton, 'total_cost':total_cost, 'fuel_cost': fuel_costs, 'eu_ets_penalty': total_EU_ETS_penalty, 'fuelEU_penalty':total_Fuel_EU_penalty, 'eu_ets_allowances':total_CO2_emissions, 'scenario': fuel_types}
    # new_row_df = pd.DataFrame([new_row])

    # df = pd.concat([df, new_row_df], ignore_index=True)

    # df.to_csv('../graphs/data.csv', index=False)
    # print(df)

    # recalculated_cost = objective_function(result.x, E_totals, fuel_types, densities, OPS_flags, OPS_details, year, CO2_price_per_ton, fwind, cost_per_MWh)
    # print(f"Optimal total RECALCULATED cost: {recalculated_cost}")
    # result = [E_totals['intra-eu'], E_totals['inter-eu'], E_totals['berth'], sum(E_totals.values()), total_fuel_amounts, fuel_amounts_intra, fuel_amounts_inter, fuel_amounts_berth, sum(fuel_amounts_intra[fuel] * fuel_densities[fuel] for fuel in fuel_types), sum(fuel_amounts_inter[fuel] * fuel_densities[fuel] for fuel in fuel_types), sum(fuel_amounts_berth[fuel] * fuel_densities[fuel] for fuel in fuel_types), total_CB, total_Fuel_EU_penalty, total_EU_ETS_penalty, total_CO2_emissions, OPS_cost, OPS_penalty, fuel_costs, total_cost]
    result = new_row
    return result

def berth_scenario(percentages, E_total, densities, OPS_use, total_installed_power, established_power_demand, hours_at_berth, cost_per_MWh):
    MJ_to_MWh = 0.0002777778  # Conversion factor from MJ to MWh
    fuel_amounts = {}

    if OPS_use:
        # When OPS is used, assume no MDO is used and no emissions are produced at berth
        OPS_penalty = 1.5 * established_power_demand * hours_at_berth
        E_OPS = E_total
        OPS_cost = E_OPS * MJ_to_MWh * cost_per_MWh
        return fuel_amounts, OPS_penalty, OPS_cost
    else:
        # Standard calculation if OPS is not used
        fuel_amounts = calculate_fuel_amounts(percentages, E_total, densities)
        OPS_penalty = 0
        OPS_cost = 0
        return fuel_amounts, OPS_penalty, OPS_cost

def main():
    year, CO2_price_per_ton, cost_per_MWh, E_totals, fuel_amounts, selected_fuels, OPS_flags, OPS_details, fwind, fuel_densities = get_user_input_FAST()

    # Example scenario
    selected_fuels = ['VLSFO', 'MDO', 'BIO-DIESEL']

     # Optimizing fuel mix
    result = optimize_fuel_mix(
        E_totals=E_totals,
        fuel_types=selected_fuels,
        densities=fuel_densities,
        OPS_flags=OPS_flags,
        OPS_details=OPS_details,
        year=year,
        CO2_price_per_ton=CO2_price_per_ton,
        fwind=fwind,
        cost_per_MWh=cost_per_MWh
    )

    # print("Optimized result:", result)

if __name__ == "__main__":
    main()
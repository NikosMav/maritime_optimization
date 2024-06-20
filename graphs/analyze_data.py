import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV data
df = pd.read_csv('../run/total_output_results.csv')

# Function to plot total cost over years for different CO2 prices for each scenario
def plot_total_cost(df, scenario_num, ops_status):
    plt.figure(figsize=(12, 8))
    subset = df[(df['scenario'] == scenario_num) & (df['OPS_at_berth'] == ops_status)]
    for CO2_price in subset['CO2_price'].unique():
        data = subset[subset['CO2_price'] == CO2_price]
        plt.plot(data['year'], data['total_cost'], label=f'CO2 Price: {CO2_price}€')
    plt.xlabel('Year')
    plt.ylabel('Total Cost (€)')
    plt.title(f'Scenario {scenario_num + 1} {"with" if ops_status else "without"} OPS: Total Cost over Years for Different CO2 Prices')
    plt.legend()
    plt.grid(True)
    plt.show()

# Function to plot EU TS penalty over years for different CO2 prices for each scenario
def plot_eu_ts_penalty(df, scenario_num, ops_status):
    plt.figure(figsize=(12, 8))
    subset = df[(df['scenario'] == scenario_num) & (df['OPS_at_berth'] == ops_status)]
    for CO2_price in subset['CO2_price'].unique():
        data = subset[subset['CO2_price'] == CO2_price]
        plt.plot(data['year'], data['EU_TS_penalty'], label=f'CO2 Price: {CO2_price}€')
    plt.xlabel('Year')
    plt.ylabel('EU TS Penalty (€)')
    plt.title(f'Scenario {scenario_num + 1} {"with" if ops_status else "without"} OPS: EU TS Penalty over Years for Different CO2 Prices')
    plt.legend()
    plt.grid(True)
    plt.show()

# Function to plot FuelEU penalty over years for different CO2 prices for each scenario
def plot_fueleu_penalty(df, scenario_num, ops_status):
    plt.figure(figsize=(12, 8))
    subset = df[(df['scenario'] == scenario_num) & (df['OPS_at_berth'] == ops_status)]
    for CO2_price in subset['CO2_price'].unique():
        data = subset[subset['CO2_price'] == CO2_price]
        plt.plot(data['year'], data['FuelEU_penalty'], label=f'CO2 Price: {CO2_price}€')
    plt.xlabel('Year')
    plt.ylabel('FuelEU Penalty (€)')
    plt.title(f'Scenario {scenario_num + 1} {"with" if ops_status else "without"} OPS: FuelEU Penalty over Years for Different CO2 Prices')
    plt.legend()
    plt.grid(True)
    plt.show()

# Function to plot OPS penalty over years for different CO2 prices for each scenario
def plot_ops_penalty(df, scenario_num, ops_status):
    plt.figure(figsize=(12, 8))
    subset = df[(df['scenario'] == scenario_num) & (df['OPS_at_berth'] == ops_status)]
    for CO2_price in subset['CO2_price'].unique():
        data = subset[subset['CO2_price'] == CO2_price]
        plt.plot(data['year'], data['OPS_penalty'], label=f'CO2 Price: {CO2_price}€')
    plt.xlabel('Year')
    plt.ylabel('OPS Penalty (€)')
    plt.title(f'Scenario {scenario_num + 1} {"with" if ops_status else "without"} OPS: OPS Penalty over Years for Different CO2 Prices')
    plt.legend()
    plt.grid(True)
    plt.show()

# Generate the plots for each scenario
for scenario_num in range(4):
    for ops_status in [True, False]:
        plot_total_cost(df, scenario_num, ops_status)
        plot_eu_ts_penalty(df, scenario_num, ops_status)
        plot_fueleu_penalty(df, scenario_num, ops_status)
        plot_ops_penalty(df, scenario_num, ops_status)

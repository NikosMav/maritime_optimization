import json
import matplotlib.pyplot as plt

# Load the data from the provided JSON file
with open('../run/optimization_results.json', 'r') as file:
    data = json.load(file)

# Extract year, fuel types and their amounts for visualization
years = []
fuel_data = {}

for entry in data:
    year = entry["scenario"]["year"]
    if year not in years:
        years.append(year)
    # Initialize the dictionary for each fuel type
    for mode in ["Intra", "Inter"]:
        fuels = entry["results"][mode]["fuel_types"]
        amounts = entry["results"][mode]["amounts"]
        for fuel in fuels:
            if fuel not in fuel_data:
                fuel_data[fuel] = []
            fuel_data[fuel].append(amounts.get(fuel, 0))

# Prepare the data for line graph plotting
years_sorted = sorted(years)
fuel_series = {fuel: [] for fuel in fuel_data}

# Sort data for each fuel type according to years
for year in years_sorted:
    for fuel in fuel_data:
        fuel_series[fuel].append(sum(fuel_data[fuel][i] for i, y in enumerate(years) if y == year))

# Plotting the fuel usage over years
plt.figure(figsize=(10, 6))
for fuel, amounts in fuel_series.items():
    plt.plot(years_sorted, amounts, label=fuel, marker='o')

plt.title('Fuel Usage by Type Over Years')
plt.xlabel('Year')
plt.ylabel('Fuel Amount (tons)')
plt.legend(title='Fuel Types')
plt.grid(True)
plt.show()

# Extract penalties and costs for each year
penalties_data = {year: {"EU TS": 0, "FuelEU": 0} for year in years_sorted}
costs_data = {year: 0 for year in years_sorted}

for entry in data:
    year = entry["scenario"]["year"]
    # Aggregate penalties and costs data
    for mode in ["Intra", "Inter", "Berth"]:
        penalties = entry["results"][mode].get("penalties", {})
        penalties_data[year]["EU TS"] += penalties.get("EU TS", 0)
        penalties_data[year]["FuelEU"] += penalties.get("FuelEU", 0)
        costs_data[year] += entry["results"][mode]["costs"]["total"]

# Prepare the data for stacked bar graph plotting
eu_ts = [penalties_data[year]["EU TS"] for year in years_sorted]
fuel_eu = [penalties_data[year]["FuelEU"] for year in years_sorted]
total_costs = [costs_data[year] for year in years_sorted]

# Plotting the penalties and costs over years
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

# Penalties Bar Chart
ax1.bar(years_sorted, eu_ts, label='EU TS', color='royalblue')
ax1.bar(years_sorted, fuel_eu, bottom=eu_ts, label='FuelEU', color='skyblue')
ax1.set_title('Penalties Over Years')
ax1.set_ylabel('Penalty Amount (EUR)')
ax1.legend()

# Costs Bar Chart
ax2.bar(years_sorted, total_costs, color='seagreen')
ax2.set_title('Total Costs Over Years')
ax2.set_xlabel('Year')
ax2.set_ylabel('Cost Amount (EUR)')

plt.tight_layout()
plt.show()


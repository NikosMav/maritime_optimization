import pandas as pd
import matplotlib.pyplot as plt

# Load the data
data = pd.read_csv('../run/output_results.csv')

# Convert 'year' to a datetime type if necessary
data['year'] = pd.to_datetime(data['year'], format='%Y')

# Plotting Total Costs Over Time by Scenario
fig, ax = plt.subplots()
for label, df in data.groupby('location'):
    df.groupby('year')['total_cost'].mean().plot(ax=ax, label=label)
ax.set_title('Total Costs Over Time by Scenario')
ax.set_xlabel('Year')
ax.set_ylabel('Average Total Cost')
ax.legend()
plt.show()

# Plotting Penalties Over Time by Scenario
fig, ax = plt.subplots()
for label, df in data.groupby('location'):
    df.groupby('year')[['EU_TS_penalty', 'FuelEU_penalty']].sum().plot(kind='bar', ax=ax, stacked=True)
ax.set_title('Penalties Over Time by Scenario')
ax.set_xlabel('Year')
ax.set_ylabel('Penalties')
ax.legend(['EU TS', 'FuelEU'])
plt.show()

# Additional plots based on your specific data structure and requirements can be added here

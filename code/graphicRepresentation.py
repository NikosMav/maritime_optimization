import openpyxl
from openpyxl.chart import LineChart, BarChart, DoughnutChart, Reference, Series
from optimize_graph import *

def create_excel(data):
    # Create a new workbook and select the active worksheet
    wb = openpyxl.load_workbook("./Charts_Nemo.xlsx")
    # Select the sheet you want to edit
    sheetname = 'Data'  # Replace with your sheet nam
    ws = wb[sheetname]

    # Clear the existing data in the sheet
    ws.delete_rows(1, ws.max_row)
    
    # Create an array of data
    # Write header to worksheet
    ws.append(list(data.keys()))

    # Write data to worksheet
    for i in range(len(data['year'])):
        row = [data[key][i] for key in data]
        for i in range(len(row)):
            if isinstance(row[i],list):
                row[i] = '-'.join(row[i])
                if row[i] == "HFO-MDO-VLSFO":
                    row[i] = "BAU"
            else:
                row[i] = round(row[i])
        ws.append(row)


    wb.save("sample_chart.xlsx")

def main():
    data = {
    'year': [],
    'CO2_price': [],
    'total_cost': [],
    'fuel_cost': [],
    'eu_ets_penalty': [],
    'fuelEU_penalty': [],
    'eu_ets_allowances': [],
    'scenario': []
    }

    year, CO2_price_per_ton, cost_per_MWh, E_totals, fuel_amounts, selected_fuels, OPS_flags, OPS_details, fwind, fuel_densities = get_user_input_FAST()

    # Example scenario
    all_selected_fuels = [
        ['HFO', 'MDO', 'VLSFO'],
        ['LNG', 'MDO', 'VLSFO'],
        ['VLSFO', 'MDO', 'BIO-DIESEL']
        ]

    total_years = [2025, 2030, 2035, 2040, 2045, 2050]

    # total_results = []

    for selected_fuels in all_selected_fuels:
        for year in total_years:
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
            for key in result:
                data[key].append(result[key])
            print(data)
    
    create_excel(data)
    

    # print("Optimized result:", result)

if __name__ == "__main__":
    main()

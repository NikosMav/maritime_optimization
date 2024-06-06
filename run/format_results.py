################################ NOT READY ###################################

import json

def main():
    # Load the JSON file with results
    with open('optimization_results.json', 'r') as file:
        data = json.load(file)

    with open('formatted_results.txt', 'w') as output_file:
        # Process each scenario's results
        for entry in data:
            output_file.write("Scenario Details:\n")
            for key, value in entry['scenario'].items():
                output_file.write(f"  {key}: {value}\n")
            
            output_file.write("\nResults Summary:\n")
            results = entry['results']
            
            # Extract and print the results in a formatted way
            intra_results = extract_section(results, "For intra-eu")
            inter_results = extract_section(results, "For inter-eu")
            berth_results = extract_section(results, "Berth scenario using only MDO:")
            
            output_file.write("Intra EU Results:\n")
            output_file.write(intra_results + "\n\n")
            
            output_file.write("Inter EU Results:\n")
            output_file.write(inter_results + "\n\n")
            
            output_file.write("Berth Results:\n")
            output_file.write(berth_results + "\n")

def extract_section(text, section_name):
    try:
        section_start = text.index(section_name) + len(section_name)
        next_section_start = text.find("The EU TS Penalty", section_start)
        return text[section_start:next_section_start].strip()
    except ValueError:
        return "Information not found"

if __name__ == "__main__":
    main()

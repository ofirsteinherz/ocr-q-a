import csv
import json
from typing import Dict, Set, Tuple
import re

class FormProcessor:
    def __init__(self):
        self.updated_fields: Set[Tuple[str, str]] = set()
        self.all_fields: Set[Tuple[str, str]] = set()
        
    def normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for consistent comparison"""
        # Replace different types of quotes with a standard one
        normalized = field_name.replace('״', '"').replace('"', '"')
        
        # Normalize spaces around forward slashes
        normalized = re.sub(r'\s*/\s*', '/', normalized)
        
        # Remove any double spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Trim whitespace
        normalized = normalized.strip()
        
        return normalized

    def collect_all_fields(self, json_data: Dict) -> None:
        """Collect all fields from JSON structure"""
        for section in json_data['sections']:
            section_id = section['id']
            for field in section['fields']:
                if 'sub_fields' in field:
                    for sub_field in field['sub_fields']:
                        self.all_fields.add((section_id, f"{field['label']}/{sub_field['label']}"))
                else:
                    self.all_fields.add((section_id, field['label']))

    def update_json_with_csv(self, json_data: Dict, csv_file: str) -> Dict:
        # Collect all fields first
        self.collect_all_fields(json_data)
        
        # Read CSV data
        csv_data = {}
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f, delimiter='|')
            for row in csv_reader:
                section = row['section']
                field = self.normalize_field_name(row['field'])
                value = row['value']
                
                if section not in csv_data:
                    csv_data[section] = {}
                csv_data[section][field] = value

        # Update JSON data
        for section in json_data['sections']:
            section_id = section['id']
            for field in section['fields']:
                if 'sub_fields' in field:
                    # Handle fields with sub-fields
                    for sub_field in field['sub_fields']:
                        csv_key = self.normalize_field_name(f"{field['label']}/{sub_field['label']}")
                        if section_id in csv_data and csv_key in csv_data[section_id]:
                            sub_field['value'] = csv_data[section_id][csv_key]
                            self.updated_fields.add((section_id, f"{field['label']}/{sub_field['label']}"))
                else:
                    # Handle regular fields
                    normalized_field = self.normalize_field_name(field['label'])
                    if section_id in csv_data and normalized_field in csv_data[section_id]:
                        field['value'] = csv_data[section_id][normalized_field]
                        self.updated_fields.add((section_id, field['label']))

        return json_data

    def print_update_report(self) -> None:
        """Print a report of updated and missing fields"""
        print("\n=== Field Update Report ===")
        print(f"\nTotal fields in form: {len(self.all_fields)}")
        print(f"Total fields updated: {len(self.updated_fields)}")
        
        missing_fields = self.all_fields - self.updated_fields
        if missing_fields:
            print("\nMissing/Not Updated Fields:")
            for section, field in sorted(missing_fields):
                print(f"- {section}: {field}")
                # Add CSV format hint
                print(f"  CSV format should be: {section}|{field}|value")
        else:
            print("\nAll fields were successfully updated!")
        
        print("\nUpdated Fields:")
        for section, field in sorted(self.updated_fields):
            print(f"+ {section}: {field}")

# Example usage:
if __name__ == "__main__":
    # Initialize the processor
    processor = FormProcessor()

    # Load your original JSON
    with open('form_elements.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Update with CSV data
    updated_json = processor.update_json_with_csv(json_data, 'files/form_template.csv')

    # Save the updated JSON
    with open('files/updated_form.json', 'w', encoding='utf-8') as f:
        json.dump(updated_json, f, ensure_ascii=False, indent=4)

    # Print the update report
    processor.print_update_report()

import os
import json
from fake_csv import FakeFormDataGenerator
from form_processor import FormProcessor
from insert_pdf import add_text_to_pdf

def main():
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(script_dir, "files")
    
    # Ensure files directory exists
    os.makedirs(files_dir, exist_ok=True)

    # Define all file paths
    fake_csv_path = os.path.join(files_dir, "fake_form_data.csv")
    form_elements_json = os.path.join(script_dir, "form_elements.json")
    updated_form_json = os.path.join(files_dir, "updated_form.json")
    input_pdf = os.path.join(files_dir, "283_raw.pdf")
    output_pdf = os.path.join(files_dir, "output_high_res.pdf")

    try:
        # Step 1: Generate fake CSV data
        print("\n=== Step 1: Generating fake CSV data ===")
        generator = FakeFormDataGenerator()
        generator.save_to_csv(fake_csv_path)
        print("✓ Fake CSV file has been generated successfully!")

        # Step 2: Process form data using the generated fake CSV
        print("\n=== Step 2: Processing form data ===")
        processor = FormProcessor()
        
        # Load original JSON
        with open(form_elements_json, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Update with the generated fake CSV data
        updated_json = processor.update_json_with_csv(json_data, fake_csv_path)

        # Save the updated JSON
        with open(updated_form_json, 'w', encoding='utf-8') as f:
            json.dump(updated_json, f, ensure_ascii=False, indent=4)
        
        processor.print_update_report()
        print("✓ Form processing completed successfully!")

        # Step 3: Insert text into PDF using the updated form data
        print("\n=== Step 3: Generating final PDF ===")
        add_text_to_pdf(input_pdf, output_pdf, updated_form_json, zoom=3)
        print("✓ PDF generation completed successfully!")

        print("\n=== Process completed successfully! ===")
        print(f"Output PDF saved to: {output_pdf}")

    except FileNotFoundError as e:
        print(f"\nError: Required file not found: {str(e)}")
        print("Please ensure all required files are in the correct locations:")
        print(f"- Input PDF: {input_pdf}")
        print(f"- Form elements JSON: {form_elements_json}")
    
    except Exception as e:
        print(f"\nError occurred during processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()
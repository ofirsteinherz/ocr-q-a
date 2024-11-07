import os
import json
import csv
import pandas as pd
from fake_csv import FakeFormDataGenerator
from form_processor import FormProcessor
from insert_pdf import add_text_to_pdf

def main():
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(script_dir, "files")
    pdfs_dir = os.path.join(files_dir, "generated_pdfs")
    
    # Ensure directories exist
    os.makedirs(files_dir, exist_ok=True)
    os.makedirs(pdfs_dir, exist_ok=True)

    # Define file paths
    form_elements_json = os.path.join(script_dir, "form_elements.json")
    input_pdf = os.path.join(files_dir, "283_raw.pdf")
    master_csv_path = os.path.join(files_dir, "master_data.csv")

    try:
        # Initialize generator and processor
        generator = FakeFormDataGenerator()
        processor = FormProcessor()
        
        # Load original JSON template
        with open(form_elements_json, 'r', encoding='utf-8') as f:
            json_template = json.load(f)

        # List to store all generated data
        all_data = []

        print("\n=== Starting batch PDF generation ===")
        
        # Generate 100 PDFs
        for i in range(100):
            print(f"\nProcessing PDF {i+1}/100")
            
            # Generate temporary CSV for this iteration
            temp_csv_path = os.path.join(files_dir, f"temp_form_data_{i}.csv")
            generator.save_to_csv(temp_csv_path)
            
            # Update JSON with the generated fake CSV data
            updated_json = processor.update_json_with_csv(json_template.copy(), temp_csv_path)
            
            # Read the generated CSV data and add filename column
            df = pd.read_csv(temp_csv_path, on_bad_lines='skip', escapechar='\\', quoting=csv.QUOTE_ALL)
            pdf_filename = f"form_{i+1}.pdf"
            df['filename'] = pdf_filename
            
            # Add data to master list
            all_data.append(df)
            
            # Save updated JSON temporarily
            temp_json_path = os.path.join(files_dir, f"temp_form_{i}.json")
            with open(temp_json_path, 'w', encoding='utf-8') as f:
                json.dump(updated_json, f, ensure_ascii=False, indent=4)
            
            # Generate PDF
            output_pdf = os.path.join(pdfs_dir, pdf_filename)
            add_text_to_pdf(input_pdf, output_pdf, temp_json_path, zoom=3)
            
            # Clean up temporary files
            os.remove(temp_csv_path)
            os.remove(temp_json_path)
            
            print(f"✓ Generated PDF: {pdf_filename}")

        # Create and save master CSV
        master_df = pd.concat(all_data, ignore_index=True)
        
        # Reorder columns to put filename first
        cols = master_df.columns.tolist()
        cols.remove('filename')
        cols = ['filename'] + cols
        master_df = master_df[cols]
        
        master_df.to_csv(master_csv_path, index=False)
        
        print("\n=== Batch processing completed successfully! ===")
        print(f"Generated PDFs are saved in: {pdfs_dir}")
        print(f"Master CSV saved to: {master_csv_path}")

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
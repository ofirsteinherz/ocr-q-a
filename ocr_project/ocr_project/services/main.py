import json
import csv
import pandas as pd
from pathlib import Path

from ocr_project.utils.fake_csv import FakeFormDataGenerator
from ocr_project.core.form_processor import FormProcessor
from ocr_project.processors.insert_pdf import add_text_to_pdf
from ocr_project.config.settings import settings

def main():
    try:
        # Validate required files exist
        if not settings.validate_required_files():
            return
            
        # Initialize generator and processor
        generator = FakeFormDataGenerator()
        processor = FormProcessor()
        
        # Load original JSON template
        with open(settings.FORM_ELEMENTS_JSON, 'r', encoding='utf-8') as f:
            json_template = json.load(f)

        # List to store all generated data
        all_data = []

        print("\n=== Starting batch PDF generation ===")
        
        # Generate PDFs
        for i in range(settings.NUM_PDFS_TO_GENERATE):
            print(f"\nProcessing PDF {i+1}/{settings.NUM_PDFS_TO_GENERATE}")
            
            # Generate temporary CSV for this iteration
            temp_csv_path = settings.get_temp_path(f"temp_form_data_{i}.csv")
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
            temp_json_path = settings.get_temp_path(f"temp_form_{i}.json")
            with open(temp_json_path, 'w', encoding='utf-8') as f:
                json.dump(updated_json, f, ensure_ascii=False, indent=4)
            
            # Generate PDF
            output_pdf = settings.get_output_pdf_path(pdf_filename)
            add_text_to_pdf(
                settings.RAW_PDF_PATH,
                output_pdf,
                temp_json_path,
                zoom=settings.PDF_ZOOM
            )
            
            # Clean up temporary files
            Path(temp_csv_path).unlink(missing_ok=True)
            Path(temp_json_path).unlink(missing_ok=True)
            
            print(f"✓ Generated PDF: {pdf_filename}")

        # Create and save master CSV
        master_df = pd.concat(all_data, ignore_index=True)
        
        # Reorder columns to put filename first
        cols = master_df.columns.tolist()
        cols.remove('filename')
        cols = ['filename'] + cols
        master_df = master_df[cols]
        
        master_df.to_csv(settings.MASTER_DATA_CSV, index=False)
        
        print("\n=== Batch processing completed successfully! ===")
        print(f"Generated PDFs are saved in: {settings.GENERATED_PDFS_DIR}")
        print(f"Master CSV saved to: {settings.MASTER_DATA_CSV}")

    except Exception as e:
        print(f"\nError occurred during processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()
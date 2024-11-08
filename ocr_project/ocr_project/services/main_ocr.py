import logging
from pathlib import Path
import json
import re

from ocr_project.config.settings import settings
from ocr_project.core.extract_form_fields import ExtractFormFields

def setup_logging():
    """Configure logging for the main OCR process"""
    settings.LOGS_DIR.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.LOGS_DIR / 'ocr_main.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('OCR_Main')

def get_form_number(filename: str) -> int:
    """Extract form number from filename."""
    match = re.search(r'form_(\d+)\.pdf', filename)
    return int(match.group(1)) if match else 0

def process_forms():
    """Process all forms in the generated PDFs directory"""
    logger = setup_logging()
    logger.info("\nStarting form processing application...")
    
    try:
        # Initialize processor
        processor = ExtractFormFields()
        
        # Get all PDF files and sort them by form number
        pdf_files = list(settings.GENERATED_PDFS_DIR.glob("form_*.pdf"))
        pdf_files.sort(key=lambda x: get_form_number(x.name))
        
        if not pdf_files:
            logger.error("No PDF files found in the generated PDFs directory")
            return
            
        total_files = len(pdf_files)
        processed_count = 0
        skipped_count = 0
        failed_count = 0
        
        logger.info(f"Found {total_files} PDF files to process")
        
        # Keep track of processed files
        processed_forms = set()
        existing_analyses = set(f.stem.replace('_analysis', '') for f in settings.ANALYZED_FORMS_DIR.glob("*_analysis.json"))
        
        # Process each form
        for pdf_file in pdf_files:
            form_name = pdf_file.stem
            
            # Skip if already processed
            if form_name in existing_analyses:
                logger.info(f"Skipping {form_name} - already processed")
                skipped_count += 1
                continue
                
            logger.info(f"\nProcessing form {get_form_number(pdf_file.name)}/{total_files}: {pdf_file.name}")
            
            try:
                # Process form
                results = processor.process_form(
                    pdf_path=pdf_file,
                    output_dir=settings.ANALYZED_FORMS_DIR
                )
                
                # Save results
                output_path = settings.ANALYZED_FORMS_DIR / f"{pdf_file.stem}_analysis.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                processed_forms.add(form_name)
                processed_count += 1
                logger.info(f"✓ Results saved to {output_path}")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {str(e)}")
                failed_count += 1
                continue
        
        # Report processing statistics
        logger.info("\n=== Processing Summary ===")
        logger.info(f"Total files found: {total_files}")
        logger.info(f"Successfully processed: {processed_count}")
        logger.info(f"Already processed (skipped): {skipped_count}")
        logger.info(f"Failed to process: {failed_count}")
        
        # Check for missing files
        expected_forms = set(f"form_{i}" for i in range(1, max(get_form_number(f.name) for f in pdf_files) + 1))
        missing_forms = expected_forms - processed_forms - existing_analyses
        
        if missing_forms:
            logger.warning("\nMissing form files:")
            for form in sorted(missing_forms, key=lambda x: get_form_number(x)):
                logger.warning(f"- {form}.pdf")
        
        logger.info("\nProcessing completed")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise
    finally:
        settings.clean_pycache()

def main():
    process_forms()

if __name__ == "__main__":
    main()
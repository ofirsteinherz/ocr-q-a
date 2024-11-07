import os
from dotenv import load_dotenv

from document_analyzer import DocumentAnalyzer

# Load environment variables from .env file
load_dotenv(verbose=True)

def main():

    # Initialize analyzer
    analyzer = DocumentAnalyzer(
        api_key=os.getenv("AZURE_DOCUMENT_KEY"),
        endpoint=os.getenv("AZURE_DOCUMENT_ENDPOINT")
    )

    # Example for single document

    # Define base directories relative to the current script's directory
    form_1_pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files", "generated_pdfs", "form_1.pdf")

    # You can use this path to read or write the file
    print(f"PDF Path: {form_1_pdf_path}")

    extracted_data = analyzer.analyze_local_document(form_1_pdf_path)
    
    print(extracted_data)

if __name__ == "__main__":
    main()

import csv
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import pandas as pd
from typing import List, Dict
import logging
from pathlib import Path

class DocumentAnalyzer:
    def __init__(self, endpoint: str, api_key: str, verbose: bool = False):
        """
        Initialize the Document Analyzer with Azure credentials
        
        Args:
            endpoint (str): Azure Form Recognizer endpoint
            api_key (str): Azure Form Recognizer key
            verbose (bool): Whether to show detailed logging information
        """
        self.client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        
        # Configure logging
        logging.basicConfig(level=logging.WARNING)  # Set default level to WARNING
        self.logger = logging.getLogger(__name__)
        
        # Disable Azure SDK logging
        logging.getLogger('azure').setLevel(logging.WARNING)
        logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
        
        # Set logger level based on verbose flag
        if verbose:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)

    def analyze_local_document(self, file_path: str) -> Dict:
        """
        Analyze a local document and extract key-value pairs
        
        Args:
            file_path (str): Path to the local document
            
        Returns:
            Dict: Extracted data in dictionary format
        """
        try:
            # Verify file exists
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Document not found at: {file_path}")

            self.logger.info(f"Starting analysis of local document: {file_path}")
            
            # Open and read the file
            with open(file_path, "rb") as f:
                poller = self.client.begin_analyze_document(
                    "prebuilt-document", 
                    document=f
                )
                result = poller.result()
            
            # Extract all relevant information
            extracted_data = {
                'key_value_pairs': {},
                'tables': [],
                'paragraphs': [],
                'form_fields': []
            }
            
            # Extract key-value pairs
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    extracted_data['key_value_pairs'][kv_pair.key.content] = kv_pair.value.content
            
            # Extract tables
            for table in result.tables:
                table_data = []
                for cell in table.cells:
                    table_data.append({
                        'row': cell.row_index,
                        'column': cell.column_index,
                        'content': cell.content
                    })
                extracted_data['tables'].append(table_data)
            
            # Extract paragraphs
            for paragraph in result.paragraphs:
                extracted_data['paragraphs'].append(paragraph.content)
            
            # Extract form fields (checkboxes, textboxes, etc.)
            if hasattr(result, 'form_fields'):
                for field in result.form_fields:
                    extracted_data['form_fields'].append({
                        'name': field.name,
                        'value': field.value,
                        'type': field.type
                    })
            
            self.logger.info("Document analysis completed successfully")
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing document: {str(e)}")
            raise

def analyze_document(endpoint: str, api_key: str, file_path: str, verbose: bool = False) -> Dict:
    """
    Convenience function to analyze a single document without explicitly creating an analyzer instance
    
    Args:
        endpoint (str): Azure Form Recognizer endpoint
        api_key (str): Azure Form Recognizer key
        file_path (str): Path to the document to analyze
        verbose (bool): Whether to show detailed logging information
        
    Returns:
        Dict: Extracted data in dictionary format
    """
    analyzer = DocumentAnalyzer(endpoint, api_key, verbose=verbose)
    return analyzer.analyze_local_document(file_path)
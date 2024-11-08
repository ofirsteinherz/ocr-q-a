import os
from pathlib import Path

class Settings:
    def __init__(self):
        # Base directories
        self.PACKAGE_ROOT = Path(__file__).parent.parent  # ocr_project/ocr_project
        self.PROJECT_ROOT = self.PACKAGE_ROOT.parent      # ocr_project
        
        # Directory paths
        self.CONFIG_DIR = self.PROJECT_ROOT / "config"
        self.RESOURCES_DIR = self.PROJECT_ROOT / "resources"
        self.OUTPUT_DIR = self.PROJECT_ROOT / "output"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        
        # Create necessary directories
        for directory in [self.CONFIG_DIR, self.RESOURCES_DIR, self.OUTPUT_DIR, self.LOGS_DIR]:
            directory.mkdir(exist_ok=True)
            
        # File paths - Updated to use RESOURCES_DIR
        self.RAW_PDF_PATH = self.RESOURCES_DIR / "283_raw.pdf"
        self.FORM_ELEMENTS_JSON = self.RESOURCES_DIR / "form_elements.json"  # Changed from CONFIG_DIR
        self.FORM_TEMPLATE_CSV = self.RESOURCES_DIR / "form_template.csv"    # Changed from CONFIG_DIR
        
        # Output paths
        self.GENERATED_PDFS_DIR = self.OUTPUT_DIR / "generated_pdfs"
        self.TEMP_DIR = self.OUTPUT_DIR / "temp"
        self.MASTER_DATA_CSV = self.OUTPUT_DIR / "master_data.csv"
        
        # Create output directories
        self.GENERATED_PDFS_DIR.mkdir(exist_ok=True)
        self.TEMP_DIR.mkdir(exist_ok=True)
        
        # Font settings
        self.FONT_PATH = "/usr/share/fonts/dejavu/DejaVuSans.ttf"
        
        # Processing settings
        self.PDF_ZOOM = 3
        self.NUM_PDFS_TO_GENERATE = 100
        
    def get_temp_path(self, filename):
        """Get path for temporary files"""
        return self.TEMP_DIR / filename
        
    def get_output_pdf_path(self, filename):
        """Get path for generated PDF files"""
        return self.GENERATED_PDFS_DIR / filename

    def validate_required_files(self):
        """Validate that all required files exist"""
        required_files = {
            'Raw PDF': self.RAW_PDF_PATH,
            'Form Elements JSON': self.FORM_ELEMENTS_JSON,
            'Form Template CSV': self.FORM_TEMPLATE_CSV
        }
        
        missing_files = []
        for name, path in required_files.items():
            if not path.exists():
                missing_files.append(f"{name}: {path}")
        
        if missing_files:
            print("\nMissing required files:")
            for file in missing_files:
                print(f"- {file}")
            return False
        return True

# Create a global settings instance
settings = Settings()
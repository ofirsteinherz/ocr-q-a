import os
from pathlib import Path

class Settings:
    def __init__(self):
        # Base directories
        self.PACKAGE_ROOT = Path(__file__).parent.parent
        self.PROJECT_ROOT = self.PACKAGE_ROOT.parent
        
        # Directory paths
        self.CONFIG_DIR = self.PROJECT_ROOT / "config"
        self.RESOURCES_DIR = self.PROJECT_ROOT / "resources"
        self.OUTPUT_DIR = self.PROJECT_ROOT / "output"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        
        # Prompts directory
        self.PROMPTS_DIR = self.RESOURCES_DIR / "prompts"
        
        # Output paths
        self.GENERATED_PDFS_DIR = self.OUTPUT_DIR / "generated_pdfs"
        self.TEMP_DIR = self.OUTPUT_DIR / "temp"
        self.MASTER_DATA_CSV = self.OUTPUT_DIR / "master_data.csv"
        self.ANALYZED_FORMS_DIR = self.OUTPUT_DIR / "analyzed_forms"
        
        # All directories that need to be created
        self.GENERATED_DIRS = [
            self.OUTPUT_DIR,
            self.LOGS_DIR,
            self.GENERATED_PDFS_DIR,
            self.TEMP_DIR,
            self.ANALYZED_FORMS_DIR
        ]
        
        # Create all directories
        for directory in [self.CONFIG_DIR, self.RESOURCES_DIR] + self.GENERATED_DIRS:
            directory.mkdir(exist_ok=True)
            
        # File paths
        self.RAW_PDF_PATH = self.RESOURCES_DIR / "283_raw.pdf"
        self.FORM_ELEMENTS_JSON = self.RESOURCES_DIR / "form_elements.json"
        self.FORM_TEMPLATE_CSV = self.RESOURCES_DIR / "form_template.csv"
        
        # Font settings
        self.FONT_PATH = "/usr/share/fonts/dejavu/DejaVuSans.ttf"
        
        # Processing settings
        self.PDF_ZOOM = 3
        self.NUM_PDFS_TO_GENERATE = 100

        # Form processing settings
        self.FORM_CONFIG_DIR = self.CONFIG_DIR
        self.SCHEMA_FILE = self.RESOURCES_DIR / "schema.json"
        self.SECTIONS_FILE = self.RESOURCES_DIR / "sections.json"
        
        # Image processing settings
        self.DEFAULT_DPI = 300

    def clean_pycache(self):
        """Remove all __pycache__ directories in the project"""
        for root, dirs, files in os.walk(self.PROJECT_ROOT):
            for dir in dirs:
                if dir == "__pycache__":
                    cache_path = Path(root) / dir
                    print(f"Removing cache directory: {cache_path}")
                    try:
                        for file in cache_path.glob("*"):
                            file.unlink()
                        cache_path.rmdir()
                    except Exception as e:
                        print(f"Error removing {cache_path}: {e}")

    def get_prompt(self, prompt_name: str) -> str:
        """Get the content of a specific prompt file from the prompts directory"""
        prompt_path = self.PROMPTS_DIR / f"{prompt_name}.txt"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        except Exception as e:
            raise Exception(f"Error reading prompt file {prompt_path}: {str(e)}")

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
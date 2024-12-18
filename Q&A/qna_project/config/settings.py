import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Tuple

class Settings:
    def __init__(self):
        # Base directories
        self.PACKAGE_ROOT = Path(__file__).parent.parent
        self.PROJECT_ROOT = self.PACKAGE_ROOT.parent
        
        # Directory paths
        self.RESOURCES_DIR = self.PROJECT_ROOT / "resources"
        self.OUTPUT_DIR = self.PROJECT_ROOT / "output"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        
        # Resource subdirectories
        self.RAW_HTML_DIR = self.RESOURCES_DIR / "raw_html"
        self.PROMPTS_DIR = self.RESOURCES_DIR / "prompts"
        self.PROCESSED_HTML_DIR = self.RESOURCES_DIR / "processed_html"
        
        # Output subdirectories
        self.TEMP_DIR = self.OUTPUT_DIR / "temp"

        # Prompts directory
        self.PROMPTS_DIR = self.RESOURCES_DIR / "prompts"
        
        # All directories that need to be created
        self.GENERATED_DIRS = [
            self.OUTPUT_DIR,
            self.LOGS_DIR,
            self.PROCESSED_HTML_DIR,
            self.TEMP_DIR
        ]

        # Load environment variables
        load_dotenv(dotenv_path=self.PROJECT_ROOT / ".env", verbose=True)

        # Required environment variables
        self.REQUIRED_ENV_VARS = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT"
        ]
        
        
        # Create all directories
        for directory in [self.RESOURCES_DIR] + self.GENERATED_DIRS:
            directory.mkdir(parents=True, exist_ok=True)

    
    def validate_environment(self, logger: logging.Logger = None) -> Tuple[bool, List[str]]:
        """
        Validate all required environment variables are set.
        
        Args:
            logger: Optional logger instance for logging messages
            
        Returns:
            Tuple of (is_valid: bool, missing_vars: List[str])
        """
        # Check for missing variables
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        
        if missing_vars:
            message = "Missing required environment variables:"
            if logger:
                logger.error(message)
                for var in missing_vars:
                    logger.error(f"- {var}")
                logger.error("\nPlease create a .env file in the project root with these variables.")
            return False, missing_vars
        
        return True, []

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

    def validate_required_files(self) -> Tuple[bool, List[str]]:
        """Validate that all required HTML files exist"""
        required_files = [
            'alternative_services.html',
            'communication_clinic_services.html',
            'dentel_services.html',
            'optometry_services.html',
            'pragrency_services.html',
            'workshops_services.html'
        ]
        
        missing_files = []
        for filename in required_files:
            if not (self.RAW_HTML_DIR / filename).exists():
                missing_files.append(filename)
        
        return len(missing_files) == 0, missing_files

    def get_html_files(self) -> List[Path]:
        """Get a list of all HTML files in the raw_html directory"""
        return list(self.RAW_HTML_DIR.glob('*.html'))

    def get_output_path(self, input_filename: str) -> Path:
        """Get the output path for a processed HTML file"""
        return self.PROCESSED_HTML_DIR / input_filename.replace('.html', '.json')
    
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

# Create a global settings instance
settings = Settings()
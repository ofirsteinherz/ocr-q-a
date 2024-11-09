from pathlib import Path
from typing import Dict, List, Optional, Literal
import json
import logging
from dataclasses import dataclass

from qna_project.config.settings import Settings

@dataclass
class HealthcareFilter:
    provider: Literal['maccabi', 'meuhedet', 'clalit']  # Validation for providers
    plan: Literal['gold', 'silver', 'bronze']           # Validation for plans

    def __post_init__(self):
        valid_providers = {'maccabi', 'meuhedet', 'clalit'}
        valid_plans = {'gold', 'silver', 'bronze'}
        
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid provider. Must be one of: {valid_providers}")
        
        if self.plan not in valid_plans:
            raise ValueError(f"Invalid plan. Must be one of: {valid_plans}")

class HealthcareProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.json_dir = self.settings.PROCESSED_HTML_DIR
        self._cache = {}

    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON file if not in cache"""
        file_key = str(file_path)
        if file_key not in self._cache:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._cache[file_key] = json.load(f)
            except FileNotFoundError as e:
                logging.error(f"Failed to load {file_path}: {e}")
                return {}
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in {file_path}: {e}")
                return {}
        return self._cache[file_key]

    def _filter_services_by_provider(self, services: List[Dict], healthcare_filter: HealthcareFilter) -> List[Dict]:
        """Filter services based on provider and plan"""
        filtered_services = []
        
        for service in services:
            if healthcare_filter.provider in service.get('providers', {}):
                plan_data = service['providers'][healthcare_filter.provider].get(healthcare_filter.plan)
                if plan_data:  # If we have data for this plan
                    filtered_service = {
                        'name': service['name'],
                        'details': plan_data  # Keep the original text without parsing
                    }
                    filtered_services.append(filtered_service)
        
        return filtered_services

    def _filter_contact_info(self, contact_info: Dict, provider: str) -> Dict:
        """Filter contact information for specific provider"""
        filtered_contact = {}
        
        if 'phone_numbers' in contact_info and provider in contact_info['phone_numbers']:
            filtered_contact['phone_numbers'] = contact_info['phone_numbers'][provider]
            
        if 'additional_info' in contact_info and provider in contact_info['additional_info']:
            filtered_contact['additional_info'] = contact_info['additional_info'][provider]
            
        return filtered_contact

    def _process_json_file(self, file_path: Path, healthcare_filter: HealthcareFilter) -> Dict:
        """Process a single JSON file and return filtered data"""
        data = self._load_json(file_path)
        result = {}

        if 'general_info' in data:
            result['general_info'] = data['general_info']
            
        if 'services' in data:
            result['services'] = self._filter_services_by_provider(
                data['services'],
                healthcare_filter
            )
            
        if 'contact_info' in data:
            result['contact_info'] = self._filter_contact_info(
                data['contact_info'],
                healthcare_filter.provider
            )

        return result

    def get_all_services_data(self, healthcare_filter: HealthcareFilter) -> Dict:
        """Get data from all JSON files in the directory, filtered by provider and plan"""
        result = {}
        
        try:
            for file_path in self.json_dir.glob('*.json'):
                file_name = file_path.stem
                result[file_name] = self._process_json_file(file_path, healthcare_filter)
                
        except Exception as e:
            logging.error(f"Error processing services data: {e}")
            
        return result
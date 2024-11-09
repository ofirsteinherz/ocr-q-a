import logging
from typing import Dict
import json

from qna_project.clients.healthcare_provider import HealthcareProvider, HealthcareFilter
from qna_project.config.settings import Settings

class CustomerService:
    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()
        self.customer_provider = HealthcareProvider(self.settings)
    
    def get_all_provider_services(self, provider: str, plan: str) -> Dict:
        try:
            provider_filter = HealthcareFilter(provider=provider, plan=plan)
            return self.customer_provider.get_all_services_data(provider_filter)
        except ValueError as e:
            logging.error(f"Invalid provider or plan: {e}")
            return {}

# Example usage:
if __name__ == "__main__":
    settings = Settings()
    service = CustomerService(settings)

    # Get all services for Maccabi Gold
    maccabi_gold_services = service.get_all_provider_services('maccabi', 'gold')
    json_response = json.dumps(maccabi_gold_services, indent=4, ensure_ascii=False)
    print(json_response)

    settings.clean_pycache()

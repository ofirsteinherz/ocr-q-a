from bs4 import BeautifulSoup
import json
import re
from pathlib import Path

from qna_project.config.settings import settings

class HTMLProcessor:
    def __init__(self):
        """Initialize the HTML processor using project settings."""
        self.raw_html_dir = settings.RAW_HTML_DIR
        self.output_dir = settings.PROCESSED_HTML_DIR

    def _extract_general_info(self, soup):
        """Extract title and general description from the HTML."""
        title = soup.find('h2').text.strip()
        description = soup.find('p').text.strip()
        
        return {
            "title": title,
            "description": description
        }

    def _parse_cell_content(self, cell_text):
        """Keep the original cell text without parsing"""
        if not cell_text or cell_text == "ללא הנחה":
            return "ללא הנחה"
        return cell_text.strip()

    def _parse_service_cell(self, cell_text):
        """Parse a cell containing information for all three plans."""
        plans = {}
        if not cell_text:
            return plans
        
        plan_texts = cell_text.split('\n')
        
        for plan_text in plan_texts:
            plan_text = plan_text.strip()
            if not plan_text:
                continue
                
            if plan_text.startswith('זהב:'):
                plans['gold'] = plan_text.replace('זהב:', '').strip()
            elif plan_text.startswith('כסף:'):
                plans['silver'] = plan_text.replace('כסף:', '').strip()
            elif plan_text.startswith('ארד:'):
                plans['bronze'] = plan_text.replace('ארד:', '').strip()
        
        return plans

    def _extract_services(self, soup):
        """Extract services information from the table."""
        services = []
        table = soup.find('table')
        
        if not table:
            return services
        
        rows = table.find_all('tr')
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) < 4:  # Skip invalid rows
                continue
                
            service_name = cells[0].text.strip()
            
            service = {
                "name": service_name,
                "providers": {
                    "maccabi": self._parse_service_cell(cells[1].text.strip()),
                    "meuhedet": self._parse_service_cell(cells[2].text.strip()),
                    "clalit": self._parse_service_cell(cells[3].text.strip())
                }
            }
            
            services.append(service)
        
        return services

    def _extract_contact_info(self, soup):
        """Extract contact information including phone numbers and additional info."""
        contact_info = {
            "phone_numbers": {},
            "additional_info": {}
        }
        
        phone_section = soup.find(string=re.compile('מספרי טלפון')).find_parent()
        if phone_section:
            phone_list = phone_section.find_next('ul')
            if phone_list:
                for item in phone_list.find_all('li'):
                    text = item.text.strip()
                    for provider, name in [('מכבי', 'maccabi'), ('מאוחדת', 'meuhedet'), ('כללית', 'clalit')]:
                        if provider in text:
                            numbers = re.findall(r'\*\d+|\d+-[\d-]+', text)
                            contact_info["phone_numbers"][name] = {
                                "short": numbers[0] if len(numbers) > 0 else "",
                                "long": numbers[1] if len(numbers) > 1 else "",
                                "extension": text.split('שלוחה')[-1].strip() if 'שלוחה' in text else ""
                            }
        
        additional_section = soup.find(string=re.compile('לפרטים נוספים')).find_parent()
        if additional_section:
            info_list = additional_section.find_next('ul')
            if info_list:
                for item in info_list.find_all('li'):
                    text = item.text.strip()
                    for provider, name in [('מכבי', 'maccabi'), ('מאוחדת', 'meuhedet'), ('כללית', 'clalit')]:
                        if provider in text:
                            phone = re.search(r'\d+-[\d-]+', text)
                            website = re.search(r'https?://\S+', text)
                            contact_info["additional_info"][name] = {
                                "phone": phone.group() if phone else "",
                                "website": website.group() if website else ""
                            }
        
        return contact_info

    def parse_html_to_json(self, html_content):
        """Parse the specialized HTML format into a structured JSON format."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = {
            "general_info": self._extract_general_info(soup),
            "services": self._extract_services(soup),
            "contact_info": self._extract_contact_info(soup)
        }
        
        return result

    
    def process_file(self, input_filename: str) -> dict:
        """
        Process a single HTML file and save the result as JSON.
        
        Args:
            input_filename (str): Name of the HTML file to process
        
        Returns:
            dict: Parsed data in dictionary format
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            Exception: For other processing errors
        """
        try:
            input_path = self.raw_html_dir / input_filename
            output_path = settings.get_output_path(input_filename)
            
            # Read HTML file
            with open(input_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Parse HTML to JSON
            result = self.parse_html_to_json(html_content)
            
            # Write to JSON file
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(result, file, ensure_ascii=False, indent=2)
            
            return result
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {input_path}")
        except Exception as e:
            raise Exception(f"Error processing {input_filename}: {str(e)}")

    def process_all_files(self) -> dict:
        """
        Process all HTML files in the raw_html directory.
        
        Returns:
            dict: Dictionary mapping filenames to their parsed data
        """
        results = {}
        html_files = settings.get_html_files()
        
        for html_file in html_files:
            try:
                results[html_file.name] = self.process_file(html_file.name)
            except Exception as e:
                print(f"Error processing {html_file.name}: {str(e)}")
                
        return results
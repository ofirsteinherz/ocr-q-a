from pathlib import Path
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
import pandas as pd

from ocr_project.config.settings import settings

class CompareService:
    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger('CompareService')

        # Field definitions for specialized handling
        self.date_fields = {
            'תאריך מילוי הטופס', 'תאריך קבלת הטופס בקופה', 
            'תאריך הפגיעה', 'תאריך לידה', 'בתאריך'
        }
        self.text_fields = {
            'נסיבות הפגיעה', 'תיאור התאונה', 'כתובת מקום התאונה',
            'האיבר שנפגע', 'שם המבקש'
        }
        self.numeric_fields = {
            'ת.ז', 'טלפון קווי', 'טלפון נייד', 'מיקוד',
            'אבחנה רפואית 1', 'אבחנה רפואית 2'
        }
        self.boolean_fields = {
            'מין/זכר', 'מין/נקבה',
            'מקום התאונה/מפעל', 'מקום התאונה/ת. דרכים בעבודה',
            'מקום התאונה/ת. דרכים בדרך לעבודה/מהעבודה',
            'מקום התאונה/תאונה בדרך לא רכב', 'מקום התאונה/אחר',
            'סטטוס חברות בקופת חולים/הנפגע חבר בקופת חולים',
            'סטטוס חברות בקופת חולים/הנפגע אינו חבר בקופת חולים',
            'קופת חולים/כללית', 'קופת חולים/מאוחדת',
            'קופת חולים/מכבי', 'קופת חולים/לאומית'
        }

    def _setup_logging(self):
        """Configure logging"""
        settings.LOGS_DIR.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(settings.LOGS_DIR / 'compare_service.log'),
                logging.StreamHandler()
            ]
        )

    def _load_data(self) -> pd.DataFrame:
        """Load and filter master data for available files"""
        # Get available files
        available_files = [f.stem.replace('_analysis', '') + '.pdf' 
                         for f in settings.ANALYZED_FORMS_DIR.glob('*_analysis.json')]
        
        # Load and filter master data
        df = pd.read_csv(settings.MASTER_DATA_CSV)
        df = df[df['filename'].isin(available_files)]
        
        self.logger.info(f"Loaded {len(df)} rows for {len(available_files)} files")
        return df

    def _load_json(self, filename: str) -> Dict:
        """Load and parse JSON file"""
        try:
            json_path = settings.ANALYZED_FORMS_DIR / f"{Path(filename).stem}_analysis.json"
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Handle escaped JSON if needed
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1].replace('\\n', '\n').replace('\\"', '"')
                return json.loads(content)
        except Exception as e:
            self.logger.error(f"Error loading JSON {filename}: {str(e)}")
            raise

    def _extract_value(self, data: Dict, section: str, field: str) -> Optional[str]:
        """Extract value from JSON using section and field path"""
        try:
            section_data = data.get(section, {})
            if not section_data or 'fields' not in section_data:
                return None

            # Handle regular and sub-fields
            field_parts = field.split('/')
            main_field = field_parts[0]

            # Find field in section
            for f in section_data['fields']:
                if f['label'] == main_field:
                    # Simple field
                    if len(field_parts) == 1:
                        return str(f['value']) if f['value'] is not None else None
                    
                    # Sub-field
                    if len(field_parts) == 2 and 'sub_fields' in f:
                        sub_name = field_parts[1]
                        for sub in f['sub_fields']:
                            if sub['label'] == sub_name:
                                return str(sub['value']) if sub['value'] is not None else None
            return None
        except Exception as e:
            self.logger.error(f"Error extracting {section}/{field}: {str(e)}")
            return None

    def _normalize_value(self, value: Optional[str]) -> str:
        """Normalize extracted value for comparison"""
        if value is None:
            return ""
        
        # Convert to string and normalize
        value = str(value).strip()
        
        # Handle boolean values
        if value.lower() == 'true':
            return 'V'
        if value.lower() == 'false':
            return ''
        
        # Special handling for numeric values
        if re.match(r'^[\d\s]+$', value):
            return re.sub(r'\s+', '', value)
        
        # Remove spaces, dots, and slashes for general text
        return re.sub(r'[\s./]+', '', value)

    def _normalize_expected_value(self, value: str, field: str) -> str:
        """Normalize expected value from CSV based on field type"""
        if not value:
            return ""

        # Handle boolean fields
        if field in self.boolean_fields:
            return 'V' if value == 'V' else ''

        # Handle numeric fields (ID, phone, medical codes)
        if field in self.numeric_fields or re.match(r'^[\d\s]+$', value):
            return re.sub(r'\s+', '', value)

        # Handle date fields
        if any(date_field in field for date_field in self.date_fields):
            return re.sub(r'[\s./]+', '', value)

        # Handle text fields
        if any(text_field in field for text_field in self.text_fields):
            return re.sub(r'\s+', '', value.strip())

        # Default normalization
        return re.sub(r'[\s./]+', '', value)

    def _compare_values(self, row: pd.Series) -> bool:
        """Compare expected and extracted values with smart matching"""
        normalized_expected = self._normalize_expected_value(row['expected_value'], row['field'])
        normalized_extracted = self._normalize_value(row['extracted_value'])

        # Handle medical diagnosis fields
        if 'אבחנה רפואית' in row['field']:
            if normalized_expected in normalized_extracted or normalized_extracted in normalized_expected:
                return True

        # Handle boolean fields
        if row['field'] in self.boolean_fields:
            return normalized_expected == normalized_extracted or (
                not normalized_expected and not normalized_extracted
            )

        return normalized_expected == normalized_extracted

    def compare_data(self) -> pd.DataFrame:
        """Compare master data with analyzed forms"""
        df = self._load_data()
        results = []
        json_cache = {}

        # Process each file
        for filename, group in df.groupby('filename'):
            # Load JSON once per file
            if filename not in json_cache:
                try:
                    json_cache[filename] = self._load_json(filename)
                except Exception as e:
                    self.logger.error(f"Error loading {filename}: {str(e)}")
                    continue

            json_data = json_cache[filename]

            # Process each field
            for _, row in group.iterrows():
                section, field, expected = row['section|field|value'].split('|')
                
                # Get and normalize values
                extracted = self._extract_value(json_data, section, field)
                norm_expected = self._normalize_expected_value(expected, field)
                norm_extracted = self._normalize_value(extracted)
                
                results.append({
                    'filename': filename,
                    'section': section,
                    'field': field,
                    'expected_value': expected,
                    'extracted_value': extracted,
                    'normalized_expected': norm_expected,
                    'normalized_extracted': norm_extracted,
                    'matches': self._compare_values(pd.Series({
                        'field': field,
                        'expected_value': expected,
                        'extracted_value': extracted
                    }))
                })

        return pd.DataFrame(results)

    def generate_report(self) -> Dict:
        """Generate comparison report"""
        df = self.compare_data()
        
        # Calculate section statistics
        section_stats = df.groupby('section').agg({
            'matches': ['count', 'sum']
        })
        section_stats.columns = ['total', 'matched']
        section_stats['match_rate'] = (section_stats['matched'] / section_stats['total'] * 100)
        
        # Calculate file statistics
        file_stats = df.groupby('filename').agg({
            'matches': ['count', 'sum']
        })
        file_stats.columns = ['total', 'matched']
        file_stats['match_rate'] = (file_stats['matched'] / file_stats['total'] * 100)
        
        # Compile stats
        stats = {
            'total_files': len(df['filename'].unique()),
            'total_fields': len(df),
            'matched_fields': int(df['matches'].sum()),
            'overall_match_rate': (df['matches'].sum() / len(df) * 100),
            'section_stats': section_stats.to_dict('index'),
            'file_stats': file_stats.to_dict('index')
        }
        
        return stats

    def save_results(self, output_path: Optional[Path] = None):
        """Save comparison results to Excel"""
        df = self.compare_data()
        report = self.generate_report()
        
        output_path = output_path or settings.OUTPUT_DIR / "comparison_results.xlsx"
        
        with pd.ExcelWriter(output_path) as writer:
            # Main results
            df.to_excel(writer, sheet_name='Detailed Results', index=False)
            
            # Section statistics
            section_stats = pd.DataFrame.from_dict(report['section_stats'], orient='index')
            section_stats.to_excel(writer, sheet_name='Section Statistics')
            
            # File statistics
            file_stats = pd.DataFrame.from_dict(report['file_stats'], orient='index')
            file_stats.to_excel(writer, sheet_name='File Statistics')
        
        self.logger.info(f"Results saved to: {output_path}")


def main():
    """Main function to run comparison"""
    service = CompareService()
    try:
        # Generate and save results
        service.save_results()
        
        # Generate and print report
        report = service.generate_report()
        
        print("\n=== Comparison Report ===")
        print(f"Total files processed: {report['total_files']}")
        print(f"Total fields processed: {report['total_fields']}")
        print(f"Fields matched: {report['matched_fields']}")
        print(f"Overall match rate: {report['overall_match_rate']:.2f}%\n")
        
        print("Section Statistics:")
        for section, stats in report['section_stats'].items():
            print(f"\n{section}:")
            print(f"  Total fields: {stats['total']}")
            print(f"  Matched fields: {stats['matched']}")
            print(f"  Match rate: {stats['match_rate']:.2f}%")
            
        print("\nFile Statistics:")
        for filename, stats in report['file_stats'].items():
            print(f"\n{filename}:")
            print(f"  Total fields: {stats['total']}")
            print(f"  Matched fields: {stats['matched']}")
            print(f"  Match rate: {stats['match_rate']:.2f}%")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
    settings.clean_pycache()

# === Comparison Report ===
# Total files processed: 4
# Total fields processed: 152
# Fields matched: 117
# Overall match rate: 76.97%

# Section Statistics:

# header:
#   Total fields: 12
#   Matched fields: 5
#   Match rate: 41.67%

# section1:
#   Total fields: 4
#   Matched fields: 2
#   Match rate: 50.00%

# section2:
#   Total fields: 56
#   Matched fields: 46
#   Match rate: 82.14%

# section3:
#   Total fields: 40
#   Matched fields: 30
#   Match rate: 75.00%

# section4:
#   Total fields: 8
#   Matched fields: 8
#   Match rate: 100.00%

# section5:
#   Total fields: 32
#   Matched fields: 26
#   Match rate: 81.25%

# File Statistics:

# form_1.pdf:
#   Total fields: 38
#   Matched fields: 32
#   Match rate: 84.21%

# form_2.pdf:
#   Total fields: 38
#   Matched fields: 28
#   Match rate: 73.68%

# form_3.pdf:
#   Total fields: 38
#   Matched fields: 28
#   Match rate: 73.68%

# form_4.pdf:
#   Total fields: 38
#   Matched fields: 29
#   Match rate: 76.32%
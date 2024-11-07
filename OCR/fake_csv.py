import random
from datetime import datetime, timedelta
import csv
from typing import List, Dict, Tuple
import faker

class FakeFormDataGenerator:
    def __init__(self):
        self.fake = faker.Faker(['he_IL'])  # Hebrew locale

    def generate_number(self, length: int) -> str:
        """Generate number without spaces between digits"""
        digits = [str(random.randint(0, 9)) for _ in range(length)]
        return " ".join(digits)
        
    def generate_spaced_number(self, length: int) -> str:
        """Generate number with spaces between digits"""
        digits = [str(random.randint(0, 9)) for _ in range(length)]
        return "  ".join(digits)
    
    def generate_date(self, start_year: int = 2023) -> str:
        """Generate a random date in DD.MM.YYYY format"""
        start_date = datetime(start_year, 1, 1)
        days = random.randint(0, 365)
        random_date = start_date + timedelta(days=days)
        return random_date.strftime("%d.%m.%Y")
    
    def generate_time(self) -> str:
        """Generate a random time in HH:MM format"""
        hour = random.randint(8, 20)  # Business hours
        minute = random.randint(0, 59)
        return f"{hour:02d}:{minute:02d}"

    def generate_exclusive_choices(self, options: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Generate mutually exclusive choices where only one option is selected"""
        selected_index = random.randrange(len(options))
        return [(field, "V" if i == selected_index else "") 
                for i, (field, _) in enumerate(options)]
    
    def generate_injury_sentence(self):
        # Possible variations for actions and circumstances
        actions = ["החלקה", "נפילה", "מעידה", "איבוד שיווי משקל"]
        locations = ["רצפה רטובה", "מדרגה חלקלקה", "שביל רטוב", "משטח חלק"]
        circumstances = ["במהלך העבודה", "בעת ביצוע מטלה", "בעת תפקיד"]

        # Build the sentence with random choices
        action = random.choice(actions)
        location = random.choice(locations)
        circumstance = random.choice(circumstances)

        return f"{action} על {location} {circumstance}."

    def generate_fake_data(self) -> List[Dict[str, str]]:
        # Define groups of mutually exclusive choices
        gender_fields = [
            ("section2|מין/זכר", ""),
            ("section2|מין/נקבה", "")
        ]

        accident_location_fields = [
            ("section3|מקום התאונה/מפעל", ""),
            ("section3|מקום התאונה/ת. דרכים בעבודה", ""),
            ("section3|מקום התאונה/ת. דרכים בדרך לעבודה/מהעבודה", ""),
            ("section3|מקום התאונה/תאונה בדרך לא רכב", ""),
            ("section3|מקום התאונה/אחר", "")
        ]

        member_status_fields = [
            ("section5|סטטוס חברות בקופת חולים/הנפגע חבר בקופת חולים", ""),
            ("section5|סטטוס חברות בקופת חולים/הנפגע אינו חבר בקופת חולים", "")
        ]

        hmo_fields = [
            ("section5|קופת חולים/כללית", ""),
            ("section5|קופת חולים/מאוחדת", ""),
            ("section5|קופת חולים/מכבי", ""),
            ("section5|קופת חולים/לאומית", "")
        ]

        # Generate selections for each group
        gender_choices = self.generate_exclusive_choices(gender_fields)
        accident_choices = self.generate_exclusive_choices(accident_location_fields)
        member_choices = self.generate_exclusive_choices(member_status_fields)
        hmo_choices = self.generate_exclusive_choices(hmo_fields)

        # Combine all data
        data = [
            # Headers
            ("header|אל קופ״ח/בי״ח", self.fake.city()),
            ("header|תאריך מילוי הטופס", self.generate_spaced_number(8)),
            ("header|תאריך קבלת הטופס בקופה", self.generate_spaced_number(8)),
            
            # Section 1
            ("section1|תאריך הפגיעה", self.generate_spaced_number(8)),
            
            # Section 2 - Personal Info
            ("section2|שם משפחה", self.fake.last_name()),
            ("section2|שם פרטי", self.fake.first_name()),
            ("section2|ת.ז", self.generate_spaced_number(10)),
            ("section2|תאריך לידה", self.generate_number(8)),
            ("section2|רחוב", self.fake.street_name()),
            ("section2|מס' בית", str(random.randint(1, 150))),
            ("section2|כניסה", str(random.randint(1, 4))),
            ("section2|דירה", str(random.randint(1, 40))),
            ("section2|יישוב", self.fake.city()),
            ("section2|מיקוד", str(random.randint(100000, 999999))),
            ("section2|טלפון קווי", self.generate_spaced_number(10)),
            ("section2|טלפון נייד", self.generate_spaced_number(10)),
            
            # Section 3 - Accident Details
            ("section3|בתאריך", self.generate_date()),
            ("section3|בשעה", self.generate_time()),
            ("section3|כאשר עבדתי ב", random.choice(['מלצרות', 'מכירות', 'משרד', 'מחסן', 'נהיגה'])),
            ("section3|כתובת מקום התאונה", f"{self.fake.street_name()} {random.randint(1,100)}, {self.fake.city()}"),
            ("section3|נסיבות הפגיעה / תיאור התאונה", self.generate_injury_sentence()),
            ("section3|האיבר שנפגע", random.choice(['יד ימין', 'יד שמאל', 'רגל ימין', 'רגל שמאל', 'גב', 'ראש'])),
            
            # Section 4
            ("section4|שם המבקש", f"{self.fake.first_name()} {self.fake.last_name()}"),
            ("section4|חתימה", random.choice(['signed', ''])),
            
            # Section 5 - Medical Details
            ("section5|אבחנה רפואית 1", self.generate_spaced_number(4)),
            ("section5|אבחנה רפואית 2", self.generate_spaced_number(4))
        ]

        # Add the mutually exclusive choices
        data.extend(gender_choices)
        data.extend(accident_choices)
        data.extend(member_choices)
        data.extend(hmo_choices)

        return data

    def save_to_csv(self, filename: str):
        data = self.generate_fake_data()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='|')
            writer.writerow(['section', 'field', 'value'])  # Header
            for field, value in data:
                section, field_name = field.split('|')
                writer.writerow([section, field_name, value])

# Example usage:
if __name__ == "__main__":
    generator = FakeFormDataGenerator()
    generator.save_to_csv('files/fake_form_data.csv')
    print("Fake CSV file has been generated successfully!")
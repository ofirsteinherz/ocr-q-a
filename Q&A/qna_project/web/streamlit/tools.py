from functools import wraps
from typing import Callable, Dict, Any
import json
from pathlib import Path
import sys
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tool_calls.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('tools')

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from qna_project.services.search_healthcare import CustomerService
from qna_project.config.settings import settings

# Initialize service
service = CustomerService(settings)

# Define TOOL_REGISTRY at the module level
TOOL_REGISTRY = {}

def log_tool_call(func):
    """Decorator to log tool calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Tool Call - {timestamp}")
        logger.info(f"Function: {func.__name__}")
        logger.info(f"Arguments: {kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

def register_tool(name: str, description: str, parameters: Dict[str, Any]):
    """Decorator to register a function as a tool"""
    global TOOL_REGISTRY
    def decorator(func: Callable):
        @wraps(func)
        @log_tool_call
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        TOOL_REGISTRY[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }
        return wrapper
    return decorator

# Initialize user data
user_data = {}

@register_tool(
    name="update_user_data",
    description="Update user data fields with the provided information.",
    parameters={
        "type": "object",
        "properties": {
            "updates": {
                "type": "object",
                "description": "Key-value pairs for user data to update",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "id_number": {"type": "string"},
                    "gender": {"type": "string"},
                    "age": {"type": "string"},
                    "hmo_number": {"type": "string"},
                    "hmo_name": {"type": "string"},
                    "insurance_plan": {"type": "string"}
                }
            }
        },
        "required": ["updates"]
    }
)
def update_user_data(updates: Dict[str, str]) -> str:
    global user_data
    updated_fields = {}
    
    for field, value in updates.items():
        user_data[field] = value
        updated_fields[field] = value

    response = {
        "updated_fields": updated_fields,
        "current_data": user_data
    }
    return json.dumps(response)

@register_tool(
    name="get_healthcare_services",
    description="Get available healthcare services based on HMO and insurance plan",
    parameters={
        "type": "object",
        "properties": {
            "hmo_name": {
                "type": "string",
                "description": "Name of the HMO provider (maccabi/meuhedet/clalit)",
                "enum": ["maccabi", "meuhedet", "clalit"]
            },
            "insurance_plan": {
                "type": "string",
                "description": "Insurance plan level (gold/silver/bronze)",
                "enum": ["gold", "silver", "bronze"]
            }
        },
        "required": ["hmo_name", "insurance_plan"]
    }
)
def get_healthcare_services(hmo_name: str, insurance_plan: str) -> str:
    try:
        # Convert parameters to lowercase
        hmo_name = hmo_name.lower()
        insurance_plan = insurance_plan.lower()

        # Get services from the database
        services = service.get_all_provider_services(hmo_name, insurance_plan)
        
        if not services:
            return json.dumps({
                "status": "error",
                "message": f"No services found for {hmo_name} {insurance_plan}"
            })

        return json.dumps({
            "status": "success",
            "hmo": hmo_name,
            "plan": insurance_plan,
            "services": services
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in get_healthcare_services: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

# Ensure TOOL_REGISTRY is populated before export
if "update_user_data" not in TOOL_REGISTRY or "get_healthcare_services" not in TOOL_REGISTRY:
    raise RuntimeError("Tools were not properly registered")

# Function to get the registry
def get_registry():
    return TOOL_REGISTRY
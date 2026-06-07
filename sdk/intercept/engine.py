# sdk/intercept/engine.py
import os
import json
from pydantic import ValidationError, create_model
from typing import Any
from sdk.intercept.multi_provider import generate_content_with_byok

def generate_dynamic_pydantic_model(schema_name: str, schema_json: dict) -> Any:
    """
    Dynamically compiles a Pydantic BaseModel.
    Upgraded to support both simple flat dictionaries and nested JSON Schemas.
    """
    fields = {}
    
    # 1. CRITICAL FIX: Detect if the user pasted a standard JSON Schema containing "properties"
    properties = schema_json.get("properties", schema_json)
    
    for field_name, field_val in properties.items():
        # If the value is a nested dictionary (e.g., {"type": "string"}), extract the type
        if isinstance(field_val, dict):
            field_type_string = str(field_val.get("type", "any"))
        else:
            # If it's a flat sandbox format (e.g., "string")
            field_type_string = str(field_val)
            
        type_lower = field_type_string.lower()
        
        if type_lower == "string":
            fields[field_name] = (str, ...)
        elif type_lower in ["float", "number"]:
            fields[field_name] = (float, ...)
        elif type_lower == "integer":
            fields[field_name] = (int, ...)
        elif type_lower == "boolean":
            fields[field_name] = (bool, ...)
        elif type_lower == "array":
            fields[field_name] = (list, ...)
        elif type_lower == "object":
            fields[field_name] = (dict, ...)
        else:
            fields[field_name] = (Any, ...)  
            
    return create_model(schema_name, **fields)


def run_contract_test(
    system_prompt: str, 
    user_input: str, 
    schema_name: str, 
    schema_json: dict,
    llm_provider: str,
    llm_api_key: str
) -> dict:
    """
    Executes contract validation using a dynamically compiled Pydantic model.
    """
    raw_output = None
    try:
        DynamicModel = generate_dynamic_pydantic_model(schema_name, schema_json)
        
        structural_instruction = (
            f"{system_prompt}\n"
            f"CRITICAL: Your response must be a single, flat JSON object matching this schema blueprint:\n"
            f"{json.dumps(schema_json)}\n"
            "Do not include markdown blocks, backticks, or wrapping formatting outside the raw JSON payload."
        )

        raw_output = generate_content_with_byok(
            provider=llm_provider,
            api_key=llm_api_key,
            system_instruction=structural_instruction,
            user_prompt=user_input,
            json_schema=schema_json
        )

        cleaned_output = raw_output.strip()
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3]
        cleaned_output = cleaned_output.strip()

        validated_instance = DynamicModel.model_validate_json(cleaned_output)
            
        return {
            "status": "passed",
            "model_output": validated_instance.model_dump(),
            "error": None  # <-- FIXED KEY NAME
        }
        
    except ValidationError as e:
        # 2. CRITICAL FIX: Convert Pydantic error list to a readable string and fix the dictionary key
        return {
            "status": "failed",
            "model_output": raw_output if raw_output else "Empty response string",
            "error": str(e)  # <-- FIXED KEY NAME (was 'errors')
        }
    except Exception as e:
        # Runtime crashes or parsing failures handled cleanly
        return {
            "status": "error",
            "model_output": raw_output if raw_output else "Pipeline crashed before completion",
            "error": f"Engine Runtime Exception: {str(e)}" # <-- FIXED KEY NAME
        }
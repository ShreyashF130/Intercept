# sdk/intercept/engine.py
import os
import json
from pydantic import ValidationError, create_model
from typing import Any
from sdk.intercept.multi_provider import generate_content_with_byok

def generate_dynamic_pydantic_model(schema_name: str, schema_json: dict) -> Any:
    """
    Takes a raw JSON dictionary mapping field names to Python types (represented as strings)
    and dynamically compiles a Pydantic BaseModel in memory.
    """
    fields = {}
    for field_name, field_type_string in schema_json.items():
        if field_type_string.lower() == "string":
            fields[field_name] = (str, ...)
        elif field_type_string.lower() == "float":
            fields[field_name] = (float, ...)
        elif field_type_string.lower() == "integer":
            fields[field_name] = (int, ...)
        elif field_type_string.lower() == "boolean":
            fields[field_name] = (bool, ...)
        else:
            fields[field_name] = (Any, ...)  # Fallback for complex types
            
    # Dynamic class generation via Pydantic
    return create_model(schema_name, **fields)


def run_contract_test(
    system_prompt: str, 
    user_input: str, 
    schema_name: str, 
    schema_json: dict,
    llm_provider: str,  # <-- NEW: Dynamic Provider (gemini, openai, anthropic)
    llm_api_key: str    # <-- NEW: User-supplied API Key from the Action
) -> dict:
    """
    Executes contract validation using a dynamically compiled Pydantic model
    agnostic of the underlying LLM infrastructure.
    """
    raw_output = None
    try:
        # 1. Build the target structural contract in-memory
        DynamicModel = generate_dynamic_pydantic_model(schema_name, schema_json)
        
        # 2. Instruct the model to conform strictly to the expected key structure
        structural_instruction = (
            f"{system_prompt}\n"
            f"CRITICAL: Your response must be a single, flat JSON object matching this schema blueprint:\n"
            f"{json.dumps(schema_json)}\n"
            "Do not include markdown blocks, backticks, or wrapping formatting outside the raw JSON payload."
        )

        # 3. Route the execution to the requested engine provider using their key
        raw_output = generate_content_with_byok(
            provider=llm_provider,
            api_key=llm_api_key,
            system_instruction=structural_instruction,
            user_prompt=user_input,
            json_schema=schema_json
        )

        # Clean common model outputs if they wrapped it in markdown code blocks anyway
        cleaned_output = raw_output.strip()
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3]
        cleaned_output = cleaned_output.strip()

        # 4. Enforce validation on our gateway using the compiled Pydantic rules
        validated_instance = DynamicModel.model_validate_json(cleaned_output)
            
        return {
            "status": "passed",
            "model_output": validated_instance.model_dump(),
            "errors": None
        }
        
    except ValidationError as e:
        # The LLM generated text but it violated the developer's types
        return {
            "status": "failed",
            "model_output": raw_output if raw_output else "Empty response string",
            "errors": e.errors()
        }
    except Exception as e:
        # Runtime crashes or invalid API keys handled cleanly
        return {
            "status": "error",
            "model_output": raw_output if raw_output else "Pipeline crashed before completion",
            "errors": f"Engine Runtime Exception: {str(e)}"
        }
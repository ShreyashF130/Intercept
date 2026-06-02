import ast
import json
import sys

class PydanticExtractor(ast.NodeVisitor):
    def __init__(self, target_class_name: str):
        self.target_class_name = target_class_name
        self.schema_definition = {}
        self.found = False

    def visit_ClassDef(self, node):
        # Look for the specific Pydantic class name specified by the developer
        if node.name == self.target_class_name:
            self.found = True
            for item in node.body:
                # Identify variable annotations (e.g., username: str)
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field_name = item.target.id
                    
                    # Resolve simple types (str, int, float, bool)
                    if isinstance(item.annotation, ast.Name):
                        field_type = item.annotation.id
                    else:
                        field_type = "string"  # Fallback for complex types for now
                        
                    # Map standard Python types to our engine's primitive expectations
                    type_mapping = {
                        "str": "string",
                        "int": "integer",
                        "float": "float",
                        "bool": "boolean"
                    }
                    
                    self.schema_definition[field_name] = type_mapping.get(field_type, "string")
        self.generic_visit(node)

def extract_schema_from_py_file(file_path: str, class_name: str) -> dict:
    """
    Reads a raw Python file, parses its code structure, and returns a 
    clean dictionary mapping of a Pydantic model's attributes.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        tree = ast.parse(source_code)
        extractor = PydanticExtractor(class_name)
        extractor.visit(tree)
        
        if not extractor.found:
            print(f"❌ ERROR: Class '{class_name}' not found in file '{file_path}'.")
            return {}
            
        return extractor.schema_definition
    except Exception as e:
        print(f"❌ ERROR: Failed to parse Python file syntax: {str(e)}")
        return {}
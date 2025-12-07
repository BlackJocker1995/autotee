import re
from typing import List, Dict, Any
from loguru import logger
from tree_sitter import Node

from static.base_code import ProgramCode

BASIC_PYTHON_TYPES = {"int", "float", "bool", "str", "list", "dict", "tuple", "set",
                      "None", # Python's NoneType
                      # Common built-in types that might be used as arguments
                      "bytes", "bytearray", "memoryview", "range",
                      # Basic array-like structures (though Python lists/tuples are more common)
                      # No direct equivalent of Java's primitive arrays in type hints, usually list[int] etc.
                      }

class PythonCode(ProgramCode):
    def _is_basic_python_type(self, type_node: Node, code: str) -> bool:
        type_text = self._node_text(type_node, code).strip()
        # Handle type hints like List[str], Dict[str, int]
        if "[" in type_text and "]" in type_text:
            # For now, we'll consider simple generic types with basic inner types as basic
            # This is a simplification and might need more robust parsing for complex generics
            main_type = type_text.split("[")[0].strip()
            inner_type_match = re.search(r'\[([\w, ]+)\]', type_text)
            if inner_type_match:
                inner_types = [t.strip() for t in inner_type_match.group(1).split(",")]
                if all(t in BASIC_PYTHON_TYPES for t in inner_types) and main_type in {"list", "dict", "tuple", "set"}:
                    return True
            return False # More complex generics are not basic
        return type_text in BASIC_PYTHON_TYPES

    def _get_function_parameters(self, function_node: Node, code: str) -> List[Node]:
        parameters_node = function_node.child_by_field_name("parameters")
        if parameters_node:
            # Filter for named parameters, excluding special tokens like '(' ')' ','
            return [c for c in parameters_node.children if c.type == "parameter"]
        return []

    def __init__(self) -> None:
        super().__init__()
        self.file_exec = "py"
        self.language_name = "python"

        
    def match_leaf_block(self, file_path: str, code: str, root_node: Node, lang_name: str) -> List[Dict[str, Any]]:
        if lang_name != "python":
            return []

        leaf_functions = []
        function_definitions = []
        function_names = set() # Stores function names

        # First pass: Collect all function definitions and their names
        stack = [root_node]
        while stack:
            node = stack.pop()
            if node.type == "function_definition":
                function_definitions.append(node)
                
                # Extract function name
                name_node = node.child_by_field_name("name")
                function_name = self._node_text(name_node, code) if name_node else ""
                function_names.add(function_name)
            
            for child in reversed(node.children):
                stack.append(child)

        # Second pass: Identify leaf functions
        for function_node in function_definitions:
            name_node = function_node.child_by_field_name("name")
            current_function_name = self._node_text(name_node, code) if name_node else ""

            # Check for a function body
            body_node = function_node.child_by_field_name("body")
            if not body_node:
                logger.debug(f"Skipping {current_function_name} because it has no function body")
                continue

            # Check for basic return type
            return_type_node = function_node.child_by_field_name("return_type")
            # If no return type hint, assume it's basic (e.g., None or implicit None)
            if return_type_node and not self._is_basic_python_type(return_type_node, code):
                logger.debug(f"Skipping {current_function_name} due to non-basic return type")
                continue # Not a leaf function if return type is not basic

            # Check for basic arguments
            is_basic_args = True
            for param_node in self._get_function_parameters(function_node, code):
                # For Python, type hints are in 'type' child of 'parameter' node
                type_node = param_node.child_by_field_name("type")
                if type_node and not self._is_basic_python_type(type_node, code):
                    type_text = self._node_text(type_node, code)
                    logger.info(f"Skipping '{current_function_name}': Non-basic argument type '{type_text}'.")
                    is_basic_args = False
                    break
                    is_basic_args = False
                    break
            
            if not is_basic_args:
                logger.debug(f"Skipping {current_function_name} due to non-basic arguments")
                continue # Not a leaf function if arguments are not basic

            # Check if the function is an instance method (has 'self' as first parameter)
            is_instance_method = False
            params = self._get_function_parameters(function_node, code)
            if params:
                first_param_name_node = params[0].child_by_field_name("name")
                if first_param_name_node and self._node_text(first_param_name_node, code) == "self":
                    is_instance_method = True
            
            if is_instance_method:
                logger.debug(f"Skipping {current_function_name} because it is an instance method")
                continue

            has_function_calls = False
            # Traverse the function body to find call expressions
            body_node = function_node.child_by_field_name("body")
            if body_node:
                body_stack = [body_node]
                while body_stack:
                    current_body_node = body_stack.pop()
                    if current_body_node.type == "call":
                        # Extract called function name
                        function_call_node = current_body_node.child_by_field_name("function")
                        if function_call_node and function_call_node.type == "identifier":
                            called_function_name = self._node_text(function_call_node, code)
                            if called_function_name in function_names and called_function_name != current_function_name:
                                logger.debug(f"Function {current_function_name} calls another user-defined function: {called_function_name}")
                                has_function_calls = True
                                break # Found a call to another user-defined function, not a leaf
                        elif function_call_node and function_call_node.type == "attribute":
                            # Handle method calls like self.method()
                            attribute_node = function_call_node.child_by_field_name("attribute")
                            if attribute_node and attribute_node.type == "identifier":
                                called_function_name = self._node_text(attribute_node, code)
                                if called_function_name in function_names and called_function_name != current_function_name:
                                    has_function_calls = True
                                    break # Found a call to another user-defined method, not a leaf
                    
                    for child in reversed(current_body_node.children):
                        body_stack.append(child)
            
            if not has_function_calls:
                logger.debug(f"Found leaf function: {current_function_name}")
                leaf_functions.append({
                    "code": self._node_text(function_node, code),
                    "file_path": file_path,
                    "start_line": function_node.start_point[0] + 1,
                    "end_line": function_node.end_point[0] + 1
                })
        
        return leaf_functions

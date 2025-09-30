import abc
import os
import re
from pathlib import Path
from abc import abstractmethod
from typing import Optional, Type, List, Set, Dict, Any, Pattern
from functools import lru_cache
import json # Added for saving code blocks

import tree_sitter_java as tsjava
import tree_sitter_python as tscpython

import itertools

from loguru import logger

from tree_sitter import Language, Parser, Node

try:
    # Assuming these are compiled and available in a 'languages' directory
    JAVA_LANGUAGE = tsjava.language()
    PYTHON_LANGUAGE = tscpython.language()
except Exception as e:
    logger.warning(f"Could not load tree-sitter languages: {e}. AST extraction might not work.")
    JAVA_LANGUAGE = None
    PYTHON_LANGUAGE = None

class ProgramCode(object):
    """Base class for program code analysis and processing."""
    
    def __init__(self) -> None:
        """Initialize ProgramCode with default values."""
        self.match_pattern: str = ""
        self.file_exec: str = ""
        self.parser: Optional[Parser] = None
        self.language_module: Any = None

    def _load_language(self, lang_name: str):
        """
        Load tree-sitter language parser if not already loaded.

        Args:
            lang_name (str): Language identifier (e.g., "java", "python")

        Raises:
            ValueError: If language is not supported or language module is not loaded
        """
        if lang_name.lower() == "java":
            lang_obj = JAVA_LANGUAGE
        elif lang_name.lower() == "python":
            lang_obj = PYTHON_LANGUAGE
        else:
            raise ValueError(f"Unsupported language for tree-sitter: {lang_name}")

        if lang_obj is None:
            raise ValueError(f"Tree-sitter language module for {lang_name} is not loaded.")

        if self.parser is None or self.language_module != lang_obj:
            self.parser = Parser(Language(lang_obj))
            self.language_module = lang_obj

    def parse(self, code: str, lang_name: str) -> Node:
        """
        Parse code into AST tree using tree-sitter.

        Args:
            code (str): Source code string
            lang_name (str): Programming language identifier

        Returns:
            tree_sitter.Tree: Root node of the parsed AST
        """
        self._load_language(lang_name)
        if self.parser:
            return self.parser.parse(bytes(code, "utf8")).root_node
        else:
            raise RuntimeError("Tree-sitter parser not initialized.")

    def find_specific_files(self, directory: str) -> List[str]:
        """
        Find all files with the specified extension in the given directory.

        Args:
            directory (str): Path to the directory to search

        Returns:
            List[str]: List of file paths matching the extension
        """
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return []

        return [
            str(path)
            for path in Path(directory).rglob(f"*.{self.file_exec}")
            if path.is_file()
        ]
    
    def ast_code_from_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Extract code blocks from multiple files using the provided pattern matcher.

        Args:
            file_paths (List[str]): List of file paths to process

        Returns:
            List[Dict[str, Any]]: List of dictionaries, each containing 'code', 'file_path', 'start_line', and 'end_line'.
        """
        if not file_paths:
            return []

        return list(itertools.chain.from_iterable(
            self.extract_leaf_node(file_path)
            for file_path in file_paths
        ))
        
    def extract_leaf_node(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract code blocks from a single file using the provided pattern matcher.

        Args:
            file_path (str): Path to the file to process

        Returns:
            List[Dict[str, Any]]: List of dictionaries, each containing 'code', 'file_path', 'start_line', and 'end_line'.
        """
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return []

        # Try UTF-8 first, fallback to ISO-8859-1 if needed
        encodings = ['utf-8', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    texts = file.read()
                    lang_name = self.file_exec.lower()
                    root_node = self.parse(texts, lang_name)
                    match_result = self.match_leaf_block(file_path, texts, root_node, lang_name)
                    return match_result if match_result is not None else []
            except Exception as e:
                logger.warning(f"Failed to read or parse file {file_path} with encoding {encoding}: {e}")
        return []
    
    @abstractmethod
    def match_leaf_block(self, file_path: str, code: str, root_node: Any, lang_name: str) -> List[Dict[str, Any]]:
        """
        Match leaf blocks in the given code.
        A leaf block is a function/method that doesn't call other functions/methods.

        Args:
            file_path (str): The path to the file being analyzed.
            code (str): The code to analyze
            root_node (Any): The root node of the AST.
            lang_name (str): The name of the language.

        Returns:
            List[Dict[str, Any]]: List of dictionaries, each containing 'code', 'file_path', 'start_line', and 'end_line'.
        """
    
    def _node_text(self, node: Node, source_code: str) -> str:
        """Helper to get the text of a node."""
        return source_code[node.start_byte:node.end_byte]

    def list_directories(self, dataset_path: str) -> List[str]:
        """
        List all subdirectories within the given dataset path.

        Args:
            dataset_path (str): The path to the dataset.

        Returns:
            List[str]: A list of paths to subdirectories.
        """
        if not os.path.isdir(dataset_path):
            logger.error(f"Dataset path is not a directory or does not exist: {dataset_path}")
            return []
        
        # List all immediate subdirectories
        subdirectories = [
            os.path.join(dataset_path, d)
            for d in os.listdir(dataset_path)
            if os.path.isdir(os.path.join(dataset_path, d))
        ]
        return subdirectories

    def save_code_block(self, dir_item: str, code_blocks: List[Dict[str, Any]], ast_file_suffix: str):
        """
        Save the extracted code blocks to a JSON file within the directory.

        Args:
            dir_item (str): The path to the directory where the file will be saved.
            code_blocks (List[Dict[str, Any]]): The list of code blocks (dictionaries) to save.
            ast_file_suffix (str): The suffix for the AST JSON file (e.g., "java_ast", "python_ast").
        """
        output_file = os.path.join(dir_item, f"{ast_file_suffix}.json")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(code_blocks, f, indent=4)
            logger.info(f"Saved {len(code_blocks)} code blocks to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save code blocks to {output_file}: {e}")


BASIC_JAVA_TYPES = {"int", "long", "float", "double", "boolean", "char", "String", "byte",
                    "short", "void", "Integer", "Long", "Float", "Double", "Boolean",
                    "Character", "Byte", "Short"}



class JavaCode(ProgramCode):
    def _is_basic_java_type(self, type_node: Node, code: str) -> bool:
        type_text = self._node_text(type_node, code).strip()
        # Handle array types like byte[]
        if type_text.endswith("[]"):
            # Strip array indicators and check the base type
            base_type = type_text.replace("[]", "").strip()
            return base_type in BASIC_JAVA_TYPES
        # Handle generic types like List<String> - for now, treat as non-basic
        if "<" in type_text or ">" in type_text:
            return False
        return type_text in BASIC_JAVA_TYPES

    def _get_method_parameters(self, method_node: Node, code: str) -> List[Node]:
        parameters_node = method_node.child_by_field_name("parameters")
        if parameters_node:
            return [c for c in parameters_node.children if c.type == "formal_parameter"]
        return []

    def __init__(self) -> None:
        super().__init__()
        self.file_exec = "java"
        
    def match_leaf_block(self, file_path: str, code: str, root_node: Node, lang_name: str) -> List[Dict[str, Any]]:
        if lang_name != "java":
            return []

        leaf_methods = []
        method_declarations = []
        method_signatures = set() # Stores "methodName:paramCount" for overload handling

        # First pass: Collect all method declarations and their signatures
        stack = [root_node]
        while stack:
            node = stack.pop()
            if node.type == "method_declaration":
                method_declarations.append(node)
                
                # Extract method name
                name_node = node.child_by_field_name("name")
                method_name = self._node_text(name_node, code) if name_node else ""

                # Extract parameter count for signature
                parameters_node = node.child_by_field_name("parameters")
                param_count = len([c for c in parameters_node.children if c.type == "formal_parameter"]) if parameters_node else 0
                
                method_signatures.add(f"{method_name}:{param_count}")
            
            for child in reversed(node.children):
                stack.append(child)

        # Second pass: Identify leaf methods
        for method_node in method_declarations:
            name_node = method_node.child_by_field_name("name")
            current_method_name = self._node_text(name_node, code) if name_node else ""
            parameters_node = method_node.child_by_field_name("parameters")
            current_param_count = len([c for c in parameters_node.children if c.type == "formal_parameter"]) if parameters_node else 0
            current_method_signature = f"{current_method_name}:{current_param_count}"

            logger.debug(f"Processing method: {current_method_name}")

            # Check for a method body
            body_node = method_node.child_by_field_name("body")
            if not body_node:
                logger.debug(f"Skipping {current_method_name} because it has no method body")
                continue

            # Corrected definitive check. The issue was a misunderstanding of the Java AST.
            # Annotations are modifiers and appear as direct children of the method node,
            # not within a single 'modifiers' field. This code now correctly reflects that.
            has_annotation = False
            body_node = method_node.child_by_field_name("body")
            body_start_byte = body_node.start_byte if body_node else float('inf')

            # We iterate through all direct children of the method that appear before the body.
            for child in method_node.children:
                if child.start_byte >= body_start_byte:
                    break

                # We perform a deep search within each child to find any nested annotations.
                stack = [child]
                while stack:
                    node = stack.pop()
                    if 'annotation' in node.type:
                        has_annotation = True
                        break
                    # Add children in reverse for a pre-order traversal feel
                    stack.extend(reversed(node.children))
                
                if has_annotation:
                    break

            if has_annotation:
                logger.debug(f"Skipping {current_method_name} because it has an annotation")
                continue



            # Check for basic return type
            return_type_node = method_node.child_by_field_name("type")
            if return_type_node and not self._is_basic_java_type(return_type_node, code):
                logger.debug(f"Skipping {current_method_name} due to non-basic return type")
                continue # Not a leaf method if return type is not basic
            
            # Check for basic arguments
            is_basic_args = True
            for param_node in self._get_method_parameters(method_node, code):
                type_node = param_node.child_by_field_name("type")
                if type_node and not self._is_basic_java_type(type_node, code):
                    is_basic_args = False
                    break
            
            if not is_basic_args:
                logger.debug(f"Skipping {current_method_name} due to non-basic arguments")
                continue # Not a leaf method if arguments are not basic

            # A method must be static to be truly self-contained and not rely on instance state.
            is_static = False
            modifiers_node = None
            for child in method_node.children:
                if child.type == 'modifiers':
                    modifiers_node = child
                    break
            
            if modifiers_node:
                for modifier in modifiers_node.children:
                    if self._node_text(modifier, code) == "static":
                        is_static = True
                        break
            
            if not is_static:
                logger.debug(f"Skipping {current_method_name} because it is not a static method.")
                continue

            has_user_method_calls = False
            if body_node:
                body_stack = [body_node]
                while body_stack:
                    current_body_node = body_stack.pop()
                    if current_body_node.type == "method_invocation":
                        # Extract called method name
                        called_name_node = current_body_node.child_by_field_name("name")
                        called_method_name = self._node_text(called_name_node, code) if called_name_node else ""

                        # Extract called method arguments count
                        arguments_node = current_body_node.child_by_field_name("arguments")
                        called_param_count = len([c for c in arguments_node.children if c.type != "," and c.type != "(" and c.type != ")"]) if arguments_node else 0
                        
                        called_method_signature = f"{called_method_name}:{called_param_count}"

                        if called_method_signature in method_signatures and called_method_signature != current_method_signature:
                            logger.debug(f"Method {current_method_name} calls another user-defined method: {called_method_name}")
                            has_user_method_calls = True
                            break # Found a call to another user-defined method, not a leaf
                    
                    for child in reversed(current_body_node.children):
                        body_stack.append(child)
            
            if not has_user_method_calls:
                logger.debug(f"Found leaf method: {current_method_name}")
                leaf_methods.append({
                    "code": self._node_text(method_node, code),
                    "file_path": file_path,
                    "start_line": method_node.start_point[0] + 1,
                    "end_line": method_node.end_point[0] + 1
                })
        
        return leaf_methods
        
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
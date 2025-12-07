from typing import List, Dict, Any
from loguru import logger
from tree_sitter import Node

from static.base_code import ProgramCode

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
        self.language_name = "java"
        
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
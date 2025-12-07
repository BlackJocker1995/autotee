import abc
import os
import json
from pathlib import Path
from abc import abstractmethod
from typing import Optional, List, Dict, Any
import itertools

from loguru import logger
import tree_sitter_java as tsjava
import tree_sitter_python as tscpython
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
        self.language_name: str = ""
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
                    lang_name = self.language_name.lower()
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

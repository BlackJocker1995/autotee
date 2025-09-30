import os
from loguru import logger
from static.code_match import JavaCode, PythonCode, ProgramCode
from typing import List, Dict, Any

def create_code_analyzer(language: str) -> ProgramCode:
    """
    Factory function to create a Code Analyzer instance based on the language.
    
    Args:
        language (str): The programming language (e.g., "java", "python").
        
    Returns:
        ProgramCode: An instance of the appropriate ProgramCode subclass.
        
    Raises:
        ValueError: If an unsupported language is provided.
    """
    if language.lower() == "java":
        return JavaCode()
    elif language.lower() == "python":
        return PythonCode()
    else:
        raise ValueError(f"Unsupported language: {language}")

def run_processing(project_name: str, language: str, overwrite: bool = False):
    """
    Processes a single project to extract code blocks.
    It initializes a code analyzer, finds specific files, extracts AST code blocks,
    and saves them to a JSON file.
    
    Args:
        project_name (str): The path to the project directory to process.
        language (str): The programming language (e.g., "java", "python").
        overwrite (bool): If True, existing AST files will be overwritten.
    """
    logger.info(f"Starting processing of project: {project_name}")
    
    # Create a code analyzer instance using the factory function
    code_ana = create_code_analyzer(language)
    
    output_dir = os.path.join(project_name, "ana_json")
    if not os.path.exists(output_dir):
        try:
            os.mkdir(output_dir)
        except FileNotFoundError:
            logger.error(f"Error: The parent directory for '{output_dir}' does not exist.")
            logger.error("Please ensure the base project path is correct and accessible.")
            return
    output_file = os.path.join(output_dir, f"{language.lower()}_leaf.json")

    # Skip processing if AST file already exists and overwrite is False
    if not overwrite and os.path.exists(output_file):
        logger.info(f"Skipped processing for {project_name} as AST file already exists and overwrite is False.")
        return

    # Find specific files within the directory
    files = code_ana.find_specific_files(project_name)
    # Extract AST code blocks from the found files
    code_blocks: List[Dict[str, Any]] = code_ana.ast_code_from_files(files)
    logger.info(f"{project_name}, We get {len(code_blocks)} code blocks.")
    # Save the extracted code blocks to a JSON file
    code_ana.save_code_block(output_dir, code_blocks, f"{language.lower()}_leaf")
    
    logger.info(f"Total code blocks processed for {project_name}: {len(code_blocks)}")

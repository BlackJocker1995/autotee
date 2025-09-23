import os
import ray
from loguru import logger
from static.code_match import JavaCode, PythonCode, ProgramCode
from typing import List, Dict, Any

# Default number of threads for Ray, can be adjusted
NUM_THREADS = 6

@ray.remote
def process_directory(language: str, dir_item: str, overwrite: bool):
    """
    Ray remote function to process a single directory.
    It initializes a code analyzer, finds specific files, extracts AST code blocks,
    and saves them to a JSON file.
    
    Args:
        language (str): The programming language (e.g., "java", "python").
        dir_item (str): The path to the directory to process.
        ast_file_suffix (str): The suffix for the AST JSON file (e.g., "java_ast", "python_ast").
        overwrite (bool): If True, existing AST files will be overwritten.
        
    Returns:
        int: The number of code blocks processed in the directory, or None if skipped.
    """
    # Create a code analyzer instance using the factory function
    code_ana = create_code_analyzer(language)
    # Skip processing if AST file already exists and overwrite is False
    if not overwrite and os.path.exists(f"{dir_item}/{language.lower()}_ast.json"):
        return None
    
    # Find specific files within the directory
    files = code_ana.find_specific_files(dir_item)
    # Extract AST code blocks from the found files
    code_blocks: List[Dict[str, Any]] = code_ana.ast_code_from_files(files)
    logger.info(f"{dir_item}, We get {len(code_blocks)} code blocks.")
    # Save the extracted code blocks to a JSON file
    code_ana.save_code_block(dir_item, code_blocks, f"{language.lower()}_ast")
    return len(code_blocks)

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

def split_into_chunks(dirs: list[str]) -> list[list[str]]:
    """
    Split directories into chunks for parallel processing.
    This function divides a list of directories into a specified number of chunks,
    which can then be processed in parallel using Ray.
    """
    chunks = []
    num_chunks = NUM_THREADS
    avg_chunk_size = len(dirs) // num_chunks
    for i in range(num_chunks):
        start_index = i * avg_chunk_size
        end_index = start_index + avg_chunk_size if i < num_chunks - 1 else len(dirs)
        chunks.append(dirs[start_index:end_index])
    return chunks

def run_processing(language: str, dataset_path: str, overwrite: bool = False):
    ast_file_suffix = f"{language.lower()}_ast"
    """
    Initializes Ray and orchestrates the parallel processing of directories.
    It uses a given language to create a code_analyzer_class to process files in each directory,
    extracting code blocks and saving them.
    
    Args:
        language (str): The programming language (e.g., "java", "python").
        dataset_path (str): The path to the dataset containing the directories to process.
        ast_file_suffix (str): The suffix for the AST JSON file (e.g., "java_ast", "python_ast").
        overwrite (bool): If True, existing AST files will be overwritten.
    """
    logger.info(f"Initializing Ray with {NUM_THREADS} threads")
    ray.init(num_cpus=NUM_THREADS, ignore_reinit_error=True)
    
    try:
        # Create a code analyzer instance using the factory function
        code_ana_instance = create_code_analyzer(language)
        
        # List all directories to be processed
        dirs = code_ana_instance.list_directories(dataset_path)

        logger.info(f"Starting processing of {len(dirs)} directories")
        # Create Ray futures for parallel execution of process_directory for each directory
        futures = [process_directory.remote(language, dir_item, overwrite) for dir_item in dirs]
        
        # Wait for all futures to complete and get the results
        results = ray.get(futures)
        logger.info(f"Completed processing all directories")
        
        # Calculate the total number of code blocks processed
        total_blocks = sum(r for r in results if r is not None)
        logger.info(f"Total code blocks processed: {total_blocks}")
    finally:
        # Shutdown Ray
        ray.shutdown()

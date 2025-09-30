import os
from LLM.llmodel import LLMConfig
from task.search_sensitive import query_sensitive_project, OUTPUT_NAME_SUFFIX
from static.projectUtil import read_code_block, save_code_block, short_hash
from loguru import logger

def write_sensitive_code_to_files(project_path: str, language: str, sensitive_code_blocks: list[dict]) -> None:
    """
    Writes sensitive code blocks to individual files in a designated directory.
    Each code block is placed in a subfolder named by its hash, and for Java,
    it's wrapped in a class with a matching filename.
    """
    project_code_files_dir = os.path.join(project_path, "project_code_files")
    os.makedirs(project_code_files_dir, exist_ok=True)
    logger.info(f"Created output directory for sensitive code files: {project_code_files_dir}")

    for i, code_block in enumerate(sensitive_code_blocks):
        code_content = code_block.get("code", "")
        function_name = code_block.get("function_name", f"unknown_func_{i}")
        
        # Generate a hash for the code content to create a unique subdirectory
        code_hash = short_hash(code_content)
        hash_subdir = os.path.join(project_code_files_dir, code_hash)
        os.makedirs(hash_subdir, exist_ok=True)

        if language == "java":
            # Use "SensitiveFun" as the base class name, or derive from function_name if available and not a placeholder
            base_class_name = "SensitiveFun"
            if function_name and not function_name.startswith("unknown_func_"):
                base_class_name = function_name[0].upper() + function_name[1:]
            
            class_name = base_class_name
            output_file_name = f"{class_name}.java"
            output_file_path = os.path.join(hash_subdir, output_file_name)

            # Wrap the function code in a class
            wrapped_code_content = f"""
public class {class_name} {{
    {code_content}
}}
"""
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(wrapped_code_content)
            logger.info(f"Written sensitive Java class to: {output_file_path}")
        else:
            # For other languages, write as-is for now (or implement specific wrapping)
            # The file name will be function_name.language inside the hash subdirectory
            output_file_name = f"{function_name}.{language}"
            output_file_path = os.path.join(hash_subdir, output_file_name)
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(code_content)
            logger.info(f"Written sensitive code block to: {output_file_path}")
    logger.info("Finished writing sensitive code blocks to individual files.")


def run_create_test_workflow(project_path: str, language: str, llm_config: LLMConfig) -> None:
    """
    Orchestrates the workflow for querying sensitive projects, writing code to files,
    and generating test files.
    """
    # Read the sensitive code blocks after query_sensitive_project has run
    output_dir_ana_json = os.path.join(project_path, "ana_json")
    out_name = f"{llm_config.get_description()}{OUTPUT_NAME_SUFFIX}"
    
    try:
        sensitive_code_blocks = read_code_block(output_dir_ana_json, out_name)
        logger.info(f"Read {len(sensitive_code_blocks)} sensitive code blocks for writing to files.")
    except FileNotFoundError:
        logger.warning(f"No sensitive code blocks found at {output_dir_ana_json}/{out_name}.json for writing to files.")
        sensitive_code_blocks = []

    write_sensitive_code_to_files(project_path, language, sensitive_code_blocks)


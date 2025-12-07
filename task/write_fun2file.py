import os
from LLM.llmodel import LLMConfig
from task.search_sensitive import OUTPUT_NAME_SUFFIX
from static.projectUtil import read_code_block
from loguru import logger
from task.java.java_write_fun2file import JavaWriter
from task.python.python_write_fun2file import PythonWriter

def write_sensitive_code_to_files(project_path: str, language: str, sensitive_code_blocks: list[dict]) -> None:
    if language == "java":
        writer = JavaWriter(project_path, sensitive_code_blocks)
    elif language == "python":
        writer = PythonWriter(project_path, sensitive_code_blocks)
    else:
        logger.error(f"Unsupported language for writing sensitive code: {language}")
        return
    
    writer.write_sensitive_code_to_files()


def write_sen2file(project_path: str, language: str, llm_config: LLMConfig) -> None:
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
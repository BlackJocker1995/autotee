import os

from loguru import logger

from LLM.llmodel import LLMConfig
from task.java.java_test_workflow import JavaTestWorkflow


def run_create_test_workflow(
    project_path: str, language: str, llm_config: LLMConfig
) -> None:
    """
    Orchestrates the workflow for generating test files for sensitive code blocks.
    This function delegates the test creation process to a language-specific workflow.
    """
    logger.info(f"Starting the create test workflow for {language}.")

    project_code_files_dir = os.path.join(project_path, "project_code_files")

    if not os.path.exists(project_code_files_dir):
        logger.warning(
            f"Project code files directory not found: {project_code_files_dir}. Exiting test creation workflow."
        )
        return

    code_block_hashes = [
        d
        for d in os.listdir(project_code_files_dir)
        if os.path.isdir(os.path.join(project_code_files_dir, d))
    ]

    if not code_block_hashes:
        logger.info(
            "No code blocks found in project_code_files. Exiting test creation workflow."
        )
        return

    logger.info(f"Found {len(code_block_hashes)} code blocks for test generation.")

    for code_hash in code_block_hashes:
        logger.info(f"Processing code block: {code_hash}")
        workflow = None
        if language.lower() == "java":
            workflow = JavaTestWorkflow(project_path, language, llm_config, code_hash)
        # Add other languages here, e.g., Python
        # elif language.lower() == "python":
        #     # workflow = PythonTestWorkflow(project_path, language, llm_config, code_hash)
        #     pass
        else:
            logger.error(f"Unsupported language for test generation: {language}")
            continue

        if workflow:
            workflow.run()

    logger.info("Finished create test workflow.")

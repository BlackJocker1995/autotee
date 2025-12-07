import os
from loguru import logger
from LLM.llmodel import LLMConfig
from task.java.java_to_rust_transform_workflow import JavaToRustTransformWorkflow

def run_transform_workflow(
    project_path: str, language: str, llm_config: LLMConfig
) -> None:
    logger.info(f"Starting the transform workflow from {language} to rust.")

    project_code_files_dir = os.path.join(project_path, "project_code_files")

    if not os.path.exists(project_code_files_dir):
        logger.warning(
            f"Project code files directory not found: {project_code_files_dir}. Exiting transform workflow."
        )
        return

    code_block_hashes = [
        d for d in os.listdir(project_code_files_dir) if os.path.isdir(os.path.join(project_code_files_dir, d))
    ]

    if not code_block_hashes:
        logger.info(
            "No code blocks found in project_code_files. Exiting transform workflow."
        )
        return

    logger.info(f"Found {len(code_block_hashes)} code blocks for transformation.")

    for code_hash in code_block_hashes:
        logger.info(f"Processing code block: {code_hash}")
        workflow = None
        if language.lower() == "java":
            workflow = JavaToRustTransformWorkflow(project_path, code_hash, llm_config)
        else:
            logger.error(
                f"Unsupported transformation from {language} to rust."
            )
            continue

        if workflow:
            workflow.run()

    logger.info("Finished transform workflow.")
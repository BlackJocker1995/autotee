"""
Main script for executing various project tasks in Java.

This script provides a command-line interface to run different tasks
related to project analysis, testing, and database operations.
"""

import sys
from loguru import logger

from LLM.llmodel import LLMConfig

from task.match_block_common import run_processing
from task.search_sensitive import query_sensitive_project
from task.create_test import run_create_test_workflow


def main():
    """
    Main function to execute project tasks.

    Usage: python main.py <task>
    """
    # cryptomator hashids-java java-opentimestamps JustAuth Zero-Allocation-Hashing
    language = "java"  # Language for the project (hardcoded for Java)
    project_name = "/home/rdhan/data/dataset/test/starlarky"

    # Configuration for each task specifying their parameters
    task_configs = {
        "leaf": {"func": run_processing, "params": {}},
        "sensitive": {"func": query_sensitive_project, "params": {"llm_config": LLMConfig(provider='vllm', model='Qwen3-coder:30b')}},
        "create_test": {"func": run_create_test_workflow, "params": {"llm_config": LLMConfig(provider='vllm', model='Qwen3-coder:30b')}},
    }
    # Check if correct number of arguments provided
    if len(sys.argv) != 2:
        logger.info("Usage: python main.py <task>")
        logger.info(f"Available tasks: {', '.join(task_configs.keys())}")
        return

    task_name = sys.argv[1]  # Get task name from command line argument

    # Get the task configuration
    config = task_configs.get(task_name)
    if config:
        try:
            # Execute the selected task with appropriate parameters
            func = config["func"]
            params = config["params"]

            # Execute function with all parameters
            func(project_name,language, **params)
        finally:
            # Cleanup message - verify shared memory cleanup status
            logger.info("Exiting main: Verify shared memory cleanup status. Any shared memory warnings should be monitored.")
    else:
        # Handle unknown task
        logger.warning(f"Unknown task: {task_name}")
        logger.info(f"Available tasks: {', '.join(task_configs.keys())}")

if __name__ == "__main__":
    """
    Entry point of the script.

    This ensures that main() is only called when the script is executed directly,
    not when it's imported as a module in another script.
    """
    main()
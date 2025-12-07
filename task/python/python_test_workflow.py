import os
import subprocess
from loguru import logger
from task.common.base_test_workflow import BaseTestWorkflow

class PythonTestWorkflow(BaseTestWorkflow):
    """
    Test generation workflow for Python projects.
    """

    def _ensure_virtual_environment(self, project_base_path: str) -> bool:
        """Ensures a virtual environment exists in the specified path, creating it if necessary."""
        venv_path = os.path.join(project_base_path, ".venv")
        if not os.path.exists(venv_path):
            try:
                logger.info(f"Creating virtual environment in {project_base_path}")
                subprocess.run(
                    "uv venv",
                    cwd=project_base_path,
                    capture_output=True,
                    text=True,
                    shell=True,
                    check=True
                )
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create virtual environment in {project_base_path}: {e.stderr}")
                return False
        return True

    
    def _setup_project_structure(self) -> None:
        python_main_dir = os.path.join(self.hash_subdir)
        os.makedirs(python_main_dir, exist_ok=True)

        test_file_name = "test_sensitive_fun.py"
        test_file_path = os.path.join(python_main_dir, test_file_name)

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("")
        logger.info(f"Created empty test file: {test_file_path}")

        self._ensure_virtual_environment('..')
        
        
    def _get_initial_input(self) -> dict:
        test_file_path = os.path.join(self.hash_subdir, "test_sensitive_fun.py")
        code_to_test_path = os.path.join(self.hash_subdir, "sensitive_fun.py")
    

        prompt = f"""You are a professional Python development engineer. Your core task is to write a set of unit tests using pytest for the specified functions in a single file.

        **Target Functions**
        - **Functions Location**: `{self.project_path}/sensitive_fun.py`

        **Project Context**
        - The functions to be tested are located in `{test_file_path}`.
        - Your generated test code must be written to `{test_file_path}`.

        **Code Generation Guidelines**
        1.  **Framework**: You must use `pytest`.
        2.  **Imports**:
            - Import the target functions from the `sensitive_fun` module (e.g., `from sensitive_fun import your_function_name`).
            - Use relative import paths for any other local packages or files.
        3.  **Test Quality**:
            - Ensure the generated code is clear, readable, and includes all necessary `import` statements.
            - Each test case function must start with the `test_` prefix.
            - Use clear and specific `assert` statements to verify results. Do not simply use `assert True`.
            - If the code involves file operations, database interactions, or network requests, use the `unittest.mock` library (e.g., via the `pytest-mock` fixture) to mock these external dependencies.
            - If testing a function that returns a `TextContent` object (from a tool call), assert against the `text` attribute of the result (e.g., `assert result.text == "expected output"`).

        **Coverage Goal**
        Your primary goal is to maximize both line and branch coverage. Generate a diverse set of tests that cover:
        - Normal operating scenarios.
        - Common edge cases (e.g., empty inputs, null values).
        - Potential error conditions.

        **Completion Criteria**
        This task is considered complete only when all the following conditions are met:
        1. All generated unit tests execute successfully without errors.
        2. The generated test file (`test_sensitive_fun.py`) is not empty and contains valid pytest tests.
        3. The process will automatically conclude if three consecutive attempts to generate tests result in no improvement to code coverage.
        """
        return {
            "messages": [
                (
                    "user",
                    prompt,
                )
            ]
        }

import os
from loguru import logger
from task.common.base_test_workflow import BaseTestWorkflow
from utils.maven_utils import get_java_pom_template

class JavaTestWorkflow(BaseTestWorkflow):
    """
    Test generation workflow for Java projects.
    """

    def _setup_project_structure(self) -> None:
        java_main_dir = os.path.join(
            self.hash_subdir, "src", "main", "java", "com", "example", "project"
        )
        java_test_dir = os.path.join(
            self.hash_subdir, "src", "test", "java", "com", "example", "project"
        )

        os.makedirs(java_main_dir, exist_ok=True)
        os.makedirs(java_test_dir, exist_ok=True)

        test_file_name = "SensitiveFunTest.java"
        test_file_path = os.path.join(java_test_dir, test_file_name)

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("")
        logger.info(f"Created empty test file: {test_file_path}")

        pom_content = get_java_pom_template()
        pom_content = pom_content.replace("REPLACE_ME_ARTIFACT_ID", self.code_hash)

        pom_file_path = os.path.join(self.hash_subdir, "pom.xml")
        with open(pom_file_path, "w", encoding="utf-8") as f:
            f.write(pom_content)
        logger.info(f"Created pom.xml for Maven project at: {pom_file_path}")

    def _get_initial_input(self) -> dict:
        test_file_path = os.path.join(
            self.hash_subdir,
            "src",
            "test",
            "java",
            "com",
            "example",
            "project",
            "SensitiveFunTest.java",
        )
        code_to_test_path = os.path.join(
            self.hash_subdir,
            "src",
            "main",
            "java",
            "com",
            "example",
            "project",
            "SensitiveFun.java",
        )

        prompt = f"""You are a professional Java development engineer. Your core task is to write a set of unit tests using JUnit for the specified methods in a single file.

        **Target Methods**
        - **Methods Location**: `{code_to_test_path}`

        **Project Context**
        - The methods to be tested are located in the class within `{code_to_test_path}`.
        - Your generated test code must be written to `{test_file_path}`.
        - The test class should be named `SensitiveFunTest`.

        **Code Generation Guidelines**
        1.  **Framework**: You must use `JUnit 5`.
        2.  **Imports**:
            - Import the target class and its methods.
            - Import necessary JUnit assertions (e.g., `import static org.junit.jupiter.api.Assertions.*;`).
            - All necessary `import` statements must be included.
        3.  **Test Quality**:
            - Each test case must be a public method annotated with `@Test`.
            - Use clear and specific assertion statements to verify results. Per project requirements, you may only use `assertEquals` for checking values and `assertThrows(Exception.class, ...)` for exceptions. Do not use other assertions.
            - If the code involves external dependencies (e.g., file I/O, database, network), use `Mockito` to create mocks.
            - Ensure the generated code is clean, readable, and syntactically correct Java.

        **Coverage Goal**
        Your primary goal is to maximize both line and branch coverage. Generate a diverse set of tests that cover:
        - Normal operating scenarios.
        - Common edge cases (e.g., empty inputs, null values).
        - Potential error conditions that should throw an `Exception`.

        **Completion Criteria**
        This task is considered complete only when all the following conditions are met:
        1. All generated unit tests compile and execute successfully, reporting 'Failures: 0, Errors: 0, Skipped: 0'.
        2. The generated test file (`{os.path.basename(test_file_path)}`) is not empty and contains valid JUnit tests.
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


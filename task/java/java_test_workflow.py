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
        return {
            "messages": [
                (
                    "user",
                    f"""
        Generate a diverse set of test inputs for  {self.language} project located at `{self.hash_subdir}`, aiming to maximize both line and branch coverage.
        Enhance the unit test coverage (line and branch) for the specified code unit.
        Ensure generated tests are syntactically correct, invoke relevant methods with appropriate inputs, and include assertions to validate expected behavior.
        If the added unit tests do not increase coverage, they will not be kept. The generated tests can only be assertEquals and assertThrows, and assertThrows can only be Exception.class

        **Completion Criteria:** You have successfully completed this task only when both of the following conditions are met:
        1. The task concludes after three consecutive attempts show no improvement in line and branch coverage.
        2. Test.java is not empty.
        3. All unit tests execute successfully, reporting 'Failures: 0, Errors: 0, Skipped: 0'

        """,
                )
            ]
        }

import os
from task.common.base_transform_workflow import BaseTransformWorkflow
from LLM.tools.cargo_tool import cargo_new

class JavaToRustTransformWorkflow(BaseTransformWorkflow):
    def __init__(self, project_path, code_hash, llm_config):
        super().__init__(project_path, code_hash, llm_config, "java", "rust")

    def _setup_project(self) -> None:
        cargo_new(self.hash_subdir)

    def _get_source_code(self) -> str | None:
        java_main_file = os.path.join(self.hash_subdir, "src", "main", "java", "com", "example", "project", "SensitiveFun.java")
        try:
            with open(java_main_file) as f:
                return f.read()
        except FileNotFoundError:
            return None

    def _get_initial_input(self, source_code: str) -> dict:
        return {
            "messages": [
                (
                    "user",
f"""
You are an expert polyglot software engineer specializing in high-fidelity, idiomatic code migration. Your mission is to perform a functional-equivalent translation of a specific Java function, ensuring the new implementation passes the same behavioral checks as the original.

**## CONTEXT ##**
*   **Objective:** Translate the function `{source_code}` located in the source file into a functionally equivalent and idiomatic Rust implementation.
*   **Source File Path:** `src/main/java/com/exmaple/project/SensitiveFun.java`
*   **Target File Path:** `rust/src/lib.rs`
    ```

**## Process ##**
1. Translate the {self.source_language} function's logic into a pure Rust function and write into `rust/src/lib.rs`.
2. After every modification to `rust/src/lib.rs`, you must immediately run `cargo check` to validate the code and fix issues. Do not proceed to the next step until `cargo check` passes without errors.
3. Once the core Rust logic is syntactically correct, call `create_template_for_transformation` exactly once. This tool generates the necessary {self.source_language}-to-Rust connection templates, correctly mapping the original function name on the {self.source_language} side to the `snake_case` name on the Rust side.
4. Run `cargo check` again to ensure the newly generated connection code integrates correctly with your implementation. If `cargo check` fails, do not proceed to the next step.
5. Use `execute_unit_test` to run the original {self.source_language} unit tests. They must pass to confirm the translation is functionally correct and the integration is successful. If an error occurs, try to fix it.

**## REQUIREMENTS ##**

1.  **Functional Equivalence:** The Rust code must replicate the exact behavior, logic, and edge cases of the original Java function. The primary measure of success is its ability to pass the provided unit tests' logic.
2.  **Idiomatic Rust Style:** You must adopt standard Rust patterns, including ownership/borrowing, `Result` and `Option` for error handling, iterators, and traits. Avoid direct, literal translations that lead to unidiomatic or unsafe code.
3.  **Code Completeness:** The generated Rust code for `Rust/src/lib.rs` must be a complete, compilable file, including all necessary `use` statements, `struct`/`enum` definitions, `impl` blocks, and the translated function itself.
4. **Cargo.toml**: do not remove 'serde' and 'serde_json' in toml.
5. Rust's MD5 uses `md5::compute`, do not use `extern "C"`

**## DELIVERABLE ##**

Your final output must be a single, complete Rust code block containing the full contents for the `Rust/src/lib.rs` file, followed by a `TOML` code block for the suggested `Cargo.toml` dependencies. Do not include any explanations, conversational text, or markdown formatting outside of these two code blocks.


""",
                )
            ]
        }

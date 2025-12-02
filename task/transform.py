import os
from LLM.llmodel import LLMConfig, LLModel
from LLM.tasks_tool_creater import create_transform_tools
from LLM.tools.cargo_tool import cargo_new
from loguru import logger

from utils.chunk_utils import process_chunk, extract_token_usage # Import extract_token_usage


def get_transform_prompt(language, source_code):
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
1. Translate the `{language}` function's logic into a pure Rust function and write into `rust/src/lib.rs`.
2. After every modification to `rust/src/lib.rs`, you must immediately run `cargo check` to validate the code and fix issues. Do not proceed to the next step until `cargo check` passes without errors.
3. Once the core Rust logic is syntactically correct, call `create_template_for_transformation` exactly once. This tool generates the necessary `{language}`-to-Rust connection templates, correctly mapping the original function name on the `{language}` side to the `snake_case` name on the Rust side.
4. Run `cargo check` again to ensure the newly generated connection code integrates correctly with your implementation. If `cargo check` fails, do not proceed to the next step.
5. Use `execute_unit_test` to run the original `{language}` unit tests. They must pass to confirm the translation is functionally correct and the integration is successful. If an error occurs, try to fix it.

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


def run_transform_workflow(project_path: str, language: str, llm_config: LLMConfig) -> None:
    logger.info("Starting the create test workflow.")

    # Define the directory where individual code files were saved
    project_code_files_dir = os.path.join(project_path, "project_code_files")

    # Iterate through the project_code_files directory to find code blocks
    # Each subdirectory in project_code_files_dir represents a code block identified by its hash

    if not os.path.exists(project_code_files_dir):
        logger.warning(f"Project code files directory not found: {project_code_files_dir}. Exiting test creation workflow.")
        return

    code_block_hashes = [d for d in os.listdir(project_code_files_dir) if os.path.isdir(os.path.join(project_code_files_dir, d))]

    if not code_block_hashes:
        logger.info("No code blocks found in project_code_files. Exiting test creation workflow.")
        return

    logger.info(f"Found {len(code_block_hashes)} code blocks for test generation.")

    for i, code_hash in enumerate(code_block_hashes):
        hash_subdir = os.path.join(project_code_files_dir, code_hash)

        cargo_new(hash_subdir)
        java_main_file = os.path.join(hash_subdir, "src", "main", "java", "com", "example", "project","SensitiveFun.java")
        with open(java_main_file) as f:
            source_code = f.read()

        created_tools = create_transform_tools(
            project_root_path=hash_subdir,
            language=language,
        )

        # Create LLM agent with the tools
        system_prompt = (
            "You are an autonomous Java build-and-test engineer. "
            "You can run tools to build, test, and modify the codebase."
            "Follow the user's constraints strictly and do not attempt to ask the user questions.\n"
            "{agent_scratchpad}"
        )
        llm = LLModel.from_config(llm_config) # Instantiate LLModel
        agent_executor = llm.create_tool_react(created_tools, system_prompt)

        initial_input = get_transform_prompt(language, source_code)

         # Run
        total_all_tokens = 0
        token_usage_steps = 0 # Initialize counter for steps with token usage
        for chunk in agent_executor.stream(initial_input, config={"recursion_limit": 150}):
            current_chunk_tokens = extract_token_usage(chunk)
            total_all_tokens += current_chunk_tokens
            if current_chunk_tokens > 0:
                logger.info(f"Token usage for this step: {current_chunk_tokens}")
                token_usage_steps += 1 # Increment counter if tokens were used

            bool_result, _ = process_chunk(chunk)
            if bool_result:
                break

        logger.info(f"Total tokens for the workflow: {total_all_tokens}")
        if token_usage_steps > 0:
            average_tokens = total_all_tokens / token_usage_steps
            logger.info(f"Average tokens per step: {average_tokens:.2f}")
        else:
            logger.info("No token usage recorded for any step.")
    logger.info("Finished abstract test creation workflow.")

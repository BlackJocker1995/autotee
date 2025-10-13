import os
from LLM.llmodel import LLMConfig, LLModel
from LLM.tasks_tool_creater import create_test_gen_tools, create_transform_tools
from LLM.tools.cargo_tool import cargo_new
from static.projectUtil import read_code_block, save_code_block, short_hash
from loguru import logger

from utils.chunk_utils import process_chunk
from static.get_env import return_env # To get the project root for template
from utils.maven_utils import get_java_pom_template
# from build.language_tools import create_java_tools # No longer needed

def get_transform_prompt(language, source_code):
    return {
        "messages": [
            (
                "user",
f"""
You are an expert polyglot software engineer specializing in high-fidelity, idiomatic code migration. Your mission is to perform a functional-equivalent translation of a specific Java function, ensuring the new implementation passes the same behavioral checks as the original.  You need to get a transformation template first.

**## CONTEXT ##**

*   **Source Language:** Java
*   **Target Language:** Rust
*   **Objective:** Translate the function `{source_code}` located in the source file into a functionally equivalent and idiomatic Rust implementation.
*   **Source File Path:** `src/main/java/com/exmaple/project/SensitiveFun.java`
*   **Target File Path:** `rust/src/lib.rs`
    ```

**## REQUIREMENTS ##**

1.  **Functional Equivalence:** The Rust code must replicate the exact behavior, logic, and edge cases of the original Java function. The primary measure of success is its ability to pass the provided unit tests' logic.
2.  **Idiomatic Rust Style:** You must adopt standard Rust patterns, including ownership/borrowing, `Result` and `Option` for error handling, iterators, and traits. Avoid direct, literal translations that lead to unidiomatic or unsafe code.
3.  **Type Mapping:** Intelligently map Java types (e.g., `List`, `Map`, `String`, custom classes) to the most appropriate and performant Rust equivalents (e.g., `Vec`, `HashMap`, `String`, `struct`). All custom types in the Java code must be defined as Rust `struct`s or `enum`s.
4.  **Dependency Management:** Based on Java `pom.xml` dependencies, identify and recommend the closest equivalent Rust crates. Provide an example of the `[dependencies]` section in `Cargo.toml`, which is necessary for compiling your generated code.
5.  **Full Autonomy:** You must operate without requesting clarification or external resources. Make reasonable, professional decisions for any ambiguities based on the provided context.
6.  **Code Completeness:** The generated Rust code for `Rust/src/lib.rs` must be a complete, compilable file, including all necessary `use` statements, `struct`/`enum` definitions, `impl` blocks, and the translated function itself.
7.  **External Calls**: The Java code should be able to call the converted equivalent code via `main.rs`, main.rs is the server-side called in the template.

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
        for chunk in agent_executor.stream(initial_input, config={"recursion_limit": 150}):
            bool_result, last_stream_message = process_chunk(chunk)
            if bool_result:
                break


    logger.info("Finished abstract test creation workflow.")

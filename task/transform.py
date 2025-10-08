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
            source_code = f.read
        
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

        #TODO Detailed prompt transform and as a IPC
        initial_input = {"messages": [("user",f"""
        Your mission is to translate the function '{source_code}' in {language} project as a functional equivalent Rust project, saving the new implementation to `rust/src/lib.rs`.
        You must operate with complete autonomy, making all decisions based solely on the provided project context, without requesting clarification, additional information, or external resources.
        
        **Current File Structure:**
        1. **{language} file**: `src`
        2. **rust file**: `rust`

        **Core Requirements:**
        The body of the original Java function needs to be refactored into a relay function that uses stdin/stdout to forward its arguments to the Rust side. The main function on the Rust side will receive the arguments, call the equivalent function in lib.rs, and then return the result to Java.
        You need to run Java unit tests and ensure the results remain unchanged after converting to remote calls.
        
        ## Technical Requirements
        1.  **Communication Method**: Java and Rust will communicate via standard input (`stdin`) and standard output (`stdout`). Java will write parameters to the Rust process's `stdin` and read results from its `stdout`.
        2.  **Data Protocol**: All communication must use a standardized **JSON** format to ensure robustness and scalability.
            *   **Java to Rust (Request)**: Must be a JSON object containing `function_name` and `params` fields.
            *   **Rust to Java (Response)**: Must be a JSON object containing a `status` field (`success` or `error`). It should include a `data` field on success and an `error_message` field on failure.
        3.  **Rust Program**: Must be a standalone, executable binary. It should be implemented as a **generic dispatcher**, capable of calling different function logic based on the `function_name` in the request.
        4.  **Java Program**: Must include a generic invocation method, and the original functions should be refact
        """
        )]}
        
         # Run
        for chunk in agent_executor.stream(initial_input, config={"recursion_limit": 150}):
            bool_result, last_stream_message = process_chunk(chunk)
            if bool_result:
                break


    logger.info("Finished abstract test creation workflow.")

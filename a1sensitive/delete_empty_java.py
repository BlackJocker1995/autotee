import os
import shutil

from loguru import logger

from LLM.scenarios.code_build import CodeBuildScenario
from LLM.scenarios.code_conver import CodeConvertScenario
from a4build_test.convert_example import convert_example_str_list
from build.build_dynamic import RustDynamic
from static.projectUtil import list_directories


def query_convert(code_react, code):

    # Analysis function
    qus_result = code_react.model_agent.query(f"What does this piece of code accomplish? {code}")
    logger.info(qus_result)

    # message = """
    #    Implement this code using Rust with same type input and return.
    #    Note that it should be public and static.
    #    """
    # code_react.model_agent.add_message("user", message)

    for item in convert_example_str_list:
        code_react.model_agent.add_message("user", f"Implement this code using Rust with same type input and return."
                                                   f"Note that it should be public and static. For example, {item}")

    # Covernt
    qus_result = code_react.model_agent.query_json(message = f" Implement this code using Rust with same type input and return. ```{code}``` using Rust.",
                                                   output_format=CodeConvertScenario.RustCodeFormatWithDep, remember=True)

    code_react.model_agent.messages_memary.pop(2)

    rust_code = qus_result.code
    rust_dependency = qus_result.dependency

    logger.debug(rust_code)
    # # Write the Rust code to a new project
    rust_target = RustDynamic()
    rust_target.new_project()
    rust_target.delete_file("main.rs")
    rust_target.clear_dependencies()
    rust_target.write_file_code("lib.rs",rust_code)
    rust_target.update_dependency(rust_dependency)
    logger.info(rust_dependency)

    qus_result = code_react.infer_react(question=CodeBuildScenario.convert_and_build_prompt(rust_code),
                                        output_format=CodeBuildScenario.ReactOutputForm)
    if "Get answer" in qus_result:
        logger.info(qus_result)
    else:
        return False

    return True


if __name__ == '__main__':

    base_path = "/home/rdhan/data/dataset/java"
    source_path = "/home/rdhan/tee"

    overwrite = False

    dirs = list_directories(base_path)

    for project_path in dirs:
        code_file_path = os.path.join(project_path, "code_file")
        # List all directories within the specified path
        subdirs = list_directories(code_file_path)
        if len(subdirs) == 0:
            shutil.rmtree(os.path.join(base_path, project_path))

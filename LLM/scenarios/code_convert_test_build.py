import os.path
from typing import Optional, Dict

from LLM.action import Scenario
from build.build_dynamic import BuildConfig, RustDynamic, JavaDynamic, CodeDynamic
from static.get_env import return_env

def contains_star(arr):
    for item in arr:
        if '*' in item:
            return True
    return False

class CodeConvertBuildTestScenario(Scenario):

    @classmethod
    def prompt_code_analysis(cls, code:str):
        return f"What does this piece of code accomplish? {code}"

    @classmethod
    def prompt_convert_example(cls, languages:str, convert_example_str_list:list[str]):
        out =  (f"Convert this {languages} code to Rust. "
                f"Their structure and the functions employed may differ."
                f"Note that it should be public. For example, ")
        for item in convert_example_str_list:
            out += item
        return out


    @classmethod
    def prompt_convert_and_build_prompt(cls, language:str) -> str:
        return (f"I will give you a block of {language} code; "
                f"Please follow its code logic and convert it into Rust program code."
                f"Please note that it is necessary to ensure that the functionality remains the same, "
                f"and some functions can be substituted with those provided by Rust."
                f"Ensure that the input and output remain unchanged.")

    class Actions(Scenario.Actions):
        def __init__(self, language: str, source_project_path: str, rust_project_path: str):
            rust_config = BuildConfig(language="rust", exec_extension="rs", test_file_name="test", project_path=rust_project_path, project_name="tee")
            self.rust = RustDynamic(rust_config)
            self.other_language = CodeDynamic.class_generator(language, source_project_path)

        def update_dependencies(self, dependencies: list) -> str:
            """
                Update or add dependencies for a Rust project.

                This function interacts with the `Cargo.toml` file of a Rust project. It first clears
                existing dependencies and then updates or adds new ones based on the provided list.
                Each dependency is set to a wildcard version (`*`), indicating that any version is
                acceptable.
                Do not provide specific version numbers.
                When calculating the MD5 hash, it is advisable to utilize the md-5 dependency rather than
                the 'md5' dependency, as the latter has not been updated for a considerable period.

                :param dependencies: A list of dependency names to be added or updated.
                :type dependencies: list

                :return: A message indicating the success or failure of the operation. If successful,
                         it returns the result of the build check as a string. Otherwise, it returns
                         "Failed to add the dependency."
                :rtype: str


                ```
                update_dependencies(['aes', 'rand'])

                ```

                """

            # Check if the dependencies contain a '*' character, which is not allowed.
            if contains_star(dependencies):
                return "Error arguments! should be a list without '=' or '*'."

            # Clear existing dependencies in the Rust project.
            self.rust.clear_dependencies()

            # Attempt to update the dependencies with the provided list.
            if self.rust.update_dependency(dependencies):
                # Perform a build check on the Rust project.
                check_result = self.rust.build_check()

                # If the build check is successful, build the target and notify the user.
                if "success" in check_result:
                    self.rust.build_target()
                    return "The code is now operational; please verify its consistency."

                # Return the result of the build check if it was not successful.
                return check_result
            else:
                # Return an error message if updating dependencies failed.
                return "Failed to add the dependency."

        def verify_output_consistency(self):
            """
            Compare whether the output of the transformed code matches that of the source code.

            Please note that if it pertains to random methods, consistency can be deemed adequate as long as the format is the same.

            For instance, '[98, 86, 26, 42, 42]' and '[98, 14, 26, 42, 58]' are same format;

            'Encrypted: b3bbfPHQOU4FdmL5cVfi0hMpQ12ryFLPadGYonJvASs=T6c8mxOoGIipwn8ZExxhQA==' and
            'Encrypted: b3bbfPHQOU4FdmL5cVfi0g==YKqPqcch9fFNlOK0uGrpiQ==' are same format;

            '185/Kr5mWK+UwU3oCWIBvw==' and 'F+9wOBUhizlc7bbQGRzdng==' are same format;

            '8C80ZFF6+umuqVqWgWA7+d+5A8Qtb5/6ekcCStrppVA='and 'gqponOBdkZolVk/jP0OfE5s1Dhok+dBT' are same format;

            If arrays are of the same length but contain different elements, they are considered consistent.
            Using the same cryptography type is also deemed consistent.

            :return:
            """
            self.rust.build_target()
            # Execute the code and store the result.
            source_result = self.other_language.execute()
            # Execute the Rust code and store the result.
            rust_result = self.rust.execute()
            # Return a formatted string comparing both results.
            if source_result == rust_result:
                return "The output is consistent."
            else:
                return f"Inconsistent, source output is '{source_result}', rust output is '{rust_result}'. "

        def update_rust_code(self, code: str) -> str:
            """
               Writes the specified code to the main.rs file.

               This operation opens the file located at the specified Rust `.rs` path and writes the provided code to it.
               The file is overwritten with the new content, ensuring that the entire file contains only the new code.

               :param code: The code snippet to be written to the `main.rs` file.
               :type code: str

               For instance,
               update_rust_code("use aes::Aes128;
                    pub fn decrypt_file(file: &str, dest_file: &str, decrypt_type: &str) -> i32 {
                        let cipher = match get_pattern(decrypt_type) {
                            Some(cipher) => cipher,
                            None => return 6,
                        };
               ")

            """
            # Write the provided code to a file named "main.rs"
            self.rust.write_file_code("main.rs", code)

            # Perform a build check on the Rust code
            check_result = self.rust.build_check()

            # If the build check passes, proceed to build the target
            if "Check pass" in check_result:
                # Build the Rust project
                self.rust.build_target()

                # Return a message indicating that the code is executable
                return "The code is now executable; please verify its consistency."

            # If the build check does not pass, return the result of the check
            return str(check_result)



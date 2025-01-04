from typing import Optional, Dict

from LLM.action import Scenario
from build.build_dynamic import RustDynamic


class CodeBuildScenario(Scenario):

    # class ReactOutputForm(Scenario.OutputForm):
    #     thought: str
    #     action: str
    #     argument: Optional[Dict[str, object]]
    #     # observation: str
    #     # finish: bool
    #
    # class ActOutputForm(Scenario.OutputForm):
    #     action: str
    #     argument: Optional[Dict[str, object]]
    #     observation: str
    #     answer: bool

    @classmethod
    def convert_and_build_prompt(cls, block: str, ) -> str:
        return (f"Please analyze the Rust code and ensure it can be compiled successfully. "
                f"If there have any cryptography you can replace as a rust implement."
                f"Code: {block}")

    class Actions(Scenario.Actions):
        @staticmethod
        def update_dependencies(dependencies: list) -> str:
            """
                Update or add dependencies for a Rust project.

                This function interacts with the `Cargo.toml` file of a Rust project. It first clears
                existing dependencies and then updates or adds new ones based on the provided list.
                Each dependency is set to a wildcard version (`*`), indicating that any version is
                acceptable.
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

            target_rust = RustDynamic()
            target_rust.clear_dependencies()
            if target_rust.update_dependency(dependencies):
                check_result = target_rust.build_check()
                return check_result
            else:
                return "Failed to add the dependency."

        # @staticmethod
        # def update_dependencies_code_with_version(dependencies: list, versions: list = None) -> str:
        #     """
        #           Update or add dependencies in the Cargo.toml file.
        #
        #           This function reads the `Cargo.toml` file from the specified project path,
        #           locates the `[dependencies]` section, and either updates existing dependencies
        #           or adds new ones based on the provided lists. If no version list is provided,
        #           each dependency is set to a wildcard version (`*`), indicating that any version
        #           is acceptable.
        #
        #           :param dependencies: A list of dependency names to be added or updated.
        #           :type dependencies: list
        #           :param versions: An optional list of versions corresponding to each dependency.
        #                            If not provided, all dependencies will default to version `*`.
        #           :type versions: list, optional
        #
        #           """
        #     target_rust = TargetRust()
        #     if target_rust.update_dependency(dependencies, versions):
        #         return "Successfully add the dependency."
        #     else:
        #         return "Failed to add the dependency."

        @staticmethod
        def remove_dependency_item(dependency_name: str) -> str:
            """
                Remove a dependency from the Cargo.toml file.

                :param dependency_name: The name of the dependency to be removed.
                :type dependency_name: str

                :returns: A string indicating the result of the operation. If successful,
                          it returns the result of the build check as a string. Otherwise,
                          it returns "Failed to remove the dependency."

                For instance,


                """
            target_rust = RustDynamic()
            if target_rust.remove_dependency(dependency_name):
                check_result = target_rust.build_check()
                return str(check_result)
            else:
                return "Failed to remove the dependency."

        @staticmethod
        def update_rust_code(code: str) -> str:
            """
               Writes the specified code to the lib.rs file.

               This operation opens the file located at the specified Rust `.rs` path and writes the provided code to it.
               The file is overwritten with the new content, ensuring that the entire file contains only the new code.

               :param code: The code snippet to be written to the `lib.rs` file.
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
            target_rust = RustDynamic()
            target_rust.write_file_code("lib.rs",code)
            check_result = target_rust.build_check()
            return str(check_result)

        # @staticmethod
        # def explain_error_code(error_code: str) -> str:
        #     """
        #          Explain a Rust compiler error code by executing the appropriate command.
        #
        #          This method constructs a command to invoke the Rust compiler's explanation feature
        #          for a given error code and executes it within the project's environment.
        #
        #          :param error_code: The Rust compiler error code to be explained.
        #          :type error_code: str
        #          :return: A string containing the explanation of the specified error code.
        #          :rtype: str
        #     """
        #     target_rust = TargetRust()
        #     return target_rust.explain_error_code(error_code)

        # @staticmethod
        # def get_function_doc(crate_name: str, function_name: str) -> str:
        #     """
        #     Fetch the documentation for a specific function from the Rust crate documentation.
        #
        #     This function constructs a URL to access the documentation of a given function
        #     It sends an HTTP GET request to retrieve the HTML content of the documentation page and attempts to extract
        #     the relevant documentation block for the function.
        #
        #     :param crate_name: The name of the Rust crate.
        #     :type crate_name: str
        #     :param function_name: The name of the function whose documentation is to be fetched.
        #     :type function_name: str
        #
        #     :returns: A string containing the documentation text if found, or an error message
        #               indicating that the documentation could not be retrieved or does not exist.
        #     :rtype: str
        #
        #     :raises requests.exceptions.RequestException: If there is an issue with the HTTP request.
        #     """
        #     return fetch_rust_function_doc(crate_name, function_name)

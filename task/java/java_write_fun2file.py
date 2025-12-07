import os
from task.common.base_write_fun2file import BaseWriter
from loguru import logger

class JavaWriter(BaseWriter):
    def _write_single_file(self, index: int, code_block: dict, hash_subdir: str) -> None:
        code_content = code_block.get("code", "")
        function_name = code_block.get("function_name", f"unknown_func_{index}")

        # Use "SensitiveFun" as the base class name, or derive from function_name if available and not a placeholder
        base_class_name = "SensitiveFun"
        if function_name and not function_name.startswith("unknown_func_"):
            base_class_name = function_name[0].upper() + function_name[1:]
        
        class_name = base_class_name
        output_file_name = f"{class_name}.java"
        
        # Define Maven standard directory structure for main Java files
        java_main_dir = os.path.join(hash_subdir, "src", "main", "java", "com", "example", "project")
        os.makedirs(java_main_dir, exist_ok=True)
        
        output_file_path = os.path.join(java_main_dir, output_file_name)

        # Wrap the function code in a class with package declaration
        wrapped_code_content = f"""package com.example.project;
        public class {class_name} {{
            {code_content}
        }}
        """
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(wrapped_code_content)
        logger.info(f"Written sensitive Java class to: {output_file_path}")

import os
from task.common.base_write_fun2file import BaseWriter
from loguru import logger

class PythonWriter(BaseWriter):
    def _write_single_file(self, index: int, code_block: dict, hash_subdir: str) -> None:
        code_content = code_block.get("code", "")
        function_name = code_block.get("function_name", f"unknown_func_{index}")
        
        # For Python, save the function code as a .py file
        output_file_name = f"{function_name}.py"
        output_file_path = os.path.join(hash_subdir, output_file_name)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        logger.info(f"Written sensitive Python function to: {output_file_path}")

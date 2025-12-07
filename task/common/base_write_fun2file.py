import os
from abc import ABC, abstractmethod
from static.projectUtil import short_hash
from loguru import logger

class BaseWriter(ABC):
    def __init__(self, project_path: str, sensitive_code_blocks: list[dict]):
        self.project_path = project_path
        self.sensitive_code_blocks = sensitive_code_blocks
        self.project_code_files_dir = os.path.join(project_path, "project_code_files")
        os.makedirs(self.project_code_files_dir, exist_ok=True)
        logger.info(f"Created output directory for sensitive code files: {self.project_code_files_dir}")

    def write_sensitive_code_to_files(self) -> None:
        """
        Writes sensitive code blocks to individual files in a designated directory.
        """
        for i, code_block in enumerate(self.sensitive_code_blocks):
            code_content = code_block.get("code", "")
            code_hash = short_hash(code_content)
            hash_subdir = os.path.join(self.project_code_files_dir, code_hash)
            os.makedirs(hash_subdir, exist_ok=True)
            self._write_single_file(i, code_block, hash_subdir)
        logger.info("Finished writing sensitive code blocks to individual files.")

    @abstractmethod
    def _write_single_file(self, index: int, code_block: dict, hash_subdir: str) -> None:
        pass

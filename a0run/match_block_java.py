import os
import ray

NUM_THREADS = 6  # Default number of threads, can be adjusted
from static.code_match import JavaCode
from static.projectUtil import save_code_block, list_directories
from loguru import logger


def split_into_chunks(dirs: list[str], chunk_size: int = 10) -> list[list[str]]:
    """Split directories into chunks for parallel processing."""
    chunks = []
    num_chunks = NUM_THREADS
    avg_chunk_size = len(dirs) // num_chunks
    for i in range(num_chunks):
        start_index = i * avg_chunk_size
        end_index = start_index + avg_chunk_size if i < num_chunks - 1 else len(dirs)
        chunks.append(dirs[start_index:end_index])
    return chunks

@ray.remote
def process_directory(dir_item, overwrite=False):
    code_ana = JavaCode()
    if not overwrite and os.path.exists(f"{dir_item}/java_ast.json"):
        return None
    
    files = code_ana.find_specific_files(dir_item)
    code_blocks = code_ana.ast_code_from_files(files)
    logger.info(f"{dir_item}, We get {len(code_blocks)} code blocks.")
    save_code_block(dir_item, code_blocks, "java_ast")
    return len(code_blocks)

if __name__ == '__main__':
    logger.info(f"Initializing Ray with {NUM_THREADS} threads")
    ray.init(num_cpus=NUM_THREADS)
    
    overwrite = False
    dirs = list_directories("/home/rdhan/data/dataset/java")

    # Create all futures at once
    logger.info(f"Starting processing of {len(dirs)} directories")
    futures = [process_directory.remote(dir_item, overwrite) for dir_item in dirs]
    
    # Wait for all futures to complete
    results = ray.get(futures)
    logger.info(f"Completed processing all directories")
    
    total_blocks = sum(r for r in results if r is not None)
    logger.info(f"Total code blocks processed: {total_blocks}")
    
    ray.shutdown()

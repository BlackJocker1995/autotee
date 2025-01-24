import shutil
from tqdm import tqdm
from static.projectUtil import list_directories, read_code_block, short_hash
import os
from loguru import logger


def list_directories(directory_path: str) -> list[str]:
    """返回指定路径下的所有目录"""
    try:
        return [d for d in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, d))]
    except Exception as e:
        logger.error(f"Error listing directories: {e}")
        return []


def process_sen_manual(dir_item: str, sen_votes: list[dict], overwrite: bool, language: str) -> None:
    """Process sensitive manual code blocks for specified language
    
    Args:
        dir_item: Directory containing the code blocks
        sen_votes: List of code blocks to process
        overwrite: Whether to overwrite existing files
        language: Either 'java' or 'python'
    """
    code_file_path = os.path.join(dir_item, "code_file")
    if not os.path.exists(code_file_path):
        os.makedirs(code_file_path)

    for code in tqdm(sen_votes):
        hash_index = short_hash(code["block"])
        current_file_path = os.path.join(code_file_path, f"{hash_index}_{language}")
        
        if not os.path.exists(current_file_path):
            os.makedirs(current_file_path)

        main_file = os.path.join(current_file_path, f"main.{'java' if language == 'java' else 'py'}")
        
        # Skip if file exists and not overwriting
        if os.path.exists(main_file) and not overwrite:
            continue

        with open(main_file, "w", encoding="utf-8") as f:
            f.write(code["block"])


def main(language: str = "java", overwrite: bool = False) -> None:
    """Main function to process code directories for specified language
    
    Args:
        language: Either 'java' or 'python'
        overwrite: Whether to overwrite existing files
    """
    if language not in ["java", "python"]:
        raise ValueError("Language must be either 'java' or 'python'")

    directory = f"/home/rdhan/data/dataset/{language}"
    dirs = list_directories(directory)
    
    for dir_item in dirs:
        logger.info(f"Processing {language} project: {dir_item}")
        sen_votes = read_code_block(os.path.join(directory, dir_item), "sen_manual")
        
        # Clean up empty Python directories
        if language == "python" and len(sen_votes) == 0:
            shutil.rmtree(os.path.join(directory, dir_item))
            continue
            
        logger.info(f"Found {len(sen_votes)} {language} code blocks")
        process_sen_manual(os.path.join(directory, dir_item), sen_votes, overwrite, language)


if __name__ == "__main__":
    # Example usage:
    # main(language="java")  # For Java processing
    # main(language="python", overwrite=True)  # For Python processing with overwrite
    main(language="java")
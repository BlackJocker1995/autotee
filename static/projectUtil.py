import hashlib
import json
import os
import shutil
from loguru import logger

def save_code_block(path:str, code_blocks:list[dict], name="data"):
    """
    Save a list of code blocks to a JSON file.

    This function takes a list of code block dictionaries and saves them to a JSON file
    at the specified path. The file will be named according to the provided name parameter.

    :param path: The directory path where the JSON file should be saved
    :type path: str
    :param code_blocks: List of code block dictionaries to save
    :type code_blocks: list[dict]
    :param name: Base name for the output file (without extension). Defaults to "data"
    :type name: str, optional
    """
    with open(f'{path}/{name}.json', 'w', encoding='utf-8') as json_file:
        json.dump(code_blocks, json_file, indent=4)

def read_code_block(path:str, name="data") -> list[dict]:
    """
    Read code blocks from a JSON file.

    This function reads a list of code block dictionaries from a JSON file
    located at the specified path. The file should have been created using
    save_code_block().

    :param path: The directory path where the JSON file is located
    :type path: str
    :param name: Base name of the input file (without extension). Defaults to "data"
    :type name: str, optional
    :return: List of code block dictionaries
    :rtype: list[dict]
    """
    with open(f'{path}/{name}.json', 'r', encoding='utf-8') as json_file:
        code_blocks = json.load(json_file)
    return code_blocks

def list_directories(folder_path):
    """
    List all subdirectories in a given folder path.

    This function returns a list of full paths for all subdirectories
    within the specified folder path.

    :param folder_path: Path to the folder to scan for subdirectories
    :type folder_path: str
    :return: List of full paths to subdirectories
    :rtype: list[str]
    """
    # List all subdirectories in the specified path with their full paths
    return [os.path.join(folder_path, d) for d in os.listdir(folder_path) if
            os.path.isdir(os.path.join(folder_path, d))]

def copy_directory(source_directory, destination_directory, skip_list=None):
    """
    Copies the contents of the source directory to the destination directory,
    optionally skipping specified folders.

    This function attempts to copy all files and subdirectories from the specified
    source directory to the destination directory, excluding any folders listed in
    the skip_list. If the destination directory already exists, it will catch the
    `FileExistsError` and print a message. Any other exceptions encountered during
    the copy process will also be caught and printed.

    :param source_directory: The path to the directory to be copied.
    :type source_directory: str
    :param destination_directory: The path where the directory should be copied to.
    :type destination_directory: str
    :param skip_list: A list of folder names to skip during the copy process.
    :type skip_list: list, optional
    """
    try:
        # Construct the full destination path including the source directory name
        destination_path = os.path.join(destination_directory, os.path.basename(source_directory))

        def ignore_folders(dir, files):
            return [f for f in files if os.path.isdir(os.path.join(dir, f)) and f in (skip_list or [])]

        # Attempt to copy the entire directory tree, including the root directory
        shutil.copytree(source_directory, destination_path, ignore=ignore_folders)
        logger.info(f"Successfully copied {source_directory} to {destination_directory}")
        if skip_list:
            logger.info(f"Skipped folders: {', '.join(skip_list)}")
    except FileExistsError:
        # Handle the case where the destination directory already exists
        logger.error(f"The destination directory {destination_directory} already exists!")
    except Exception as e:
        # Catch any other exceptions and print the error message
        logger.error(f"An error occurred: {e}")



def short_hash(input_string, length=8):
    """
     Generate a shortened SHA-256 hash of the input string.

     This function takes an input string, computes its SHA-256 hash,
     and returns the first `length` characters of the resulting hash.

     :param input_string: The string to be hashed.
     :type input_string: str
     :param length: The number of characters to return from the hash. Defaults to 8.
     :type length: int, optional
     :return: A substring of the SHA-256 hash of the input string.
     :rtype: str

     :raises ValueError: If the specified length is greater than the length of the full hash.
     """

    # Generate a SHA-256 hash
    hash_object = hashlib.sha256(input_string.encode())
    full_hash = hash_object.hexdigest()

    # Return the specified length of the short hash
    return full_hash[:length]

def truncate_string(s, length=100):
    """
    Truncate a string to a specified length and append an ellipsis if necessary.

    This function checks if the input is a string, removes newline characters,
    and truncates it to the specified length. If the string exceeds the given
    length, it appends '...' to indicate truncation.

    :param s: The string to be truncated.
    :type s: str

    :param length: The maximum length of the truncated string, including the ellipsis.
                   Defaults to 30.
    :type length: int

    :return: The truncated string with an ellipsis if it was longer than the specified length,
             or the original string if it was shorter or equal to the specified length.
             If the input is not a string, it returns the input unchanged.
    :rtype: str or any
    """
    if not isinstance(s, str):
        return s
    s = s.replace('\n', '')
    if len(s) > length:
        return s[:length] + '...'
    return s

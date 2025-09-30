import hashlib
import os
import json
import shutil
from typing import Optional


def get_base_dir():
    return os.path.dirname(os.path.abspath(__file__))

def get_abs_project_path(project_name):
    base_dir = get_base_dir()
    return os.path.abspath(os.path.join(base_dir, '..', 'projects', project_name))

def get_output_path(project_name):
    base_dir = get_base_dir()
    output_path = os.path.join(base_dir, '..', 'output', project_name)
    ensure_dir(output_path) # Ensure output directory exists
    return output_path

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def read_file(path):
    try:
        if not os.path.exists(path):
            raise FileExistsError(f"File {path} does not exist.")
        # Try reading with UTF-8 first (common default)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # If UTF-8 fails, try Latin-1 as a fallback
        # Latin-1 can decode any byte, preventing errors but might not render characters correctly if the encoding is truly different
        # Consider adding logging here if needed: logger.warning(f"UTF-8 decoding failed for {path}, falling back to latin-1")
        with open(path, 'r', encoding='latin-1') as f:
            return f.read()

def read_lines(path):
    with open(path, 'r') as f:
        return f.readlines()

def write_file(path, content):
    ensure_dir(os.path.dirname(path)) # Ensure directory exists before writing
    with open(path, 'w') as f:
        f.write(content)

def check_path_exists(path):
    return os.path.exists(path)

def store_source_code_result(result, output_path):
    content = json.dumps(result, indent=2)
    write_file(output_path, content)

def list_directories(folder_path):
    """
    List all subdirectories in a given folder path.

    This function returns a list of full paths for all subdirectories
    within the specified folder path.

    :param folder_path: Path to the folder to scan for subdirectories
    :type folder_path: str
    :return: List of full paths to subdirectories
    :rtype: list[dict[str, str]]
    """
    # List all subdirectories in the specified path with their full paths
    return [os.path.join(folder_path, d) for d in os.listdir(folder_path) if
            os.path.isdir(os.path.join(folder_path, d))]

def hash_dict(test_items: list[dict[str, str]]):
    return hashlib.md5(json.dumps(test_items).encode('utf-8')).hexdigest()[:8]

def copy_jacoco_xml(project_name, test_hash):
    shutil.copy('target/site/jacoco/jacoco.xml', os.path.join(project_name, 'database', "jacoco", f"{test_hash}.xml"))

def build_recursive_directory_tree_string(resolved_root_dir: str) -> str:
    """
    Recursively builds a string representation of the directory tree structure
    starting from resolved_root_dir, including both files and directories.

    Args:
        resolved_root_dir (str): The absolute path to the root directory to scan.

    Returns:
        str: A string representing the directory tree structure.
             Returns an empty string if resolved_root_dir is not a valid directory.
    """
    if not os.path.isdir(resolved_root_dir):
        return ""

    tree_lines = []

    def build_tree_recursive(current_dir, depth):
        # Determine indentation based on depth
        indent_prefix = '    ' * depth
        entry_prefix = indent_prefix + '|-- '

        try:
            # List items, sort them alphabetically
            items = sorted(os.listdir(current_dir))
        except OSError:
            # Append an error message if directory is inaccessible
            tree_lines.append(f"{entry_prefix}[Error accessing directory]")
            return

        for item in items:
            item_path = os.path.join(current_dir, item)
            # Exclude 'build' and 'target' directories
            if os.path.isdir(item_path) and item in ['build', 'target']:
                continue
            # Check if it's a directory
            if os.path.isdir(item_path):
                # Append directory entry and recurse
                tree_lines.append(f"{entry_prefix}{item}/") # Indicate directory with a slash
                build_tree_recursive(item_path, depth + 1)
            # Check if it's a file
            elif os.path.isfile(item_path):
                # Append file entry
                tree_lines.append(f"{entry_prefix}{item}")
            # Optionally, handle other types like symlinks etc. here if needed

    # Add the root directory name as the first line
    tree_lines.append(os.path.basename(resolved_root_dir))
    # Start the recursive build process for the contents of the root directory
    build_tree_recursive(resolved_root_dir, 0) # Initial depth is 0 for items inside root

    # Join all collected lines into a single string
    return "\n".join(tree_lines)

def create_status_flag(directory: str, success: bool, message: str, iterations: Optional[int] = None):
    """Creates a success or failure flag file, optionally including iteration count."""
    success_flag_path = os.path.join(directory, 'conversion_success.flag')
    failure_flag_path = os.path.join(directory, 'conversion_failed.flag')

    # Clean up existing flags
    if os.path.exists(success_flag_path):
        try:
            os.remove(success_flag_path)
        except OSError as e:
            print(f"Warning: Could not remove existing success flag: {e}")
    if os.path.exists(failure_flag_path):
        try:
            os.remove(failure_flag_path)
        except OSError as e:
            print(f"Warning: Could not remove existing failure flag: {e}")

    # Determine flag path and content
    flag_path = success_flag_path if success else failure_flag_path
    status = "Success" if success else "Failure"
    full_message = f"Conversion Status: {status}\n"
    if iterations is not None:
        full_message += f"Agent Iterations: {iterations}\n"
    full_message += f"Message: {message}\n"

    # Create the flag file
    try:
        os.makedirs(os.path.dirname(flag_path), exist_ok=True)
        with open(flag_path, 'w') as f:
            f.write(full_message)
        print(f"Created status flag file at: {flag_path}")
    except Exception as e:
        print(f"Error: Failed to create status flag file at {flag_path}: {e}")

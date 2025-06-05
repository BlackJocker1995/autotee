import os
import shutil

from static.projectUtil import list_directories

if __name__ == '__main__':
    """
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Delete File  !!!!!!!!!!!!!!!!!!!!

    """
    base_path = "/home/rdhan/data/dataset/java"
    source_path = "/home/rdhan/tee"

    overwrite = False

    dirs = list_directories(base_path)

    for project_path in dirs:
        code_file_path = os.path.join(project_path, "code_file")
        # List all directories within the specified path
        subdirs = list_directories(code_file_path)
        subdirs = [it for it in subdirs if "_java" in it]
        for it in subdirs:
            if not os.path.exists(os.path.join(code_file_path, it, 'Test.java')):
                shutil.rmtree(os.path.join(code_file_path, it))

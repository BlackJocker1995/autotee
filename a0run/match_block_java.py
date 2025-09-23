# Import the JavaCode analyzer from static.code_match
# Import the common processing function from match_block_common
from a0run.match_block_common import run_processing

# Main execution block
if __name__ == '__main__':
    # Run the common processing logic for Java projects
    # Arguments: Language string, Dataset Path, AST File Suffix
    run_processing("java", "/home/rdhan/data/dataset/java")

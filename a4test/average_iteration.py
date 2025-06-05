import os
from typing import List
import matplotlib.pyplot as plt

from loguru import logger
from tqdm import tqdm

from build.build_assistance import TestAssistance
from static.projectUtil import list_directories

def collect_results(project_path: str, model_name: str = "gpt") -> List[float]:
    """Collect result values from conversion directories.
    
    Args:
        project_path: Path to project directory containing result directories
        
    Returns:
        List[float]: List of all result values
    """
    code_file_path = os.path.join(project_path, "code_file")
    dirs = list_directories(code_file_path)
    
    results = []
    for dir_item in dirs:
        # Look for directories ending with _rust_{model_name}
        if f"_rust_{model_name}" in dir_item:
            rust_dir = os.path.join(code_file_path, dir_item)
            # Get all subdirectories that are numeric
            for result_dir in list_directories(rust_dir):
                try:
                    # Get just the last part of the path
                    result_value = os.path.basename(result_dir)
                    # Try to convert just the numeric part to float
                    result = float(result_value)
                    results.append(result)
                except ValueError:
                    continue
    
    return results

def plot_density(results: List[float], label: str, color: str):
    """Plot probability density of results.
    
    Args:
        results: List of result values
        label: Label for this histogram
        color: Color for this histogram
    """
    plt.hist(results, bins=range(1, 21), density=True, color=color, 
             alpha=0.5, label=label, histtype='stepfilled')
  
    
    #plt.close()

if __name__ == "__main__":
    output_image = "result_histogram.png"
    plt.figure(figsize=(12, 8))
    plt.title('Result Value Probability Density')
    plt.xlabel('Result Value')
    plt.ylabel('Density')
    plt.grid(True)
    plt.xticks(range(1, 21))
    plt.xlim(1, 20)
    
    colors = ['blue', 'green', 'red', 'purple']
    
    for idx, (model_name, language) in enumerate([("gpt", "python"), ("gpt", "java"), ("deepseek", "python"), ("deepseek", "java")]):
        base_path = f"/home/rdhan/data/dataset/{language}_mul_case"
        dirs = list_directories(base_path)
        all_results = []
        
        for dir_item in tqdm(dirs):
            logger.info(f"Processing {dir_item}")
            project_path = os.path.join(base_path, dir_item)
            
            results = collect_results(project_path, model_name=model_name)
            all_results.extend(results)
                
        if all_results:
            plot_density(all_results,
                        label=f"{model_name} ({language})",
                        color=colors[idx % len(colors)])
            logger.success(f"Histogram for {model_name} ({language}) added")
        else:
            logger.warning(f"No valid results found for {model_name} ({language})")
    
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
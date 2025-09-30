from abc import ABC


class BaseAnalyzer(ABC):
    """Base class for all analyzers in the project.
    
    This abstract class defines the common interface that all analyzers must implement.
    It provides basic functionality for result management and logging.
    """
    
    def __init__(self, language: str, project_path: str):
        """Initialize the analyzer.
        
        Args:
            language: The programming language to analyze.
        """
        self.language = language
        self.project_path = project_path
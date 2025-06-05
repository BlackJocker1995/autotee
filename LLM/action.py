from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel

class Scenario(ABC):
    """Abstract base class defining the interface for scenario implementations."""
    
    class OutputForm(BaseModel):
        """Base class for all scenario output formats."""
        pass

    @classmethod
    def get_class_method_info(cls) -> Tuple[List[str], List[str]]:
        """Get information about all public methods in the Actions class.
        
        Returns:
            Tuple containing:
                - List of method names
                - List of method docstrings
        """
        methods = inspect.getmembers(cls.Actions, predicate=inspect.isfunction)
        return (
            [name for name, _ in methods if not name.startswith('__')],
            [inspect.getsource(obj) for name, obj in methods if not name.startswith('__')]
        )

    @abstractmethod
    class Actions(ABC):
        """Abstract base class for scenario actions."""
        
        def __init__(self, **kwargs: Dict[str, Any]) -> None:
            """Initialize actions with configuration.
            
            Args:
                **kwargs: Configuration parameters
            """
            self.config = kwargs

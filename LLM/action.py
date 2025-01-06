import inspect
from abc import ABC, abstractmethod
from pydantic import BaseModel

class Scenario(ABC):
    """Abstract base class defining the interface for scenario implementations.
    
    Subclasses must implement the Actions inner class which contains
    the available actions for the scenario.
    """

    @classmethod
    def get_class_method_info(cls) -> tuple[list[str], list[str]]:
        """Get information about all public methods in the Actions class.
        
        Returns:
            tuple[list[str], list[str]]: A tuple containing two lists:
                - List of method names
                - List of method source code
        """
        methods = inspect.getmembers(cls.Actions, predicate=inspect.isfunction)
        return (
            [name for name, _ in methods if not name.startswith('__')],
            [inspect.getsource(obj) for name, obj in methods if not name.startswith('__')]
        )

    @abstractmethod
    class Actions(ABC):
        """Abstract base class defining the interface for scenario actions.
        
        Subclasses must implement all action methods that will be available
        for the scenario.
        """
        
        def __init__(self, **arguments: dict) -> None:
            """Initialize actions with any required arguments.
            
            Args:
                **arguments: Dictionary of arguments required for the actions
            """
            pass

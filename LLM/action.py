import inspect
from abc import ABC, abstractmethod
from pydantic import BaseModel

class Scenario(ABC):

    @classmethod
    def get_class_method_info(cls)-> [list,list]:
        methods_name = []
        methods_info = []
        for name, obj in inspect.getmembers(cls.Actions, predicate=inspect.isfunction):
            source = inspect.getsource(obj)
            if not name.startswith('__'):
                # append result
                methods_name.append(name)
                methods_info.append(source)
        return methods_name, methods_info

    @abstractmethod
    class Actions(ABC):
        def __init__(self,**arguments):
            pass

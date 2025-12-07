from typing import Dict, List

class TaskState:
    """A base class for holding the state of a task."""
    def __init__(self, required_states: List[str]):
        self.states: Dict[str, bool] = {state: False for state in required_states}

    def reset(self):
        for key in self.states:
            self.states[key] = False

    def set_success(self, key: str):
        if key in self.states:
            self.states[key] = True

    def set_failed(self, key: str):
        if key in self.states:
            self.states[key] = False

    def is_success(self) -> bool:
        if not self.states:
            return True
        return all(self.states.values())

class TestGenTaskState(TaskState):
    """A state manager for the test generation task."""
    def __init__(self):
        super().__init__(required_states=["unit_test", "coverage_pass"])

    def set_failed(self, key: str):
        super().set_failed(key)
        # If tests fail, coverage is no longer valid and must be re-evaluated.
        if key == 'unit_test' and 'coverage_pass' in self.states:
            self.states['coverage_pass'] = False

class ConvertTaskState(TaskState):
    """A state manager for the conversion task."""
    def __init__(self):
        super().__init__(required_states=["unit_test", "cargo_check"])

    def set_failed(self, key: str):
        super().set_failed(key)
        # If tests fail, coverage is no longer valid and must be re-evaluated.
        if key == 'cargo_check':
            self.states['unit_test'] = False

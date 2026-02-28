class FlagNotFoundError(Exception):
    def __init__(self, name: str):
        super().__init__(f"Feature flag '{name}' does not exist")

class DuplicateFlagError(Exception):
    def __init__(self, name: str):
        super().__init__(f"Feature flag '{name}' already exists")

from enum import Enum, auto


class AutoName(Enum):
    @staticmethod
    def _generate_next_value_(name: str, *args, **kwargs) -> str:
        return name


class UserRoles(AutoName):
    USER = auto()
    ADMIN = auto()

from typing import Any


def str_to_bool(value: Any) -> bool:
    if str(value).strip().lower() in ["1", "on", "t", "true", "y", "yes"]:
        return True
    return False

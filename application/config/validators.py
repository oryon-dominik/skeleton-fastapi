from typing import List


def dissassemble_comma_seperated_lists_of_strings(value: str) -> List[str]:
    """Validate that the value is a comma seperated list of strings"""
    if not isinstance(value, str):
        raise ValueError(f'Expected a string, got {type(value)}')
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    if "'" in value:
        value = value.replace("'", "")
    if '"' in value:
        value = value.replace('"', "")
    return [x.strip() for x in value.split(',') if x]

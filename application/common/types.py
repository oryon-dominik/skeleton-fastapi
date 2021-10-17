from typing import Union, List, Dict

JSONType = Union[str, int, float, bool, None, List['JSONType'], Dict[str, 'JSONType']]

def is_json_serializable(object):
    raise NotImplementedError

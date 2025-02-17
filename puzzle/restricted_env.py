# restricted_env.py
class RestrictedEnvironment(dict):
    """Ultra-secure execution environment"""
    def __init__(self):
        super().__init__()
        self.allowed_builtins = {
            'None': None,
            'True': True,
            'False': False,
            'bool': bool,
            'int': int,
            'float': float,
            'str': str,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'range': range,
            'len': len,
            'sum': sum,
            'min': min,
            'max': max,
            'sorted': sorted,
            'zip': zip,
        }
        
    def __getitem__(self, key):
        if key not in self.allowed_builtins:
            raise NameError(f"Access to '{key}' is restricted")
        return self.allowed_builtins[key]
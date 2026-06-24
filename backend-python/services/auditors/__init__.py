# Auditors package - Automatic discovery of all auditor classes
import pkgutil
import importlib
from typing import List, Type
from .base_auditor import BaseAuditor

# Automatically discover all auditor modules in this package
_AUDITOR_CLASSES: List[Type[BaseAuditor]] = []

for _, module_name, _ in pkgutil.iter_modules(__path__):
    # Skip the base_auditor module itself
    if module_name == "base_auditor":
        continue

    # Import the module
    module = importlib.import_module(f".{module_name}", package=__name__)

    # Find all classes in the module that inherit from BaseAuditor
    for item_name in dir(module):
        item = getattr(module, item_name)
        if (isinstance(item, type) and
            issubclass(item, BaseAuditor) and
            item is not BaseAuditor):
            _AUDITOR_CLASSES.append(item)

# Export the discovered classes
__all__ = [cls.__name__ for cls in _AUDITOR_CLASSES]

# Also make them available as module attributes for backward compatibility
for cls in _AUDITOR_CLASSES:
    globals()[cls.__name__] = cls
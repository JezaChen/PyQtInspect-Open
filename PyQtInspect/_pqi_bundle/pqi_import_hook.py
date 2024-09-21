import sys
import importlib

class ImportInterceptor(importlib.abc.Loader):
    def __init__(self, package_permissions):
        self.package_permissions = package_permissions

    def find_module(self, fullname, path=None):
        if fullname in self.package_permissions:
            if self.package_permissions[fullname]:
                return self
            else:
                raise ImportError("Package import was not allowed")

    def load_module(self, fullname):
        sys.meta_path = [x for x in sys.meta_path[1:] if x is not self]
        module = importlib.import_module(fullname)
        sys.meta_path = [self] + sys.meta_path
        return module


if not hasattr(sys,'frozen'):
    sys.meta_path = [ImportInterceptor({'textwrap': True, 'Pathlib': False})] + sys.meta_path


import textwrap

print(textwrap.dedent('    test'))
# Works fine

from pathlib import Path
# Raises exception
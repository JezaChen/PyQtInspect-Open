# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/8/7 16:04
# Description: 
# ==============================================

import PyQtInspect.pqi as pqi


def version():
    import os
    module_path = os.path.dirname(__file__)
    version_file_path = os.path.join(module_path, "VERSION")
    with open(version_file_path, 'r') as f:
        _version = int(f.read())
    return _version

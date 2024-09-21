# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/10/10 20:44
# Description: 
# ==============================================
import sys
import os

module_path = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(module_path))

if __name__ == '__main__':
    import PyQtInspect.pqi

    from PyQtInspect.pqi import SetupHolder

    PyQtInspect.pqi.main()

# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/10/11 18:48
# Description: 
# ==============================================
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

if __name__ == '__main__':
    import PyQtInspect.pqi
    from PyQtInspect.pqi import SetupHolder

    PyQtInspect.pqi.main()

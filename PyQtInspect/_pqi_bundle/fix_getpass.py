# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/8/18 15:12
# Description: 
# ==============================================
def fix_getpass():
    try:
        import getpass
    except ImportError:
        return  # If we can't import it, we can't fix it
    import warnings
    fallback = getattr(getpass, 'fallback_getpass', None)  # >= 2.6
    if not fallback:
        fallback = getpass.default_getpass  # <= 2.5 @UndefinedVariable
    getpass.getpass = fallback
    if hasattr(getpass, 'GetPassWarning'):
        warnings.simplefilter("ignore", category=getpass.GetPassWarning)

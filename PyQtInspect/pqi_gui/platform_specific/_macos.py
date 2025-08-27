from PyQtInspect.pqi_gui.platform_specific._base import Setup
from PyQtInspect import version
from PyQtInspect._pqi_bundle import pqi_log


class MacOSSetup(Setup):
    @staticmethod
    def _setupBundleName():
        # https://stackoverflow.com/questions/5047734/in-osx-change-application-name-from-python
        # Set app name, if PyObjC is installed
        # Python 2 has PyObjC preinstalled
        # Python 3: pip3 install pyobjc-framework-Cocoa
        try:
            import os
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                app_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if app_info:
                    app_info['CFBundleName'] = version.PQI_NAME
        except ImportError as e:
            pqi_log.warning(f"Cannot import pyobjc to set app name: {e}")

    @staticmethod
    def setup():
        """ Set up macOS-specific configurations. """
        MacOSSetup._setupBundleName()

import ctypes

from PyQtInspect.pqi_gui.platform_specific._base import Setup
from PyQtInspect import version


class WindowsSetup(Setup):
    @staticmethod
    def _setupAppId():
        myappid = f'jeza.tools.pyqt_inspect.{version.PQI_VERSION}'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    @staticmethod
    def setup():
        """ Set up macOS-specific configurations. """
        WindowsSetup._setupAppId()

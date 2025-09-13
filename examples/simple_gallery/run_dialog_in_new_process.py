import subprocess
import sys

if len(sys.argv) != 2 or sys.argv[1] not in ('pyqt5', 'pyqt6', 'pyside2', 'pyside6'):
    print("Usage: python run_dialog_in_new_process.py [pyqt5|pyqt6|pyside2|pyside6]")
    print("Example: python run_dialog_in_new_process.py pyqt5")
    print("Note: You need to install the corresponding PyQt or PySide package.")
    sys.exit(1)

subprocess.run(["python", "run_dialog.py", sys.argv[1]])

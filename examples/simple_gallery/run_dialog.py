import sys

loaded = False

if len(sys.argv) != 2 or sys.argv[1] not in ('pyqt5', 'pyqt6', 'pyside2', 'pyside6'):
    print("Usage: python run_dialog.py [pyqt5|pyqt6|pyside2|pyside6]")
    print("Example: python run_dialog.py pyqt5")
    print("Note: You need to install the corresponding PyQt or PySide package.")
    sys.exit(1)


if sys.argv[1] == 'pyqt5':
    from gallery_dialog_pyqt5 import Ui_GalleryDialog, QtWidgets
    loaded = True
elif sys.argv[1] == 'pyqt6':
    from gallery_dialog_pyqt6 import Ui_GalleryDialog, QtWidgets
    loaded = True
elif sys.argv[1] == 'pyside2':
    from gallery_dialog_pyside2 import Ui_GalleryDialog
    from PySide2 import QtWidgets
    loaded = True
elif sys.argv[1] == 'pyside6':
    from gallery_dialog_pyside6 import Ui_GalleryDialog
    from PySide6 import QtWidgets
    loaded = True


if __name__ == "__main__" and loaded:
    import sys

    app = QtWidgets.QApplication(sys.argv)
    GalleryDialog = QtWidgets.QDialog()
    ui = Ui_GalleryDialog()
    ui.setupUi(GalleryDialog)
    GalleryDialog.show()
    if sys.argv[1] in ('pyqt5', 'pyside2'):
        sys.exit(app.exec_())
    elif sys.argv[1] in ('pyqt6', 'pyside6'):
        sys.exit(app.exec())

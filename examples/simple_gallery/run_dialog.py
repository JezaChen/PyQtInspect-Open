import sys

loaded = False

if sys.argv[1] == 'pyqt5':
    from gallery_dialog_pyqt5 import Ui_GalleryDialog, QtWidgets
    loaded = True
elif sys.argv[1] == 'pyqt6':
    from gallery_dialog_pyqt6 import Ui_GalleryDialog, QtWidgets
    loaded = True

if __name__ == "__main__" and loaded:
    import sys

    app = QtWidgets.QApplication(sys.argv)
    GalleryDialog = QtWidgets.QDialog()
    ui = Ui_GalleryDialog()
    ui.setupUi(GalleryDialog)
    GalleryDialog.show()
    if sys.argv[1] == 'pyqt5':
        sys.exit(app.exec_())
    elif sys.argv[1] == 'pyqt6':
        sys.exit(app.exec())

# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gallery_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

import sys
import subprocess
if sys.platform == "win32":
    from PySide6.QtAxContainer import QAxWidget
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCalendarWidget, QCheckBox,
    QColumnView, QComboBox, QCommandLinkButton, QDateEdit,
    QDateTimeEdit, QDial, QDialog, QDialogButtonBox,
    QDockWidget, QDoubleSpinBox, QFontComboBox, QFrame,
    QGraphicsView, QGroupBox, QHBoxLayout, QHeaderView,
    QKeySequenceEdit, QLCDNumber, QLabel, QLineEdit,
    QListView, QListWidget, QListWidgetItem, QMdiArea,
    QPlainTextEdit, QProgressBar, QPushButton, QRadioButton,
    QScrollArea, QScrollBar, QSizePolicy, QSlider,
    QSpinBox, QStackedWidget, QTabWidget, QTableView,
    QTableWidget, QTableWidgetItem, QTextBrowser, QTextEdit,
    QTimeEdit, QToolBox, QToolButton, QTreeView,
    QTreeWidget, QTreeWidgetItem, QUndoView, QVBoxLayout,
    QWidget)

class Ui_GalleryDialog(object):
    def setupUi(self, GalleryDialog):
        if not GalleryDialog.objectName():
            GalleryDialog.setObjectName(u"GalleryDialog")
        GalleryDialog.resize(447, 468)
        self.verticalLayout_3 = QVBoxLayout(GalleryDialog)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tabWidget = QTabWidget(GalleryDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_buttons = QWidget()
        self.tab_buttons.setObjectName(u"tab_buttons")
        self.verticalLayout_2 = QVBoxLayout(self.tab_buttons)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.pushButton = QPushButton(self.tab_buttons)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.clicked.connect(lambda: subprocess.Popen(
            ["python", "run_dialog.py", 'pyqt5'],
            close_fds=True, stdin=None, stdout=None, stderr=None,
        ))
        font = QFont()
        font.setBold(False)
        font.setItalic(False)
        font.setUnderline(False)
        self.pushButton.setFont(font)
        self.pushButton.setInputMethodHints(Qt.ImhDate|Qt.ImhPreferLatin|Qt.ImhTime)

        self.verticalLayout_2.addWidget(self.pushButton)

        self.toolButton = QToolButton(self.tab_buttons)
        self.toolButton.setObjectName(u"toolButton")
        self.toolButton.setInputMethodHints(Qt.ImhHiddenText)

        self.verticalLayout_2.addWidget(self.toolButton)

        self.radioButton = QRadioButton(self.tab_buttons)
        self.radioButton.setObjectName(u"radioButton")
        self.radioButton.setInputMethodHints(Qt.ImhNone)

        self.verticalLayout_2.addWidget(self.radioButton)

        self.checkBox = QCheckBox(self.tab_buttons)
        self.checkBox.setObjectName(u"checkBox")

        self.verticalLayout_2.addWidget(self.checkBox)

        self.commandLinkButton = QCommandLinkButton(self.tab_buttons)
        self.commandLinkButton.setObjectName(u"commandLinkButton")
        self.commandLinkButton.setEnabled(True)
        self.commandLinkButton.setMaximumSize(QSize(16777215, 50))

        self.verticalLayout_2.addWidget(self.commandLinkButton)

        self.buttonBox = QDialogButtonBox(self.tab_buttons)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout_2.addWidget(self.buttonBox)

        self.tabWidget.addTab(self.tab_buttons, "")
        self.tab_item_views = QWidget()
        self.tab_item_views.setObjectName(u"tab_item_views")
        self.verticalLayout = QVBoxLayout(self.tab_item_views)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.listView = QListView(self.tab_item_views)
        self.listView.setObjectName(u"listView")
        self.listView.setItemAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.listView)

        self.treeView = QTreeView(self.tab_item_views)
        self.treeView.setObjectName(u"treeView")

        self.verticalLayout.addWidget(self.treeView)

        self.tableView = QTableView(self.tab_item_views)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout.addWidget(self.tableView)

        self.columnView = QColumnView(self.tab_item_views)
        self.columnView.setObjectName(u"columnView")

        self.verticalLayout.addWidget(self.columnView)

        self.undoView = QUndoView(self.tab_item_views)
        self.undoView.setObjectName(u"undoView")
        self.undoView.setItemAlignment(Qt.AlignHorizontal_Mask)
        icon = QIcon(QIcon.fromTheme(u"application-exit"))
        self.undoView.setCleanIcon(icon)

        self.verticalLayout.addWidget(self.undoView)

        self.tabWidget.addTab(self.tab_item_views, "")
        self.tab_item_widgets = QWidget()
        self.tab_item_widgets.setObjectName(u"tab_item_widgets")
        self.verticalLayout_4 = QVBoxLayout(self.tab_item_widgets)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.listWidget = QListWidget(self.tab_item_widgets)
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout_4.addWidget(self.listWidget)

        self.treeWidget = QTreeWidget(self.tab_item_widgets)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.treeWidget.setHeaderItem(__qtreewidgetitem)
        self.treeWidget.setObjectName(u"treeWidget")

        self.verticalLayout_4.addWidget(self.treeWidget)

        self.tableWidget = QTableWidget(self.tab_item_widgets)
        self.tableWidget.setObjectName(u"tableWidget")

        self.verticalLayout_4.addWidget(self.tableWidget)

        self.tabWidget.addTab(self.tab_item_widgets, "")
        self.tab_containers = QWidget()
        self.tab_containers.setObjectName(u"tab_containers")
        self.verticalLayout_5 = QVBoxLayout(self.tab_containers)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.groupBox = QGroupBox(self.tab_containers)
        self.groupBox.setObjectName(u"groupBox")

        self.verticalLayout_5.addWidget(self.groupBox)

        self.scrollArea = QScrollArea(self.tab_containers)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 417, 49))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_5.addWidget(self.scrollArea)

        self.toolBox = QToolBox(self.tab_containers)
        self.toolBox.setObjectName(u"toolBox")
        self.pagehahh = QWidget()
        self.pagehahh.setObjectName(u"pagehahh")
        self.pagehahh.setGeometry(QRect(0, 0, 419, 49))
        self.toolBox.addItem(self.pagehahh, u"Page hahh")
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.page_2.setGeometry(QRect(0, 0, 100, 30))
        self.toolBox.addItem(self.page_2, u"Page 2")

        self.verticalLayout_5.addWidget(self.toolBox)

        self.tabWidget_2 = QTabWidget(self.tab_containers)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        self.tabWidget_2.setTabPosition(QTabWidget.North)
        self.tabWidget_2.setTabShape(QTabWidget.Rounded)
        self.tabWidget_2.setDocumentMode(False)
        self.tabWidget_2.setTabsClosable(True)
        self.tabWidget_2.setMovable(True)
        self.tabWidget_2.setTabBarAutoHide(False)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.tabWidget_2.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.tabWidget_2.addTab(self.tab_2, "")

        self.verticalLayout_5.addWidget(self.tabWidget_2)

        self.stackedWidget = QStackedWidget(self.tab_containers)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stacked_widget_page1 = QWidget()
        self.stacked_widget_page1.setObjectName(u"stacked_widget_page1")
        self.stackedWidget.addWidget(self.stacked_widget_page1)
        self.stacked_widget_page2 = QWidget()
        self.stacked_widget_page2.setObjectName(u"stacked_widget_page2")
        self.stackedWidget.addWidget(self.stacked_widget_page2)

        self.verticalLayout_5.addWidget(self.stackedWidget)

        self.frame = QFrame(self.tab_containers)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)

        self.verticalLayout_5.addWidget(self.frame)

        self.widget = QWidget(self.tab_containers)
        self.widget.setObjectName(u"widget")

        self.verticalLayout_5.addWidget(self.widget)

        self.mdiArea = QMdiArea(self.tab_containers)
        self.mdiArea.setObjectName(u"mdiArea")
        self.mdiArea.setActivationOrder(QMdiArea.StackingOrder)
        self.mdiArea.setViewMode(QMdiArea.SubWindowView)
        self.mdiArea.setTabsMovable(True)

        self.verticalLayout_5.addWidget(self.mdiArea)

        self.dockWidget = QDockWidget(self.tab_containers)
        self.dockWidget.setObjectName(u"dockWidget")
        self.dockWidget.setFloating(False)
        self.dockWidget.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.dockWidget.setWidget(self.dockWidgetContents)

        self.verticalLayout_5.addWidget(self.dockWidget)

        if sys.platform == "win32":
            self.axWidget = QAxWidget(self.tab_containers)
            self.axWidget.setObjectName(u"axWidget")

            self.verticalLayout_5.addWidget(self.axWidget)

        self.tabWidget.addTab(self.tab_containers, "")
        self.tab_input_widgets = QWidget()
        self.tab_input_widgets.setObjectName(u"tab_input_widgets")
        self.horizontalLayout = QHBoxLayout(self.tab_input_widgets)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.comboBox = QComboBox(self.tab_input_widgets)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setEditable(True)

        self.verticalLayout_7.addWidget(self.comboBox)

        self.fontComboBox = QFontComboBox(self.tab_input_widgets)
        self.fontComboBox.setObjectName(u"fontComboBox")
        self.fontComboBox.setFontFilters(QFontComboBox.AllFonts)

        self.verticalLayout_7.addWidget(self.fontComboBox)

        self.lineEdit = QLineEdit(self.tab_input_widgets)
        self.lineEdit.setObjectName(u"lineEdit")

        self.verticalLayout_7.addWidget(self.lineEdit)

        self.textEdit = QTextEdit(self.tab_input_widgets)
        self.textEdit.setObjectName(u"textEdit")

        self.verticalLayout_7.addWidget(self.textEdit)

        self.plainTextEdit = QPlainTextEdit(self.tab_input_widgets)
        self.plainTextEdit.setObjectName(u"plainTextEdit")

        self.verticalLayout_7.addWidget(self.plainTextEdit)

        self.spinBox = QSpinBox(self.tab_input_widgets)
        self.spinBox.setObjectName(u"spinBox")

        self.verticalLayout_7.addWidget(self.spinBox)

        self.doubleSpinBox = QDoubleSpinBox(self.tab_input_widgets)
        self.doubleSpinBox.setObjectName(u"doubleSpinBox")

        self.verticalLayout_7.addWidget(self.doubleSpinBox)

        self.timeEdit = QTimeEdit(self.tab_input_widgets)
        self.timeEdit.setObjectName(u"timeEdit")
        self.timeEdit.setMinimumDate(QDate(1998, 1, 1))

        self.verticalLayout_7.addWidget(self.timeEdit)

        self.dateEdit = QDateEdit(self.tab_input_widgets)
        self.dateEdit.setObjectName(u"dateEdit")

        self.verticalLayout_7.addWidget(self.dateEdit)

        self.dateTimeEdit = QDateTimeEdit(self.tab_input_widgets)
        self.dateTimeEdit.setObjectName(u"dateTimeEdit")

        self.verticalLayout_7.addWidget(self.dateTimeEdit)

        self.dial = QDial(self.tab_input_widgets)
        self.dial.setObjectName(u"dial")

        self.verticalLayout_7.addWidget(self.dial)

        self.horizontalScrollBar = QScrollBar(self.tab_input_widgets)
        self.horizontalScrollBar.setObjectName(u"horizontalScrollBar")
        self.horizontalScrollBar.setOrientation(Qt.Horizontal)

        self.verticalLayout_7.addWidget(self.horizontalScrollBar)

        self.horizontalSlider = QSlider(self.tab_input_widgets)
        self.horizontalSlider.setObjectName(u"horizontalSlider")
        self.horizontalSlider.setOrientation(Qt.Horizontal)

        self.verticalLayout_7.addWidget(self.horizontalSlider)

        self.keySequenceEdit = QKeySequenceEdit(self.tab_input_widgets)
        self.keySequenceEdit.setObjectName(u"keySequenceEdit")

        self.verticalLayout_7.addWidget(self.keySequenceEdit)


        self.horizontalLayout.addLayout(self.verticalLayout_7)

        self.verticalScrollBar = QScrollBar(self.tab_input_widgets)
        self.verticalScrollBar.setObjectName(u"verticalScrollBar")
        self.verticalScrollBar.setOrientation(Qt.Vertical)

        self.horizontalLayout.addWidget(self.verticalScrollBar)

        self.verticalSlider = QSlider(self.tab_input_widgets)
        self.verticalSlider.setObjectName(u"verticalSlider")
        self.verticalSlider.setOrientation(Qt.Vertical)

        self.horizontalLayout.addWidget(self.verticalSlider)

        self.tabWidget.addTab(self.tab_input_widgets, "")
        self.tab_display_widgets = QWidget()
        self.tab_display_widgets.setObjectName(u"tab_display_widgets")
        self.verticalLayout_6 = QVBoxLayout(self.tab_display_widgets)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.label = QLabel(self.tab_display_widgets)
        self.label.setObjectName(u"label")
        self.label.setTextInteractionFlags(Qt.LinksAccessibleByKeyboard|Qt.LinksAccessibleByMouse)

        self.verticalLayout_6.addWidget(self.label)

        self.textBrowser = QTextBrowser(self.tab_display_widgets)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setSource(QUrl(u"file:///C:/Users/Jeza/PycharmProjects/PyqtInspect_new/examples/simple_gallery/simple_page.html"))

        self.verticalLayout_6.addWidget(self.textBrowser)

        self.graphicsView = QGraphicsView(self.tab_display_widgets)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setRenderHints(QPainter.TextAntialiasing)
        self.graphicsView.setCacheMode(QGraphicsView.CacheBackground)

        self.verticalLayout_6.addWidget(self.graphicsView)

        self.calendarWidget = QCalendarWidget(self.tab_display_widgets)
        self.calendarWidget.setObjectName(u"calendarWidget")

        self.verticalLayout_6.addWidget(self.calendarWidget)

        self.lcdNumber = QLCDNumber(self.tab_display_widgets)
        self.lcdNumber.setObjectName(u"lcdNumber")

        self.verticalLayout_6.addWidget(self.lcdNumber)

        self.progressBar = QProgressBar(self.tab_display_widgets)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(24)
        self.progressBar.setTextDirection(QProgressBar.TopToBottom)

        self.verticalLayout_6.addWidget(self.progressBar)

        self.line = QFrame(self.tab_display_widgets)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_6.addWidget(self.line)

        self.openGLWidget = QOpenGLWidget(self.tab_display_widgets)
        self.openGLWidget.setObjectName(u"openGLWidget")

        self.verticalLayout_6.addWidget(self.openGLWidget)

        self.quickWidget = QQuickWidget(self.tab_display_widgets)
        self.quickWidget.setObjectName(u"quickWidget")
        self.quickWidget.setResizeMode(QQuickWidget.SizeRootObjectToView)

        self.verticalLayout_6.addWidget(self.quickWidget)

        self.tabWidget.addTab(self.tab_display_widgets, "")

        self.verticalLayout_3.addWidget(self.tabWidget)

#if QT_CONFIG(shortcut)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(GalleryDialog)

        self.tabWidget.setCurrentIndex(3)
        self.toolBox.setCurrentIndex(0)
        self.tabWidget_2.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(GalleryDialog)
    # setupUi

    def retranslateUi(self, GalleryDialog):
        GalleryDialog.setWindowTitle(QCoreApplication.translate("GalleryDialog", u"Dialog", None))
        self.pushButton.setText(QCoreApplication.translate("GalleryDialog", u"Launch another dialog with PyQt5", None))
#if QT_CONFIG(shortcut)
        self.pushButton.setShortcut(QCoreApplication.translate("GalleryDialog", u"Ctrl+H, Ctrl+G, Ctrl+D", None))
#endif // QT_CONFIG(shortcut)
        self.toolButton.setText(QCoreApplication.translate("GalleryDialog", u"...", None))
        self.radioButton.setText(QCoreApplication.translate("GalleryDialog", u"RadioButton", None))
        self.checkBox.setText(QCoreApplication.translate("GalleryDialog", u"CheckBox", None))
        self.commandLinkButton.setText(QCoreApplication.translate("GalleryDialog", u"CommandLinkButton", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_buttons), QCoreApplication.translate("GalleryDialog", u"Buttons", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_item_views), QCoreApplication.translate("GalleryDialog", u"Item Views", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_item_widgets), QCoreApplication.translate("GalleryDialog", u"Item Widgets", None))
        self.groupBox.setTitle(QCoreApplication.translate("GalleryDialog", u"GroupBox", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.pagehahh), QCoreApplication.translate("GalleryDialog", u"Page hahh", None))
#if QT_CONFIG(tooltip)
        self.toolBox.setItemToolTip(self.toolBox.indexOf(self.pagehahh), QCoreApplication.translate("GalleryDialog", u"hahh!!", None))
#endif // QT_CONFIG(tooltip)
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), QCoreApplication.translate("GalleryDialog", u"Page 2", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab), QCoreApplication.translate("GalleryDialog", u"Tab 1", None))
#if QT_CONFIG(tooltip)
        self.tabWidget_2.setTabToolTip(self.tabWidget_2.indexOf(self.tab), QCoreApplication.translate("GalleryDialog", u"tooltip___1", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.tabWidget_2.setTabWhatsThis(self.tabWidget_2.indexOf(self.tab), QCoreApplication.translate("GalleryDialog", u"whatsthis___1", None))
#endif // QT_CONFIG(whatsthis)
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_2), QCoreApplication.translate("GalleryDialog", u"Tab 2", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_containers), QCoreApplication.translate("GalleryDialog", u"Containers", None))
        self.comboBox.setPlaceholderText(QCoreApplication.translate("GalleryDialog", u"Input...", None))
        self.textEdit.setDocumentTitle(QCoreApplication.translate("GalleryDialog", u"Hello", None))
        self.textEdit.setPlaceholderText(QCoreApplication.translate("GalleryDialog", u"Input...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_input_widgets), QCoreApplication.translate("GalleryDialog", u"Input Widget", None))
        self.label.setText(QCoreApplication.translate("GalleryDialog", u"TextLabel", None))
        self.textBrowser.setMarkdown(QCoreApplication.translate("GalleryDialog", u"# Hello, world! \n"
"\n"
"This is an example!!! \n"
"\n"
"", None))
        self.textBrowser.setHtml(QCoreApplication.translate("GalleryDialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><title>Quick hummus recipe</title><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Microsoft YaHei UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<h1 style=\" margin-top:18px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:xx-large; font-weight:700;\">Hello, world!</span> </h1>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">This is an example!!! </p></body></html>", None))
        self.textBrowser.setSearchPaths([
            QCoreApplication.translate("GalleryDialog", u"C:\\Users\\Jeza\\PycharmProjects\\PyqtInspect_new\\examples", None),
            QCoreApplication.translate("GalleryDialog", u"C:\\Users\\Jeza\\PycharmProjects\\PyqtInspect_new\\", None)])
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_display_widgets), QCoreApplication.translate("GalleryDialog", u"Display Widgets", None))
    # retranslateUi


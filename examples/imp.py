import sys
import multiprocessing

StyleSheet = """
/*These are general settings that apply to all buttons, but later definitions can override them.*/
QPushButton {
    border: none; /*Remove the border*/
}

/*
QPushButton#xxx
or
#xx
Both specify the button by its objectName.
*/
QPushButton#RedButton {
    background-color: #f44336; /*Background color*/
}
#RedButton:hover {
    background-color: #e57373; /*Background color when the cursor hovers*/
}
/*Note that the pressed state must be declared after the hover state; otherwise it will not take effect.*/
#RedButton:pressed {
    background-color: #ffcdd2; /*Background color while the mouse button remains pressed*/
}

#GreenButton {
    background-color: #4caf50;
    border-radius: 5px; /*Rounded corners*/
}
#GreenButton:hover {
    background-color: #81c784;
}
#GreenButton:pressed {
    background-color: #c8e6c9;
}

#BlueButton {
    background-color: #2196f3;
    /*Constrain the minimum and maximum size*/
    min-width: 96px;
    max-width: 96px;
    min-height: 96px;
    max-height: 96px;
    border-radius: 48px; /*Circular*/
}
#BlueButton:hover {
    background-color: #64b5f6;
}
#BlueButton:pressed {
    background-color: #bbdefb;
}

#OrangeButton {
    max-height: 48px;
    border-top-right-radius: 20px; /*Rounded top-right corner*/
    border-bottom-left-radius: 20px; /*Rounded bottom-left corner*/
    background-color: #ff9800;
}
#OrangeButton:hover {
    background-color: #ffb74d;
}
#OrangeButton:pressed {
    background-color: #ffe0b2;
}

/*Distinguish buttons by their text; likewise, other attributes can be used.*/
QPushButton[text="purple button"] {
    color: white; /*Text color*/
    background-color: #9c27b0;
}
"""
try:
    from PyQt5 import QtWidgets, QtCore
    from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QApplication

except ImportError:
    from PySide2.QtWidgets import QWidget, QHBoxLayout, QPushButton, QApplication

class Window(QWidget):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        import os
        print(f"pid: {os.getpid()}")
        layout = QHBoxLayout(self)
        layout.addWidget(QPushButton("red button", self,
                                     objectName="RedButton", minimumHeight=48))
        layout.addWidget(QPushButton("green button", self,
                                     objectName="GreenButton", minimumHeight=48))
        layout.addWidget(QPushButton("blue button", self,
                                     objectName="BlueButton", minimumHeight=48))
        layout.addWidget(QPushButton("orange button", self,
                                     objectName="OrangeButton", minimumHeight=48))
        layout.addWidget(QPushButton("purple button", self,
                                     objectName="PurpleButton", minimumHeight=48,
                                     clicked=self._onPurpleButtonClicked))

    def _onPurpleButtonClicked(self):
        multiprocessing.Process(target=main).start()

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    w = Window()
    w.show()
    sys.exit(app.exec_())

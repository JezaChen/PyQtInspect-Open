# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/8/1 10:59
# Description:
# ==============================================

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on January 29, 2018
@author: Irony
@site: https://pyqt.site , https://github.com/PyQt5
@email: 892768447@qq.com
@file: NormalStyle
@description:
"""

import sys
import multiprocessing


from PySide2.QtWidgets import QWidget, QHBoxLayout, QPushButton, QApplication, QLabel

StyleSheet = """
/*This is the general setting, effective for all buttons, but can be overridden later*/
QPushButton {
    border: none; /*Remove border*/
}

/*
QPushButton#xxx
or
#xx
Both represent specifying by the set objectName
*/
QPushButton#RedButton {
    background-color: #f44336; /*Background color*/
}
#RedButton:hover {
    background-color: #e57373; /*Background color on mouse hover*/
}
/*Note that pressed must be placed after hover, otherwise it has no effect*/
#RedButton:pressed {
    background-color: #ffcdd2; /*Background color when mouse is pressed and held*/
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
    /*Limit minimum and maximum size*/
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
    border-top-right-radius: 20px; /*Top-right rounded corner*/
    border-bottom-left-radius: 20px; /*Bottom-left rounded corner*/
    background-color: #ff9800;
}
#OrangeButton:hover {
    background-color: #ffb74d;
}
#OrangeButton:pressed {
    background-color: #ffe0b2;
}

/*Distinguish buttons by text content, similarly can distinguish by other attributes*/
QPushButton[text="purple button"] {
    color: white; /*Text color*/
    background-color: #9c27b0;
}
"""


class Window(QWidget):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        import os
        print(f"pid: {os.getpid()}")
        layout = QHBoxLayout(self)
        a = QLabel(self)
        layout.addWidget(QPushButton("red button", self,
                                     objectName="RedButton", minimumHeight=48))
        layout.addWidget(QPushButton("green button", self,
                                     objectName="GreenButton", minimumHeight=48))
        layout.addWidget(QPushButton("blue button", self,
                                     objectName="BlueButton", minimumHeight=48))
        layout.addWidget(QPushButton("orange button", self,
                                     objectName="OrangeButton", minimumHeight=48))
        layout.addWidget(QPushButton("purple button", self,
                                     objectName="PurpleButton", minimumHeight=48))


def main():
    # app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    w = Window()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    import os
    print(f"pid: {os.getpid()}")
    app = QApplication(sys.argv)
    # multiprocessing.Process(target=main).start()
    # main()
    main()
    sys.exit(app.exec_())


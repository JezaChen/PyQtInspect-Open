# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/9/7 19:09
# Description: 
# ==============================================

GLOBAL_STYLESHEET2 = """
QPushButton {
    border: 1px solid rgba(31, 35, 40, 0.15);
    border-radius: 2px;
    padding-left: 8px;
    padding-right: 8px;
    background-color: rgb(246, 248, 250);
    font: 12px "Microsoft Yahei";
    color: rgb(36, 41, 47);
}

QPushButton:hover {
    border: 1px solid rgb(221, 221, 221);
}
"""

GLOBAL_STYLESHEET = """
* {
    font-family: "Microsoft Yahei";
}

QMainWindow {
    background-color: #F0F0F0;
}

QPushButton {
    background-color: #FAFBFC;
    border: 1px solid rgba(27, 31, 35, 0.15);
    border-radius: 3px;
    color: #24292E;
    font: 12px "Microsoft Yahei";
    padding: 6px 10px;
}

QPushButton:hover {
    background-color: #F3F4F6;
}

QPushButton:pressed {
    background-color: #EDEFF2;
}

QPushButton:disabled {
    background-color: #FAFBFC;
    border-color: rgba(27, 31, 35, 0.15);
    color: #959DA5;
    cursor: default;
}

QLineEdit {
    border: 1px solid #D1D5DA;
    border-radius: 3px;
    padding: 6px 8px;
    font: 12px "Microsoft Yahei";
    color: #24292E;
}

QLineEdit:hover {
    border-color: #0366D6;
}

QLineEdit:focus {
    border-color: #0366D6;
    outline: none;
}

QLineEdit:disabled {
    background-color: #F0F0F0;
    border-color: rgba(27, 31, 35, 0.15);
    color: #959DA5;
}

QLineEdit#codeStyleLineEdit {
    font: 13px "Consolas";
}

QListWidget#stacksListWidget {
    border: 1px solid #D1D5DA;
    border-radius: 3px;
    font: 13px "Consolas";
    color: #24292E;
}

QListWidget#stacksListWidget::item {
    padding: 2px 0px;
}

QGroupBox {
    font: 13px "Microsoft Yahei";
}
"""

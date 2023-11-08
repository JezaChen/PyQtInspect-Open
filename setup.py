from setuptools import find_packages, setup

setup(
    name="PyQtInspect",
    version="0.01_alpha",
    url="https://git-cc.nie.netease.com/pc/pyqtinspect",
    author="Chen Jianzhang",
    author_email="jezachen@163.com",
    description="PyQtInspect",
    packages=find_packages(exclude=("*examples", "*examples.*")),
    python_requires=">=3.7, <4",
    install_requires=[
        "psutil",
        "PyQt5",
        "wingrab",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GPLv3 License",
    ],
    entry_points={
        "console_scripts": [
            "pqi-server = PyQtInspect.pqi_server_gui:main",
        ],
    }
)

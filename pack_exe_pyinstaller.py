import PyInstaller.__main__

PyInstaller.__main__.run([
    "PyQtInspect\\pqi_server_gui.py",
    "--onefile",
    "--windowed",
    "--clean",
])
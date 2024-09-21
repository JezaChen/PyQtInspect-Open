import PyInstaller.__main__

PyInstaller.__main__.run([
    "run_server.py",
    "--onefile",
    "--clean",
])

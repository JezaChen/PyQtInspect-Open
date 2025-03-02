from setuptools import find_packages, setup


def get_long_description() -> str:
    with open("README.md", encoding='utf8') as file:
        return file.read()

def get_version() -> str:
    import sys
    import pathlib

    base_dir = str(pathlib.Path(__file__).resolve().parent)
    sys.path.insert(0, base_dir)

    from PyQtInspect import version
    return version.PQI_VERSION


setup(
    name="PyQtInspect",
    version=get_version(),
    url="https://jeza-chen.com/PyqtInspect",
    author="Jianzhang Chen",
    author_email="jezachen@163.com",
    license="GPLv3",
    description="To inspect PyQt/PySide program elements like Chrome's element inspector",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("*examples", "*examples.*")),
    python_requires=">=3.7, <4",
    keywords="pyqt pyside inspect",
    install_requires=[
        "psutil",
        "PyQt5",
        "wingrab; platform_system=='Windows'",  # Only available on Windows
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points={
        "gui_scripts": [
            "pqi-server = PyQtInspect.pqi_server_gui:main",
        ],
    },
    # Use MANIFEST.in to include all files in the pqi_attach directory
    include_package_data=True,
)

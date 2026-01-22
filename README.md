<div align="center">
<img alt="icon.png" height="60" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/icon.png?raw=true"/>
</div>
<h1 align="center">PyQtInspect</h1>
<p align="center">Inspect PyQt/PySide elements like Chrome DevTools</p>

<p align="center">
<a href="https://github.com/JezaChen/PyQtInspect-Open">Source Code</a> |
<a href="https://pyqtinspect.jeza.net/index_zh">中文文档</a> | 
<a href="https://pypi.org/project/PyQtInspect/">PyPI</a>
</p>

For Python GUI programs developed with PyQt/PySide using Qt Widgets,
it is difficult to view control information, locate the codes where they are defined, 
and perform other operations at runtime. 
It's not as easy as inspecting HTML elements in Chrome/Firefox browsers. 
This project aims to solve this problem by providing an element inspector tool for PyQt/PySide programs, 
similar to Chrome's element inspector.

![hover and inspect](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/overview.gif?raw=true)

## 1. Requirements

- Python 3.7+

- One of the following Qt for Python frameworks installed: PyQt5/PySide2/PyQt6/Pyside6

## 2. Installation

### 2.1 Install from PyPI

Install with `pip install PyQtInspect`.

### 2.2 Install from Source

If you want to experience the latest features introduced in the master branch as soon as possible,
you can install from git or download the source ZIP package and install after extraction:

**Install from Git:**
```bash
pip install git+https://github.com/JezaChen/PyQtInspect-Open.git
```

> ⚠️ **Note:** Installing directly from the default branch is not reproducible. For deterministic installs, pin to a specific tag or commit.
> ```
> # pin to a specific tag
> pip install git+https://github.com/JezaChen/PyQtInspect-Open.git@v0.5.0
> # or pin to a specific commit
> pip install git+https://github.com/JezaChen/PyQtInspect-Open.git@<commit-sha>
> ```

**Install from Source ZIP:**
1. Download [the source ZIP package](https://github.com/JezaChen/PyQtInspect-Open/archive/refs/heads/master.zip)
2. Extract the ZIP package to a local directory
3. Navigate to the extracted directory and run:
```bash
pip install .
```

## 3. Quick Start

Use [**Direct Mode**](#direct-mode) to quickly attach PyQtInspect with your app. The GUI inspector will start alongside your app.

```powershell
python -m PyQtInspect --direct --file path/to/your_app.py [your_app_args]
```

## 4. Detailed Start Guide

The `PyQtInspect` architecture has two parts:

- **Debugger/Server/Inspector**: A GUI app for developers to visually inspect elements, locate code, etc.

- **Debuggee/Client**: Runs inside the target Python process, patches the host’s Python Qt framework, responds to the debugger, and sends host information back.

### 4.1 Overview of startup modes

Two startup modes are supported:

* [**Detached Mode**](#detached-mode): Manually start the GUI server first, then start the debuggee to connect to it. **When the debuggee exits, the GUI server remains running.**

* [**Direct Mode (Recommended)**](#direct-mode): Start only the debuggee; it will **launch a local GUI server automatically** (no need to start the server yourself). **When the debuggee exits, the GUI server exits with it.**

Note that in **Direct Mode**, each client (debuggee) creates its own server, i.e., one-to-one relationship. And you cannot manually specify the listening port, close connections, or attach to processes.

**Detached Mode** supports remote debugging (server and client on different machines). **Direct Mode** does not, since the client and its auto-launched server run on the same machine.

PyQtInspect also supports [running in IDEs like PyCharm](#run-with-ide) and [attaching to an existing PyQt/PySide process](#attach-mode).

### 4.2 Direct Mode (Convenient method, recommended 👍) <a id="direct-mode"></a>

This **recommended** one-step method launches both the PyQtInspect server and client together. It requires full access to the source code of the debugged program.

If you normally run your app via `python xxx.py param1 param2`, simply insert `-m PyQtInspect --direct --file` between `python` and `xxx.py`, i.e.:
`python -m PyQtInspect --direct --file xxx.py param1 param2` to start debugging with PyQtInspect.

> **✨ New in v0.5.0: Automatic Qt Framework Detection**  
> PyQtInspect now **automatically detects** which Qt framework your application uses (PyQt5, PyQt6, PySide2, or PySide6). You no longer need to specify `--qt-support` in most cases! The tool will detect and patch the appropriate framework based on the debugged program's imports.

For Direct Mode, the full command is:

```powershell
python -m PyQtInspect --direct [--multiprocess] [--show-pqi-stack] [--qt-support=[auto|pyqt5|pyside2|pyqt6|pyside6]] --file py_file [file_args]
```

Parameter meanings:

* `--direct`: Use **Direct Mode**
* `--multiprocess`: Enable **multi-process debugging**
* `--show-pqi-stack`: Show call stacks related to PyQtInspect
* `--qt-support`: Qt framework used by the target app, default `auto` (auto-detect); choose from `auto`, `pyqt5`, `pyside2`, `pyqt6`, `pyside6`
* `--file`: Path to the target app’s Python entry file
* `file_args`: Command-line arguments for the debuggee

> ⚠️ **Important:** When relying on **auto-detection**, make sure the IDE’s [‘PyQt compatible’ option][4] **matches the Qt framework used by your project**. A mismatch can prevent PyQtInspect from working correctly or even crash the program.
> 
> If you encounter issues with auto-detection, try explicitly specifying the framework with `--qt-support`.

### 4.3 Detached Mode (Traditional method, one-to-many debugging) <a id="detached-mode"></a>

In Detached Mode, **make sure to start the GUI server before launching the debugged Python program**.

#### 4.3.1 Start the Debugger (Server)

Run `pqi-server` in a terminal to launch the server GUI. After launch, set the listening port (default `19394`) and click **Serve** to start the server.

<img alt="start_server.png" height="600" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/start_server.png?raw=true"/>

#### 4.3.2 Start the Debuggee (Client): Attach PyQtInspect when running program source code

Prerequisite: You must have the target program’s source code.

Similar to Direct Mode, if you run an app via `python xxx.py param1 param2`, insert `-m PyQtInspect --file` between `python` and `xxx.py` (no `--direct`!), i.e.:
`python -m PyQtInspect --file xxx.py param1 param2` to start debugging with PyQtInspect.

PyQtInspect **auto-detects** the Qt framework (PyQt5/PyQt6/PySide2/PySide6) by default, so `--qt-support` is optional unless you want to override the detection.

For running the debuggee in detached mode, the full command is:

```powershell
python -m PyQtInspect [--port N] [--client hostname] [--multiprocess] [--show-pqi-stack] [--qt-support=[auto|pyqt5|pyside2|pyqt6|pyside6]] --file py_file [file_args]
```

Parameter meanings:

* `--port`: Server listening port (default `19394`)
* `--client`: Server address (default `127.0.0.1`)
* `--multiprocess`: Enable **multi-process debugging** (off by default)
* `--show-pqi-stack`: Show call stacks related to PyQtInspect (hidden by default)
* `--qt-support`: Qt framework used by the target app, default `auto` (auto-detect); choose from `auto`, `pyqt5`, `pyside2`, `pyqt6`, `pyside6`
* `--file`: Path to the target app’s Python entry file
* `file_args`: Command-line arguments for the target app

> ⚠️ **Re-emphasize:** When relying on **auto-detection**, make sure the IDE’s [‘PyQt compatible’ option][4] **matches the Qt framework used by your project** (PyQt5/PyQt6/PySide2/PySide6). A mismatch can prevent PyQtInspect from working correctly or even crash the program.

### 4.4 Other run methods

#### 4.4.1 Run PyQtInspect in PyCharm and other IDEs (supports Detached Mode/Direct Mode) <a id="run-with-ide"></a>

Debug the PyQtInspect module directly in PyCharm (or other IDEs/editors like VSCode/Cursor); this won’t interfere with debugging your app.

Also taking [`PyQt-Fluent-Widgets`][1] as an example, you can create a new Debug configuration like so:

<img alt="pycharm config" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/pycharm_config_en.png?raw=true"/>

Then simply Run/Debug.

#### 4.4.2 Attach to Process (Detached Mode only, currently unstable) <a id="attach-mode"></a>

If you **don’t have the target app’s source**, you can **try** enabling inspect via process attach.

Click **More → Attach To Process** to open the attach window, choose the target process, then click **Attach**.

**Note:** For most controls, you **cannot retrieve their creation call stacks** unless they were created **after** you attached.

![attach process](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/attach_process.gif?raw=true)

## 5. Usage

### 5.1 Select elements

Click **Select** to start picking. Hover over a control to highlight it and preview brief info (class name, object name, size, relative position, styles, etc.).

Left-click to select the control. You can then inspect it in depth: view and jump to its initialization call stack, execute code in its context, view hierarchy info, view the control tree, and inspect properties.

![hover and inspect](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/select_and_click.gif?raw=true)

### 5.2 View control properties

The second tab below the brief info shows detailed properties, organized hierarchically by class inheritance and property type.

<img alt="detailed_props" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/detailed_props.png?raw=true" width="350"/>

### 5.3 View the control’s creation call stack

The first tab below the brief info shows the call stack at control creation. Double-click to open your configured IDE (PyCharm/VSCode/Cursor or a custom command) and navigate to the file and line.

![create stacks](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/create_stack.gif?raw=true)

If IDE jump fails, please configure the IDE type and executable path under **More → Settings**.

**P.S. For clients started via [Attach to Process](#attach-mode), if the control already existed when you attached, creation info won’t be available and the call stack will be empty.**

### 5.4 Execute code

After selecting a control, click **Run Code** to execute code in the scope of the selected control (`self` is the control instance; essentially this runs inside a method of the control object).

![run code](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/run_code.gif?raw=true)

### 5.5 View hierarchy information

At the bottom is the hierarchy breadcrumb. You can view, highlight, and locate ancestor and child controls of the selection, making it easy to navigate the hierarchy.
Combined with mouse selecting, this enables more precise selection.

![inspect hierarchy](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/inspect_hierarchy.gif?raw=true)

### 5.6 While selecting, use right-click to simulate left-click

*(Enabled by default. To disable, go to **More → Mock Right Button Down as Left When Selecting Elements** and uncheck.)*

Some controls only appear after a left-click. For easier picking, you can simulate left-click with the right mouse button.

**P.S. This only applies while mouse selecting is active.**

![mock right button as left](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/mock_right_btn_as_left.gif?raw=true)

### 5.7 Force-select with F8

*(Only available on Windows, enabled by default. To disable, go to **More → Press F8 to Finish Selecting** and uncheck.)*

For controls that are hard to pick with the mouse, press **F8** to finish selection. Note that F8 only ends an ongoing selection; when selection isn’t active, pressing F8 will not start it.

### 5.8 View the control tree

Click **View → Control Tree** to see the control tree of the process that contains the selected control.
Click (or hover) a row in the tree to highlight the corresponding control.

![control tree](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/control_tree.gif?raw=true)

## 6. Known Issues
- **Patching fails with multiple inheritance involving more than two PyQt classes**, such as class `A(B, C)`, 
    where `B` and `C` inherit from **QObject**. This might cause the `__init__` method of `C` to not execute, leading to exceptions.
    > [The author of PyQt has warned against multiple inheritance with more than two PyQt classes][2], as it can also cause abnormal behavior in PyQt itself.

- Cannot select some controls for **PyQt6**.

- For some computers, sometimes the `QEnterEvent` will have the type `170` (which is `QEvent.DynamicPropertyChange`),
    which may cause crash when accessing the `propertyName` method.

## 7. Changelog

### 0.5.0

* **🎉 Auto-Detection Support**: PyQtInspect now automatically detects which Qt framework (PyQt5, PyQt6, PySide2, PySide6) your application uses - no need to specify `--qt-support` for most applications.
* IDE jump supports PyCharm, VSCode, Cursor, and custom commands, with auto-detection of IDE paths
* Improved Direct Mode server launch ordering and IDE detection logging
* Minor UI refinements

### 0.4.0

* Added the “Properties” tab
* Added toolbar entries to open/clear logs
* Fixed a series of issues

[1]: https://github.com/zhiyiYo/PyQt-Fluent-Widgets
[2]: https://www.riverbankcomputing.com/pipermail/pyqt/2017-January/038650.html
[3]: https://pypi.org/project/PyQtInspect/#files
[4]: https://www.jetbrains.com/help/pycharm/debugger-python.html
[5]: https://github.com/JezaChen/ihook

<div align="center">
<img alt="icon.png" height="60" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/icon.png?raw=true"/>
</div>
<h1 align="center">PyQtInspect</h1>
<p align="center">To inspect PyQt/PySide program elements like Chrome's element inspector.</p>

<p align="center">
<a href="https://github.com/JezaChen/PyQtInspect-Open">Source Code</a> |
<a href="https://jeza-chen.com/PyQtInspect-README-zh">中文文档</a> | 
<a href="https://pypi.org/project/PyQtInspect/">PyPI</a>
</p>

For Python GUI programs developed with PyQt/PySide using Qt Widgets,
it is difficult to view control information, locate the codes where they are defined, 
and perform other operations at runtime. 
It's not as easy as inspecting HTML elements in Chrome/Firefox browsers. 
This project aims to solve this problem by providing an element inspector tool for PyQt/PySide programs, 
similar to Chrome's element inspector.

![hover and inspect](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/hover_and_inspect.gif?raw=true)

## Requirements

- Python 3.7+

- One of the following Qt for Python frameworks: PyQt5/PySide2/PyQt6/Pyside6

## Installation

Simply install using `pip install PyQtInspect`.

## How to Start

The PyQtInspect architecture is divided into _two parts_:

- Debugger side (**Server**): A GUI program for viewing element information, locating code, etc.

- Debugged side (**Client**): Runs within the Python program to be debugged, 
  patches the host program's Qt framework, and transmits information to the server.

### Start Modes

Two start modes are currently supported:

- [**Detached Mode**](#start-in-detached-mode): Manually start the server first, then launch the client to connect to the server. 
    **The server will not close when the client closes.**
- [**Direct Mode**](#start-in-direct-mode): Start the client directly, **which will also launch a local server at the same time** 
    (no need to launch the server in advance). **The server will close when the client closes.**

In Direct Mode, running each debugged program will automatically create a corresponding server, 
forming a one-to-one relationship. 
Users cannot manually specify the server’s listening port, close the connection, or attach to other processes. 
Detached Mode supports remote debugging (the server and client are on different machines), 
whereas Direct Mode does not, as both the client and the server which is automatically launched run on the same machine.

Additionally, PyQtInspect supports [running in PyCharm and other IDEs](#running-pyqtinspect-in-pycharm-supports-detached-modedirect-mode-recommended), 
and [attaching to PyQt/PySide processes](#attach-to-process-supports-detached-mode-only-currently-unstable).

### Start in Direct Mode

This is the **recommended** method, which starts both the PyQtInspect server and client at the same time. 
It requires **full access to the Python source code** of the debugged program.

If you typically run **PyQt5 applications** using `python xxx.py param1 param2`,
just insert the `-m PyQtInspect --direct --file` argument between `python` and `xxx.py`,
like so: `python -m PyQtInspect --direct --file xxx.py param1 param2` to start PyQtInspect.

If the debugged program uses **PySide2/PyQt6/Pyside6**, 
you need to add the `--qt-support` parameter to specify the corresponding Qt framework. 
For example, for a PySide2 program, 
the full command is `python -m PyQtInspect --direct --qt-support=pyside2 --file xxx.py param1 param2`.

The complete command is:

```powershell
python -m PyQtInspect --direct [--multiprocess] [--show-pqi-stack] [--qt-support=[pyqt5|pyside2|pyqt6|pyside6]] --file executable_file [file_args]
```

Explanation of parameters:

* `--direct`: Specifies the start mode as **Direct Mode**
* `--multiprocess`: Specify whether to support **multiprocess inspecting**, **disabled by default**
* `--show-pqi-stack`: Specify whether to display the call stack related to `PyQtInspect`, **disabled by default**
* `--qt-support`: Specify the Qt framework used by the program being debugged, **default is `pyqt5`**; optional values are `pyqt5`, `pyside2`, `pyqt6`, `pyside6`
* `--file`: Specify the path to the Python source code file of the program to be debugged
* `file_args`: Command-line arguments for starting the program to be debugged

For example, to debug the **PySide2 version** of [PyQt-Fluent-Widgets][1],
which is usually run with `python examples/gallery/demo.py`, 
new you can use `python -m PyQtInspect --direct --qt-support=pyside2 --file examples/gallery/demo.py`
to start the PyQtInspect server and client in Direct Mode.

### Start in Detached Mode

In Detached Mode, make sure to start the GUI server before launching the debugged Python program.

#### Start the Debugger Side

Enter `pqi-server` in the terminal to start the server-side GUI program. 
After launching, specify the listening port (default is `19394`) 
and click the `Serve` button to start listening.

<img alt="start_server.png" height="600" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/start_server.png?raw=true"/>

#### Start the Debugged Side: Running Program Source Code attached with `PyQtInspect`

This requires full access to the Python source code of the debugged program.

If you run this program to be debugged with `python xxx.py param1 param2`, 
simply **insert** `-m PyQtInspect --file` **between** `python` and `xxx.py`, i.e.,
use `python -m PyQtInspect --file xxx.py param1 param2` to attach the PyQtInspect client
to the `xxx.py` program with parameters `param1` and `param2`.

The complete startup command is:

```powershell
python -m PyQtInspect [--port N] [--client hostname] [--multiprocess] [--show-pqi-stack] [--qt-support=[pyqt5|pyside2|pyqt6|pyside6]] --file executable_file [file_args]
```

Each parameter is explained as follows:

* `--port`: Specify the server's listening port, default is `19394`
* `--client`: Specify the server's listening address, default is `127.0.0.1`
* `--multiprocess`: Specify whether to support **multiprocess inspecting**, **disabled by default**
* `--show-pqi-stack`: Specify whether to display the call stack related to `PyQtInspect`, **disabled by default**
* `--qt-support`: Specify the Qt framework used by the program being debugged, **default is `pyqt5`**; optional values are `pyqt5`, `pyside2`, `pyqt6`, `pyside6`
* `--file`: Specify the path to the Python source code file of the program to be debugged
* `file_args`: Command-line arguments for starting the program to be debugged

For example, to debug the **PySide2 version** of [`PyQt-Fluent-Widgets`][1], 
the demo gallery program is run with `python examples/gallery/demo.py`.
Now you can start the `PyQtInspect` client with 
`python -m PyQtInspect --qt-support=pyside2 --file examples/gallery/demo.py`.
You can specify other parameters as needed.
**Make sure the server is already running and listening on port `19394`(default port) before starting the client.**

**Note: Only PyQt5 programs do not need the `--qt-support` parameter; 
other frameworks need to specify this parameter explicitly!**

### Other Running Methods

#### Running PyQtInspect in PyCharm (supports Detached Mode/Direct Mode) (Recommended)

Directly debug the `PyQtInspect` module in PyCharm without affecting program debugging.

Also taking [`PyQt-Fluent-Widgets`][1] as an example,
you can create a new Debug configuration with the following parameters:

![pycharm config](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/pycharm_config_en.png?raw=true)

Then just Run/Debug as usual.

#### Attach to Process (supports Detached Mode only, currently unstable)

**If the source code of the program to be debugged is not available**, 
you can attempt to start the `PyQtInspect` client by **attaching** to the process.

Click `More->Attach` To Process, select the process window of the program to be debugged, 
and click the `Attach` button.

**Note: Most controls will not have their creation call stack information 
unless they are created after attaching.**

![attach process](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/attach_process.gif?raw=true)

## Usage

### Inspecting Element Information

Click the `Inspect` button, **hover** the mouse over the control you want to inspect, 
and preview the control information.

![hover and inspect](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/hover_and_inspect.gif?raw=true)

Click the left mouse button to select the control. 
You can then locate the creation call stack, execute code, view hierarchy information, etc.

![then click](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/then_click.gif?raw=true)

### Call Stack Location

The area below the control information section shows the call stack at the time the control was created.
Clicking on it will open `PyCharm`, locating the corresponding file and line.

![create stacks](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/create_stacks.gif?raw=true)

If PyCharm fails to open, you can set the PyCharm path in `More->Settings` manually.

**p.s. For the PyQtInspect client started via Attach to Process, 
if the control was already created during the attach process, 
the call stack information will not be available, and this area will be empty.**

### Executing Code
After selecting a control, 
click the `Run Code` button to execute code within the scope of the selected control 
**(where the selected control instance is `self`, 
essentially executing code within one of the control's methods)**.

![run codes](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/run_codes.gif?raw=true)

### Viewing Hierarchy Information
A hierarchy navigation bar is at the bottom of the tool, 
allowing you **to directly view, highlight, 
and locate ancestor and child controls of the selected control**.
It also makes it easier to switch between controls within the hierarchy.

Combined with mouse selection, users can make more precise selections.

![inspect hierarchy](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/inspect_hierarchy.gif?raw=true)

### Simulate Left Click with Right Click During Inspection 

_(Enabled by Default, Disable in `More->Mock Right Button Down as Left`)_

Since some controls only appear after a left click, 
right-clicking can simulate a left click to facilitate inspection.

![mock right button as left](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/mock_right_btn_as_left.gif?raw=true)

### Force Selection with F8 

_(Enabled by Default, Disable in `More->Press F8 to Finish Inspect`)_

For controls that are difficult to select with a mouse click, 
you can complete the selection with F8. 
Note that F8 **is only used to finish selection** during the inspection process;
pressing F8 **WILL NOT start selection** if inspection is not active.

## Known Issues
- **Patching fails with multiple inheritance involving more than two PyQt classes**, such as class `A(B, C)`, 
    where `B` and `C` inherit from **QObject**. This might cause the `__init__` method of `C` to not execute, leading to exceptions.
    > [The author of PyQt has warned against multiple inheritance with more than two PyQt classes][2], as it can also cause abnormal behavior in PyQt itself.

- Cannot select some controls for **PyQt6**.

- For some computers, sometimes the `QEnterEvent` will have the type `170` (which is `QEvent.DynamicPropertyChange`),
    which may cause crash when accessing the `propertyName` method.


[1]: https://github.com/zhiyiYo/PyQt-Fluent-Widgets
[2]: https://www.riverbankcomputing.com/pipermail/pyqt/2017-January/038650.html
[3]: https://pypi.org/project/PyQtInspect/#files
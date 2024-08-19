<div align="center">
<img alt="icon.png" height="60" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/icon.png?raw=true"/>
</div>
<h1 align="center">PyQtInspect</h1>
<p align="center">To inspect PyQt/PySide program elements like Chrome's element inspector.</p>

[中文文档](https://jeza-chen.com/PyQtInspect-README-zh)

For Python GUI programs developed with PyQt/PySide using Qt Widgets,
it is difficult to view control information, locate the codes where they are defined, 
and perform other operations at runtime. 
It's not as easy as inspecting HTML elements in Chrome/Firefox browsers. 
This project aims to solve this problem by providing an element inspector tool for PyQt/PySide programs, 
similar to Chrome's element inspector.

## Requirements

- Python 3.7+

- One of the following Qt for Python frameworks: PyQt5/PySide2/PyQt6/Pyside6

## Installation

Simply install using `pip install PyQtInspect`.

## How to Start

The PyQtInspect architecture is divided into _two parts_:

- Debugging side (**Server**): A GUI program for viewing element information, locating code, etc.

- Debugged side (**Client**): Runs within the Python program to be debugged, 
  patches the host program's Qt framework, and transmits information to the server.

When debugging, please **start the GUI server first**, then launch the Python program to be debugged.

### Start the Debugging Side

Enter `pqi-server` in the terminal to start the server-side GUI program. 
After launching, specify the listening port (default is `19394`) 
and click the `Serve` button to start listening.

<img alt="start_server.png" height="600" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/start_server.png?raw=true"/>

### Start the Debugged Side

#### 1. Running Program Source Code with `PyQtInspect` Attached (Recommended)

It's the **recommended** startup method which requires full access to the Python source code of 
the program to be debugged.

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
* `--qt-support`: Specify the Qt framework used by the program being debugged, **default is `pyqt5`**
* `--file`: Specify the path to the Python source code file of the program to be debugged
* `file_args`: Command-line arguments for starting the program to be debugged

For example, to debug [`PyQt-Fluent-Widgets`][1], 
the demo gallery program is run with `python examples/gallery/demo.py`.
Now you can start the `PyQtInspect` client with 
`python -m PyQtInspect --file examples/gallery/demo.py`.

### 2. Using PyCharm (Recommended)

Directly debug the `PyQtInspect` module in PyCharm without affecting program debugging.

Also taking [`PyQt-Fluent-Widgets`][1] as an example,
you can create a new Debug configuration with the following parameters:

![pycharm config](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/pycharm_config_en.png?raw=true)

Then just Run/Debug as usual.

### 3. Attach to Process (Currently Unstable)

If the source code of the program to be debugged is not available, 
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

## Source Code

Currently, the source code distribution package can be downloaded from 
[PyPi][3], and the GitHub repository will be opened soon.

[1]: https://github.com/zhiyiYo/PyQt-Fluent-Widgets
[2]: https://www.riverbankcomputing.com/pipermail/pyqt/2017-January/038650.html
[3]: https://pypi.org/project/PyQtInspect/#files
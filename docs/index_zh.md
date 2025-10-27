<div align="center">
<img alt="icon.png" height="60" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/icon.png?raw=true"/>
</div>
<h1 align="center">PyQtInspect</h1>
<p align="center">像Chrome元素检查工具一样检查PyQt/PySide程序元素</p>

<p align="center">
<a href="https://github.com/JezaChen/PyQtInspect-Open">源代码</a> |
<a href="https://jeza-chen.com/PyqtInspect">英文文档</a> | 
<a href="https://pypi.org/project/PyQtInspect/">PyPI</a>
</p>

对于使用Qt Widgets编写的PyQt/PySide程序,
我们很难在运行时查看程序中的控件信息、定位控件代码, 无法做到像前端开发那样, 在浏览器中通过开发者工具轻松选择HTML元素, 定位代码及查看信息.

本项目旨在解决这个问题, 提供类似Chrome DevTools的PyQt/PySide程序元素检查工具, 以提高学习, 开发及调试效率.

![hover and inspect](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/overview.gif?raw=true)

## 1. 要求

- Python 3.7+
- 已安装以下Qt for Python的框架: PyQt5/PySide2/PyQt6/Pyside6

## 2. 安装

使用`pip install PyQtInspect`安装即可.

## 3. 启动

`PyQtInspect`架构分为两部分: 

- **调试端/服务端**: GUI程序, 供开发者直观地查看元素信息、定位代码等;

- **被调试端/客户端**: 运行在被调试的Python程序中，负责patch宿主程序的Python Qt框架, 响应调试端的请求以及将宿主程序的信息传递给调试端等.

### 3.1 启动模式简介

当前支持两种启动模式:

- [**分离模式**](#detached-mode): 先手动启动GUI服务端, 再启动被调试端以连接服务端. **被调试端关闭后, GUI服务端不会关闭.**

- [**直接模式 (推荐)**](#direct-mode): 仅需启动被调试端, 被调试端会自行**在本机启动**一个GUI服务端(无须开发者事先手动启动服务端). **被调试端关闭后会一同关闭GUI服务端.**

注意，**直接模式**下，每创建一个被调试端(客户端)的同时，都会创建一个服务端(服务端), 属于一对一的关系. 
此外, 在**直接模式**下, 用户无法手动指定监听端口、关闭连接以及Attach进程等操作. 

**分离模式**调试支持远程调试(服务端和客户端不在同一台机器上); 而在**直接模式**下, 由于自动启动的服务端和客户端在同一台机器上, 所以不支持远程调试.

此外, PyQtInspect还支持[在PyCharm等IDE上运行](#run-pyqtinspect-in-pycharm-and-other-ides),
以及[通过Attach进程的方式附加到PyQt/PySide进程中进行调试](#attach-to-process).

### 3.2 直接模式启动 (便捷方法, 推荐👍) { #direct-mode }

目前**推荐**的启动方法, 一步即可同时启动PyQtInspect服务端和客户端, 需要**使用者拥有被调试程序的Python源代码**.

如果你是通过`python xxx.py param1 param2`来运行你的**PyQt5**程序, 则仅需在`python`和`xxx.py`中间加入`-m PyQtInspect --direct --file`参数,
即`python -m PyQtInspect --direct --file xxx.py param1 param2`, 即可启动PyQtInspect调试.

如果被调试程序使用的是**PySide2/PyQt6/Pyside6**, 则需要**额外添加`--qt-support`参数**, 以指定对应的Qt框架.
举个例子, 如被调试程序使用的是PySide2, 则启动命令为`python -m PyQtInspect --direct --qt-support=pyside2 --file xxx.py param1 param2`.

直接模式下, 完整的启动命令为:

```powershell
python -m PyQtInspect --direct [--multiprocess] [--show-pqi-stack] [--qt-support=[pyqt5|pyside2|pyqt6|pyside6]] --file py_file [file_args]
```

各参数的含义如下:

* `--direct`: 指定启动模式为**直接模式**
* `--multiprocess`: 指定支持**多进程调试**, 默认不启用
* `--show-pqi-stack`: 指定显示和PyQtInspect相关的调用栈, 默认不显示
* `--qt-support`: 指定被调试程序使用的Qt框架, 默认为`pyqt5`; 可选值为`pyqt5`, `pyside2`, `pyqt6`, `pyside6`.
* `--file`: 指定被调试程序的Python源代码文件路径
* `file_args`: 被调试程序启动的命令行参数

以调试[`PyQt-Fluent-Widgets`][1]为例, 其demo可使用`python examples/gallery/demo.py`来运行程序,
此时可以使用`python -m PyQtInspect --direct --file examples/gallery/demo.py`以直接模式启动PyQtInspect调试器.

> 注: 当使用PyCharm等使用pydevd调试器的IDE进行调试时, **务必保证IDE中的['PyQt compatible'选项][4]设置为项目使用的Qt框架**, 否则可能会导致PyQtInspect无法正常工作乃至程序崩溃.

### 3.3 分离模式启动 (传统方法, 一对多调试) { #detached-mode }

通过分离模式调试时, 务必**先启动GUI服务端，再启动被调试的Python程序**.

#### 3.3.1 启动调试端 (服务端)

在终端上输入`pqi-server`即可启动服务端GUI程序。启动后，指定监听端口(默认为`19394`)并点击`Serve`按钮启动服务端。

<img alt="start_server.png" height="600" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/start_server.png?raw=true"/>

#### 3.3.2 启动被调试端 (客户端): 运行程序源代码时附加PyQtInspect

前提: 需要使用者拥有被调试程序的Python源代码.

类似直接模式, 如果你是通过`python xxx.py param1 param2`来运行你的**PyQt5**程序, 则仅需在`python`和`xxx.py`中间加入`-m PyQtInspect --file`参数,
即`python -m PyQtInspect --file xxx.py param1 param2`, 即可启动PyQtInspect调试.

类似地, 如果被调试程序使用的是**PySide2/PyQt6/Pyside6**, 同样**需要额外添加`--qt-support`参数**, 以指定对应的Qt框架.
举个例子, 如被调试程序使用的是PySide2, 此时的启动命令为`python -m PyQtInspect --qt-support=pyside2 --file xxx.py param1 param2`.

分离模式下, 完整的启动命令为:

```powershell
python -m PyQtInspect [--port N] [--client hostname] [--multiprocess] [--show-pqi-stack] [--qt-support=[pyqt5|pyside2|pyqt6|pyside6]] --file py_file [file_args]
```

各参数的含义如下:

* `--port`: 指定服务端监听端口, 默认为`19394`
* `--client`: 指定服务端监听地址, 默认为`127.0.0.1`
* `--multiprocess`: 指定支持**多进程调试**, 默认不启用
* `--show-pqi-stack`: 指定显示和PyQtInspect相关的调用栈, 默认不显示
* `--qt-support`: 指定被调试程序使用的Qt框架, 默认为`pyqt5`; 可选值为`pyqt5`, `pyside2`, `pyqt6`, `pyside6`.
* `--file`: 指定被调试程序的Python源代码文件路径
* `file_args`: 被调试程序启动的命令行参数

同样以调试[`PyQt-Fluent-Widgets`][1]为例,
如果当前GUI调试端已在本机启动(监听地址为默认值`127.0.0.1`)并监听了`19394`端口(默认值),
我们可以使用`python -m PyQtInspect --file examples/gallery/demo.py`启动被调试端. 
(因为在该例子中, 服务端的地址和端口均为默认值, 所以不需要额外指定`--client`和`--port`参数)

> 注: 当使用PyCharm等使用pydevd调试器的IDE进行调试时, 务必保证IDE中的['PyQt compatible'选项][4]设置为项目使用的Qt框架, 否则可能会导致PyQtInspect无法正常工作乃至程序崩溃.

### 3.4 其他运行方式

#### 3.4.1 在PyCharm等IDE上运行PyQtInspect (支持分离模式/直接模式) { #run-pyqtinspect-in-pycharm-and-other-ides }

直接在PyCharm调试PyQtInspect Module即可, 不影响对程序的调试.

还是以[`PyQt-Fluent-Widgets`][1]为例, 可以新增一个Debug配置, 参数如下:

<img alt="pycharm config" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/pycharm_config.png?raw=true"/>

然后直接Run/Debug即可.

#### 3.4.2 Attach进程(仅支持分离模式, 目前不稳定) { #attach-to-process }

如果**没有被调试程序的源代码,** 可以通过Attach进程的方式**尝试**启动PyQtInspect客户端.

点击`More->Attach To Process`打开Attach窗口, 选择被调试程序的进程窗口, 点击Attach按钮即可. 

**注意**: 对于大多数控件而言, 此时是**拿不到它们创造时的调用栈信息**, 除非是Attach后创建的.

![attach process](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/attach_process.gif?raw=true)

## 4. 使用方式

### 4.1 选择元素

点击Select按钮即可选择元素, 将鼠标hover到需要检查的控件上, 高亮控件的同时亦可预览控件的简要信息(类名, 对象名, 大小, 相对位置, 样式等等).

单击鼠标左键后可选中该控件. 此时可以对控件进行更详细的检查, 比如查看并定位其初始化时的调用栈、在内部执行代码、查看层次信息、控件树定位以及查看属性等操作.

![hover and inspect](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/select_and_click.gif?raw=true)

### 4.2 查看控件的属性

控件简要信息区下方的第二个选项卡页展示了该控件的详细属性信息, 按控件类继承关系和属性的类型进行层次化展示.

<img alt="detailed_props" src="https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/detailed_props.png?raw=true" width="350"/>

### 4.3 查看控件初始化时的调用栈

控件简要信息区下方的第一个选项卡页展示了该控件初始化时的调用栈，双击可以拉起PyCharm定位到对应的文件和行.

![create stacks](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/create_stack.gif?raw=true)

如果拉起PyCharm失败, 可以在More->Settings中设置PyCharm的路径.

**p.s. 对于通过[Attach进程方式](#attach-to-process)启动的PyQtInspect客户端, 如果Attach过程中控件已经创建好了, 此时是拿不到创建时的信息, 调用栈信息为空**

### 4.4 执行代码

控件选中后, 点击Run Code按钮, 可在所选控件的作用域内执行代码(其中控件实例为`self`, 本质就是在控件对象内部的一个方法内执行代码).

![run code](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/run_code.gif?raw=true)

### 4.5 查看层次信息

工具最下方为层次关系导航条, 可以查看、高亮、定位所选控件的祖先控件和子控件, 方便使用者在控件的层次中来回切换.
因此，结合已有的鼠标选择功能，用户可做到更精细的选择。

![inspect hierarchy](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/inspect_hierarchy.gif?raw=true)

### 4.6 选择过程中, 使用右键点击模拟左键点击

_(默认打开, 需要关闭请前往 More->Mock Right Button Down as Left When Selecting Elements 取消)_

由于一些控件需要左键点击后才能显示, 为了方便选择, 可以通过右键点击的方式模拟左键点击.

**p.s. 该功能仅当选择过程中开启.**

![mock right button as left](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/mock_right_btn_as_left.gif?raw=true)

### 4.7 F8强力选中 

_(默认打开, 需要关闭请前往 More->Press F8 to Finish Selecting 取消)_

对于一些很难通过鼠标点击选中的控件, 可以通过F8完成选中. 注意, F8仅用于结束选择, 在未开启选择的情况下按F8并不会开启选择.

### 4.8 控件树查看

点击菜单上的 `View->Control Tree`, 可以查看当前所选控件所在进程的控件树结构.
单击(或者hover)树中的行可以高亮对应的控件.

![control tree](https://github.com/JezaChen/PyQtInspect-README-Assets/blob/main/Images/0.4.0/control_tree.gif?raw=true)

## 5. 已知问题

- **多继承两个以上的PyQt类会patch失效**, 例如`class A(B, C)`的情况, 其中`B`和`C`继承于`QObject`, 这样可能会导致`C`的`__init__`方法无法被执行, 从而引发异常.
  > [PyQt作者曾提醒过不要多继承两个以上的PyQt类][2], 因为这样也会容易导致PyQt自身行为异常

- PySide6无法选中一些控件

- 对于一部分电脑, 有时候`QEnterEvent`的`type`会为`170`(`QEvent.DynamicPropertyChange`), 当程序访问`propertyNames`时会引发异常.

## 6. 更新日志

### 0.4.0

- 新增控件详细属性选项卡页
- 在Toolbar上新增打开日志和清空日志入口
- 修复一系列问题

[1]: https://github.com/zhiyiYo/PyQt-Fluent-Widgets
[2]: https://www.riverbankcomputing.com/pipermail/pyqt/2017-January/038650.html
[3]: https://pypi.org/project/PyQtInspect/#files
[4]: https://www.jetbrains.com/help/pycharm/debugger-python.html
[5]: https://github.com/JezaChen/ihook
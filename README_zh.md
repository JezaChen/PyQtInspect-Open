<div style="text-align: center;"><h1>PyQtInspect</h1></div>
<div style="text-align: center;">像Chrome元素检查工具一样检查PyQt/PySide程序元素</div>

对于使用Qt Widgets编写的PyQt/PySide程序, 如果界面并非通过QtDesigner生成, 
我们查看程序中的控件信息、定位控件代码等操作是非常困难的, 很难像Chrome/Firefox浏览器那般轻松查看HTML的元素信息.
本项目旨在解决这个问题, 提供一个类似Chrome元素检查工具的PyQt/PySide程序元素检查工具.

## 要求

- Python 3.7+
- 安装有以下Qt for Python的框架: PyQt5/PySide2/PyQt6/Pyside6

## 安装

使用`pip install PyQtInspect`安装即可.

## 启动方式

`PyQtInspect`架构分为两部分: 

- 调试端/服务端: GUI程序，供使用者查看元素信息、定位代码等;

- 被调试端/客户端: 运行在被调试的Python程序中，patch宿主程序的Python Qt框架, 将宿主程序的信息传递给GUI服务端等.

调试时, 需要先启动GUI服务端，再启动被调试的Python程序.

### 启动调试端

直接在终端上输入`pqi-server`即可启动服务端GUI程序。启动后，指定监听端口(默认为19394)并点击`Serve`按钮启动服务端。

<img alt="start_server.png" height="600" src="README_Assets/start_server.png"/>

### 启动被调试端

#### 1. 运行程序python源代码时附带PyQtInspect

目前**推荐**的启动方法, 需要使用者拥有被调试程序的Python源代码.

如果平时通过`python xxx.py param1 param2`运行程序, 则仅需要在`python`和`xxx.py`中间加入`-m PyQtInspect --file`参数,
如`python -m PyQtInspect --file xxx.py param1 param2`, 即可启动PyQtInspect客户端.

完整的启动命令为:

```powershell
python -m PyQtInspect [--port N] [--client hostname] [--multiprocess] [--show-pqi-stack] [--qt-support=[pyqt5|pyside2|pyqt6|pyside6]] --file executable_file [file_args]
```

每个参数的含义如下:

* `--port`: 指定服务端监听端口, 默认为`19394`
* `--client`: 指定服务端监听地址, 默认为`127.0.0.1`
* `--multiprocess`: 指定是否支持**多进程调试**, 默认不启用
* `--show-pqi-stack`: 指定是否显示和PyQtInspect相关的调用栈, 默认不显示
* `--qt-support`: 指定被调试程序使用的Qt框架, 默认为`pyqt5`
* `--file`: 指定被调试程序的Python源代码文件路径
* `file_args`: 被调试程序启动的命令行参数

以调试[`PyQt-Fluent-Widgets`][1]为例, 其demo一般可使用`python examples/gallery/demo.py`来运行程序,
此时可以使用`python -m PyQtInspect --file examples/gallery/demo.py`来启动PyQtInspect客户端.

#### 2. 用在PyCharm上

直接在PyCharm调试PyQtInspect Module即可, 不影响对程序的调试.

还是以[`PyQt-Fluent-Widgets`][1]为例, 可以新增一个Debug配置, 参数如下:

<img alt="pycharm config" src="README_Assets/pycharm_config.png"/>

然后直接Run/Debug即可.

#### 3. Attach进程(目前不稳定)

如果没有被调试程序的源代码, 可以通过Attach进程的方式**尝试**启动PyQtInspect客户端.

点击`More->Attach To Process`, 选择被调试程序的进程窗口, 点击Attach按钮即可. 

**注意**: 此时对于大多数控件是**拿不到创造时的调用栈信息**, 除非是Attach后创建的.

![attach process](README_Assets/attach_process.gif)

## 使用方式

### 检查元素信息

点击Inspect按钮, 将鼠标hover到需要检查的控件上, 即可预览控件的信息.

![hover and inspect](README_Assets/hover_and_inspect.gif)

如果需要选中该控件, 单击鼠标左键, 以完成选中. 此时可以对控件进行创建时调用栈定位、执行代码、查看层次信息等操作.

![then click](README_Assets/then_click.gif)

### 调用栈定位

控件信息区下方是创建该控件时的调用栈，点击可以拉起Pycharm定位到对应的文件和行.

![create stacks](README_Assets/create_stacks.gif)

如果拉起Pycharm失败, 可以在More->Settings中设置Pycharm的路径.

**p.s.对于通过Attach进程方式启动的PyQtInspect客户端, 如果Attach过程中控件已经创建好了, 此时是拿不到创建时的信息的, 该调用栈区域为空**

### 执行代码

控件选中后, 点击Run Code按钮, 可在选中控件的作用域内执行代码(其中选中控件实例为`self`, 实际上就是在控件的一个方法内执行代码).

![run codes](README_Assets/run_codes.gif)

### 查看层次信息

工具下方有层次关系导航条, 可以直接查看、高亮、定位选中控件的祖先控件和子控件, 方便使用者在控件的层次中来回切换.
因此，结合已有的鼠标选中，用户可做到更精细的选择。

![inspect hierachy](README_Assets/inspect_hierarchy.gif)

### 检查过程中, 使用右键点击模拟左键点击(默认打开, 需要关闭前往 More->Mock Right Button Down as Left取消)

由于一些控件需要左键点击后才能显示, 为了方便检查, 可以通过右键点击模拟左键点击.

![mock right button as left](README_Assets/mock_right_btn_as_left.gif)

### F8强力选中(默认打开, 需要关闭前往 More->Press F8 to Finish Inspect取消)

对于一些很难通过鼠标点击选中的控件, 可以通过F8完成选中. 注意, F8仅用于检查过程中的结束选中, 在未开启检查的情况下按F8并不会开启选中.

## 已知问题

- **多继承两个以上的PyQt类会patch失效**, 例如`class A(B, C)`的情况, 其中`B`和`C`继承于`QObject`, 这样可能会导致`C`的`__init__`方法无法被执行, 从而引发异常.
  > [PyQt作者曾提醒过不要多继承两个以上的PyQt类][2], 因为这样也会容易导致PyQt自身行为异常

- PySide6无法选中一些控件

## 源代码

目前可以在PyPi上直接下载源代码分布包(Source Distribution), Github仓库即将开放.

[1]: https://github.com/zhiyiYo/PyQt-Fluent-Widgets
[2]: https://www.riverbankcomputing.com/pipermail/pyqt/2017-January/038650.html

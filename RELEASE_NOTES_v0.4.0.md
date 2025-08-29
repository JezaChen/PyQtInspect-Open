# PyQtInspect v0.4.0 Release Notes

## What's New in v0.4.0

PyQtInspect v0.4.0 introduces significant enhancements to help you inspect and debug PyQt/PySide applications more effectively.

### 🆕 New Features

#### Properties Tab
- **Widget Properties Inspector**: A new "Properties" tab has been added to the main interface
- **Comprehensive Property Display**: View all widget properties in an organized tree structure
- **Real-time Property Values**: See current property values for the selected widget
- **Class Hierarchy**: Properties are organized by class inheritance for better understanding

#### Enhanced Toolbar
- **Log Management**: New toolbar entries to open and clear logs
- **Improved Workflow**: Quick access to essential debugging tools
- **Better User Experience**: Streamlined interface for common operations

### 🐛 Bug Fixes

- **Python 3.8 + PySide Compatibility**: Removed early return that was causing issues with Python 3.8 and PySide combinations
- **Various Stability Improvements**: Fixed a series of issues improving overall reliability
- **Enhanced Error Handling**: Better error management for edge cases

### 🔧 Technical Improvements

- **Property Fetcher System**: New widget properties fetcher with support for various Qt widget types including:
  - QTabWidget, QStackedWidget, QMdiArea
  - QComboBox, QGraphicsView
  - Standard widget properties (geometry, style, behavior)
- **Type Representation**: Enhanced type representation system for enums, flags, and ordinary types
- **Cross-platform Support**: Continued support for Windows, macOS, and Linux

### 📋 Features from Previous Versions

This release builds upon:
- **Control Tree View**: Visualize widget hierarchy (from v0.3.10)
- **Direct and Detached Modes**: Flexible debugging approaches
- **PyCharm Integration**: Double-click to navigate to source code
- **Force Selection**: F8 key for difficult-to-select widgets
- **Right-click Simulation**: Bypass context menus while selecting

## Installation

```bash
pip install PyQtInspect==0.4.0
```

## Usage

### Quick Start (Direct Mode - Recommended)
```python
import PyQtInspect
PyQtInspect.patch()  # Add this line to your PyQt/PySide application
```

### Detached Mode
1. Start the server: `pqi-server`
2. Add to your application:
```python
import PyQtInspect
PyQtInspect.patch(host='127.0.0.1', port=19394)
```

## Compatibility

- **Python**: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Qt Frameworks**: PyQt5, PyQt6, PySide2, PySide6
- **Operating Systems**: Windows, macOS, Linux

## Known Issues

- Patching may fail with multiple inheritance involving more than two PyQt classes
- Some controls may not be selectable in PyQt6
- On some systems, `QEnterEvent` type conflicts may cause crashes

## Links

- **Repository**: https://github.com/JezaChen/PyQtInspect-Open
- **PyPI**: https://pypi.org/project/PyQtInspect/
- **Documentation**: https://jeza-chen.com/PyqtInspect

---

Thank you for using PyQtInspect! For bug reports and feature requests, please visit our [GitHub repository](https://github.com/JezaChen/PyQtInspect-Open/issues).
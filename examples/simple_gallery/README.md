# Simple Gallery Example for Testing PyQtInspect

## How to run

Run the gallery:

```pwsh
py run_dialog.py [pyqt5|pyqt6|pyside2|pyside6]
```

Run with PyQtInspect (direct mode):

```pwsh
py -m PyQtInspect --direct --multiprocess --file run_dialog.py [pyqt5|pyqt6|pyside2|pyside6]
```

## Testing multiprocess support

Click the first button in the `Buttons` tab to launch a new gallery instance using a different Qt binding.

- PyQt5 → PyQt6
- PyQt6 → PySide6
- PySide6 → PyQt5

Note: PySide2 is not supported on recent Python versions.

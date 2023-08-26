# PQI Structures

import dataclasses


@dataclasses.dataclass
class QWidgetInfo:
    """A dataclass for storing information about a QWidget."""
    # Class name of the QWidget.
    class_name: str

    # The object name of the QWidget.
    object_name: str

    # The stack of the QWidget when it was created.
    stacks_when_create: list

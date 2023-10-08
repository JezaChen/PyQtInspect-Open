# PQI Structures

import dataclasses


@dataclasses.dataclass
class QWidgetInfo:
    """A dataclass for storing information about a QWidget."""
    # Class name of the QWidget.
    class_name: str

    # The object name of the QWidget.
    object_name: str

    # The id of the QWidget.
    id: int

    # The stack of the QWidget when it was created.
    stacks_when_create: list

    # The size of the QWidget.
    size: tuple

    # The position of the QWidget.
    pos: tuple

    # The parent classes of the QWidget.
    parent_classes: list

    # The id of all parents of the QWidget.
    parent_ids: list

    # The stylesheet of the QWidget.
    stylesheet: str

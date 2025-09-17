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

    # === PARENTS ===
    # Split into two lists to reduce the size of the JSON payload.
    # TODO: Evaluate using nested dataclasses or namedtuples.
    # The parent classes of the QWidget.
    parent_classes: list

    # The id of all parents of the QWidget.
    parent_ids: list

    # The object name of all parents of the QWidget.
    parent_object_names: list

    # The stylesheet of the QWidget.
    stylesheet: str

    # extra data from sender
    extra: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class QWidgetChildrenInfo:
    """A dataclass for storing information about a QWidget's ancestor."""
    widget_id: int

    child_classes: list

    child_ids: list

    child_object_names: list

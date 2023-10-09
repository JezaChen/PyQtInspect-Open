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
    # 之所以拆分成两个列表, 是为了减少传输的JSON数据量
    # TODO: 评估下, 使用嵌套dataclass? namedtuple?
    # The parent classes of the QWidget.
    parent_classes: list

    # The id of all parents of the QWidget.
    parent_ids: list

    # The object name of all parents of the QWidget.
    parent_object_names: list

    # The stylesheet of the QWidget.
    stylesheet: str

    # The children of the QWidget.
    children: list

    # extra data from sender
    extra: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class QWidgetChildrenInfo:
    """A dataclass for storing information about a QWidget's ancestor."""
    ancestor_classes: list

    ancestor_ids: list

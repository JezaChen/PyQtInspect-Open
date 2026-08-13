from PyQtInspect._pqi_bundle.monkey_qt.widget_utils import (
    get_widget_visual_rect,
    get_widget_window_pos,
)


class _Point:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y


class _Rect:
    @staticmethod
    def topLeft():
        return _Point(0, 0)


class _Size:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    def width(self):
        return self._width

    def height(self):
        return self._height


class _Widget:
    def __init__(self, x, y):
        self._window = object()
        self._position = _Point(x, y)

    @staticmethod
    def rect():
        return _Rect()

    def window(self):
        return self._window

    def pos(self):
        return self._position

    def mapTo(self, target, point):
        assert target is self._window
        return _Point(
            self._position.x() + point.x(),
            self._position.y() + point.y(),
        )


def test_get_widget_window_pos_maps_widget_origin():
    widget = _Widget(12, 34)

    assert get_widget_window_pos(widget) == (12, 34)


class _VisualWidget:
    def __init__(self, x, y, width, height, parent=None, is_window=False):
        self._global_position = _Point(x, y)
        self._size = _Size(width, height)
        self._parent = parent
        self._is_window = is_window

    def rect(self):
        return _Rect()

    def mapToGlobal(self, point):
        return _Point(
            self._global_position.x() + point.x(),
            self._global_position.y() + point.y(),
        )

    def size(self):
        return self._size

    def parentWidget(self):
        return self._parent

    def isWindow(self):
        return self._is_window

    def shadow_methods(self):
        self.rect = None
        self.mapToGlobal = None
        self.size = None
        self.parentWidget = None
        self.isWindow = None


def test_get_widget_visual_rect_does_not_clip_window_to_its_owner():
    owner = _VisualWidget(100, 100, 200, 200, is_window=True)
    window = _VisualWidget(350, 350, 100, 80, parent=owner, is_window=True)

    assert get_widget_visual_rect(window) == (350, 350, 100, 80)


def test_get_widget_visual_rect_handles_shadowed_widget_methods():
    parent = _VisualWidget(100, 100, 80, 60, is_window=True)
    child = _VisualWidget(90, 80, 100, 100, parent=parent)
    parent.shadow_methods()
    child.shadow_methods()

    assert get_widget_visual_rect(child) == (100, 100, 80, 60)

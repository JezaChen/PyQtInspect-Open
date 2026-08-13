from PyQtInspect._pqi_bundle.monkey_qt.metadata import _PQI_STACK_WHEN_CREATED_ATTR
from PyQtInspect._pqi_bundle.monkey_qt.widget_creation_stack import (
    FrameInfo,
    capture_current_stack,
    get_widget_creation_stack,
)


def test_capture_current_stack_returns_frame_info():
    frames = capture_current_stack()

    assert frames
    assert isinstance(frames[0], FrameInfo)
    assert frames[0].func_name == 'capture_current_stack'


def test_get_widget_creation_stack_skips_capture_and_patch_frames():
    from PyQtInspect.pqi import SetupHolder

    original_setup = SetupHolder.setup
    SetupHolder.setup = {
        SetupHolder.KEY_STACK_MAX_DEPTH: 0,
        SetupHolder.KEY_SHOW_PQI_STACK: True,
    }

    class Widget:
        pass

    widget = Widget()
    setattr(
        widget,
        _PQI_STACK_WHEN_CREATED_ATTR,
        [
            FrameInfo('capture.py', 10, 'capture_current_stack'),
            FrameInfo('patcher.py', 20, '_new_QWidget_init'),
            FrameInfo('application.py', 30, 'create_widget'),
        ],
    )

    try:
        assert get_widget_creation_stack(widget) == [
            {
                'filename': 'application.py',
                'lineno': 30,
                'function': 'create_widget',
            }
        ]
    finally:
        SetupHolder.setup = original_setup

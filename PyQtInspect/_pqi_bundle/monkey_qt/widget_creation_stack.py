"""Capture and expose widget creation stacks."""

# Thanks to Charles Machalow
# https://gist.github.com/csm10495/39dde7add5f1b1e73c4e8299f5df1116

import inspect
import sys
import typing

from PyQtInspect._pqi_bundle.monkey_qt.metadata import _PQI_STACK_WHEN_CREATED_ATTR
from PyQtInspect._pqi_bundle.pqi_path_helper import find_pqi_module_path, is_relative_to


class FrameInfo(typing.NamedTuple):
    """ The information of a frame in the stack. """
    filename: str
    line_no: int
    func_name: str


def capture_current_stack(use_get_frame=True) -> typing.List[FrameInfo]:
    """
    Brief:
        Gets a stack frame with the passed in num on the stack.
            If use_get_frame, uses sys._getframe (implementation detail of Cython)
                Otherwise or if sys._getframe is missing, uses inspect.stack() (which is really slow).
    Update:
        - 20240820: We CANNOT Store the raw frame object outputted by `sys.getframe()`
            because it will cause memory leak. We should store the information we need.
    """
    # Not all versions of python have the sys._getframe() method.
    # All should have inspect, though it is really slow
    if use_get_frame and hasattr(sys, '_getframe'):
        frame = sys._getframe(0)
        frames = [
            FrameInfo(
                filename=frame.f_code.co_filename,
                line_no=frame.f_lineno,
                func_name=frame.f_code.co_name
            )
        ]  # Capture the line number while constructing the stack; otherwise later f_lineno values point to the last line.

        while frame.f_back is not None:
            frames.append(
                FrameInfo(
                    filename=frame.f_back.f_code.co_filename,
                    line_no=frame.f_back.f_lineno,
                    func_name=frame.f_back.f_code.co_name
                )
            )
            frame = frame.f_back

        return frames
    return [FrameInfo(*frame[1:4]) for frame in inspect.stack()]


def _filter_stack(frames):
    from PyQtInspect.pqi import SetupHolder

    filtered_frames = []
    stack_max_depth = SetupHolder.setup[SetupHolder.KEY_STACK_MAX_DEPTH]
    show_pqi_stack = SetupHolder.setup[SetupHolder.KEY_SHOW_PQI_STACK]
    pqi_module_path = find_pqi_module_path()
    frames = frames[2:stack_max_depth + 1] if stack_max_depth != 0 else frames[2:]
    for filename, line_no, func_name in frames:
        if not show_pqi_stack and is_relative_to(filename, pqi_module_path):
            break
        filtered_frames.append(
            {
                'filename': filename,
                'lineno': line_no,
                'function': func_name,
            }
        )
    return filtered_frames


def get_widget_creation_stack(widget):
    frames = getattr(widget, _PQI_STACK_WHEN_CREATED_ATTR, [])
    return _filter_stack(frames)

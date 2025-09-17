# -*- encoding:utf-8 -*-
# Thanks to Charles Machalow
# https://gist.github.com/csm10495/39dde7add5f1b1e73c4e8299f5df1116

import sys
import inspect
import typing


class FrameInfo(typing.NamedTuple):
    """ The information of a frame in the stack. """
    filename: str
    line_no: int
    func_name: str


def getStackFrame(useGetFrame=True) -> typing.List[FrameInfo]:
    """
    Brief:
        Gets a stack frame with the passed in num on the stack.
            If useGetFrame, uses sys._getframe (implementation detail of Cython)
                Otherwise or if sys._getframe is missing, uses inspect.stack() (which is really slow).
    Update:
        - 20240820: We CANNOT Store the raw frame object outputted by `sys.getframe()`
            because it will cause memory leak. We should store the information we need.
    """
    # Not all versions of python have the sys._getframe() method.
    # All should have inspect, though it is really slow
    if useGetFrame and hasattr(sys, '_getframe'):
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

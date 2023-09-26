# -*- encoding:utf-8 -*-
# Thanks to Charles Machalow
# https://gist.github.com/csm10495/39dde7add5f1b1e73c4e8299f5df1116

import sys
import inspect


def getFrameLineNo(frame):
    return frame.f_lineno


def getStackFrame(useGetFrame=True):
    '''
    Brief:
        Gets a stack frame with the passed in num on the stack.
            If useGetFrame, uses sys._getframe (implementation detail of Cython)
                Otherwise or if sys._getframe is missing, uses inspect.stack() (which is really slow).
    '''
    # Not all versions of python have the sys._getframe() method.
    # All should have inspect, though it is really slow
    if useGetFrame and hasattr(sys, '_getframe'):
        frame = sys._getframe(0)
        frames = [(frame, frame.f_lineno),]  # 需要在创建期间获取stack就捕获行号, 否则后续的f_lineno会走到最后一行去

        while frame.f_back is not None:
            frames.append((frame.f_back, frame.f_back.f_lineno))
            frame = frame.f_back

        return frames
    else:
        return inspect.stack()

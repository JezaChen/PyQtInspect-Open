# -*- encoding:utf-8 -*-
# Thanks to Charles Machalow
# https://gist.github.com/csm10495/39dde7add5f1b1e73c4e8299f5df1116

import sys
import inspect


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
        frames = [frame]

        while frame.f_back is not None:
            frames.append(frame.f_back)
            frame = frame.f_back

        return frames
    else:
        return inspect.stack()

# -*- encoding:utf-8 -*-
import inspect


def filter_trace_stack(traceStacks):
    filteredStacks = []
    from PyQtInspect.pqi import SetupHolder
    stackMaxDepth = SetupHolder.setup["stack-max-depth"]
    stacks = traceStacks[2:stackMaxDepth + 1] if stackMaxDepth != 0 else traceStacks[2:]
    for frame, lineno in stacks:
        filteredStacks.append(
            {
                'filename': inspect.getsourcefile(frame),
                'lineno': lineno,
                'function': frame.f_code.co_name,
            }
        )
    return filteredStacks

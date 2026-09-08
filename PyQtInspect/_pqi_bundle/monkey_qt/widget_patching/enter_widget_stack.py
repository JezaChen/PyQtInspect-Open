from PyQtInspect._pqi_bundle.monkey_qt.shared.shared_api import QObjectInspectAPI


class EnteredWidgetStack:
    def __init__(self):
        self._stack = []

    def push(self, widget):
        self._stack.append(widget)

    def pop(self):
        self._stack.pop()

    def filter(self):
        while self._stack:
            wgt = self._stack[-1]
            if QObjectInspectAPI.instance().isdeleted(wgt):
                self._stack.pop()
            else:
                break

    def clear(self):
        self._stack.clear()

    def __bool__(self):
        return bool(self._stack)

    def __getitem__(self, item):
        return self._stack[item]

    def __len__(self):
        return len(self._stack)

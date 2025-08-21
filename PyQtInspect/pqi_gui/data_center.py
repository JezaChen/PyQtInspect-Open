import enum

_DEFAULT_HOST = '127.0.0.1'
_DEFAULT_PORT = 19394


class RunningState(enum.Enum):
    NOT_STARTED = enum.auto()
    IDLE = enum.auto()
    INSPECTING = enum.auto()


class PQIServerGUIDataCenter:
    def __init__(self):
        self._serverConfig = {}
        self._curRunningState = RunningState.NOT_STARTED
        self._lastInspectedWidgetId = -1
        self._inspectingWidgetId = -1

    def setServerConfig(self, config: dict):
        self._serverConfig = config

    @property
    def host(self):
        return self._serverConfig.get('host', _DEFAULT_HOST)

    @property
    def port(self):
        return self._serverConfig.get('port', _DEFAULT_PORT)

    @property
    def runningState(self):
        return self._curRunningState

    @runningState.setter
    def runningState(self, state: RunningState):
        self._curRunningState = state


instance = PQIServerGUIDataCenter()

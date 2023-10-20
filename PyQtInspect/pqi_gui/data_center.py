_DEFAULT_HOST = '127.0.0.1'
_DEFAULT_PORT = 19394


class PQIServerGUIDataCenter:
    def __init__(self):
        self._serverConfig = {}

    def setServerConfig(self, config: dict):
        self._serverConfig = config

    @property
    def host(self):
        return self._serverConfig.get('host', _DEFAULT_HOST)

    @property
    def port(self):
        return self._serverConfig.get('port', _DEFAULT_PORT)


instance = PQIServerGUIDataCenter()

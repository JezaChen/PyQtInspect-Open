import abc


class Setup(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def setup():
        """ Set up platform-specific configurations. """
        pass


class DummySetup(Setup):
    @staticmethod
    def setup():
        """ Dummy setup for unsupported platforms. """
        pass

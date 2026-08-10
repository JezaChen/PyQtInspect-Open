from contextlib import contextmanager


def _random_suffix() -> str:
    import uuid
    return f'_{uuid.uuid4().hex[:6]}'


_SUFFIX = _random_suffix()

# Marks
_PQI_MOCKED_EVENT_ATTR = f'_pqi_mocked{_SUFFIX}'
_PQI_INSPECTED_PROP_NAME = f'_pqi_inspected{_SUFFIX}'
_PQI_INSPECTED_PROP_NAME_BYTES = bytes(_PQI_INSPECTED_PROP_NAME, 'utf-8')
_PQI_WIDGET_INSPECTED_MARK = f'_pqi_inspected_mark{_SUFFIX}'

# Highlight foreground widget name
_PQI_HIGHLIGHT_FG_NAME = f'_pqi_highlight_fg{_SUFFIX}'

# Create stack
_PQI_STACK_WHEN_CREATED_ATTR = f'_pqi_stack_when_created{_SUFFIX}'

# Event custom attrs
_PQI_CUSTOM_EVENT_IS_ENTER_ATTR = '_pqi_is_enter'
_PQI_CUSTOM_EVENT_IS_HIGHLIGHT_ATTR = '_pqi_is_highlight'
_PQI_CUSTOM_EVENT_EXEC_CODE_ATTR = '_pqi_exec_code'
_PQI_CUSTOM_EVENT_DISABLE_INSPECT_ATTR = '_pqi_disable_inspect'

_MISSING_MARK = object()


class PatchMark:
    """
    Base class for temporarily marking classes or instances.

    Subclasses must define a non-empty ``_mark`` attribute.
    """
    _mark = None

    @classmethod
    def _mark_name(cls):
        if not isinstance(cls._mark, str) or not cls._mark:
            raise NotImplementedError(f'{cls.__name__} must define a non-empty _mark attribute')
        return cls._mark

    @classmethod
    def _own_mark(cls, target):
        """Return the target's own mark, excluding inherited class marks."""
        try:
            return vars(target).get(cls._mark_name(), _MISSING_MARK)
        except TypeError:
            return _MISSING_MARK

    @classmethod
    def mark(cls, *targets):
        """
        Mark the given targets.
        :param targets: The classes or instances to mark.
        """
        mark_name = cls._mark_name()
        for target in targets:
            setattr(target, mark_name, True)

    @classmethod
    def is_marked(cls, target) -> bool:
        """
        Check whether a target or its class is marked.
        :param target: The class or instance to check.
        :return: True if marked, False otherwise.
        """
        mark_name = cls._mark_name()
        return (
            getattr(target, mark_name, False) or
            getattr(target.__class__, mark_name, False)
        )

    @classmethod
    def unmark(cls, *targets):
        """
        Remove this mark from the given targets.
        :param targets: The classes or instances to unmark.
        """
        mark_name = cls._mark_name()
        for target in targets:
            if cls._own_mark(target) is not _MISSING_MARK:
                delattr(target, mark_name)

    @classmethod
    @contextmanager
    def marked(cls, *targets):
        """
        Temporarily mark targets, restoring their original state on exit.
        :param targets: The classes or instances to mark temporarily.
        """
        mark_name = cls._mark_name()
        previous_marks = []
        try:
            for target in targets:
                previous_marks.append(
                    (target, cls._own_mark(target))
                )
                setattr(target, mark_name, True)
            yield
        finally:
            for target, previous_mark in reversed(previous_marks):
                if previous_mark is _MISSING_MARK:
                    cls.unmark(target)
                else:
                    setattr(target, mark_name, previous_mark)


class SuppressPatchMark(PatchMark):
    _mark = f'_pqi_suppress_patch{_SUFFIX}'

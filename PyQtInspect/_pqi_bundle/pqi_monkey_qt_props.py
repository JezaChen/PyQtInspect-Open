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

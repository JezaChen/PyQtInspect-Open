# -*- encoding:utf-8 -*-

import dataclasses
import json
import threading
import typing
from urllib.parse import quote

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle.pqi_structures import (
    QWidgetChildrenInfo,
    QWidgetInfo,
)
from PyQtInspect._pqi_bundle.pqi_typing import OptionalDict

from .protocol import (
    CMD_CHILDREN_INFO,
    CMD_CONTROL_TREE,
    CMD_DISABLE_INSPECT,
    CMD_ENABLE_INSPECT,
    CMD_EXEC_CODE,
    CMD_EXEC_CODE_ERROR,
    CMD_EXEC_CODE_RESULT,
    CMD_EXIT,
    CMD_INSPECT_FINISHED,
    CMD_REQ_CHILDREN_INFO,
    CMD_REQ_CONTROL_TREE,
    CMD_REQ_WIDGET_INFO,
    CMD_REQ_WIDGET_PROPS,
    CMD_SELECT_WIDGET,
    CMD_SETTINGS_CHANGED,
    CMD_SET_WIDGET_HIGHLIGHT,
    CMD_WIDGET_INFO,
    CMD_WIDGET_PROPS,
    ID_TO_MEANING,
    TreeViewResultKeys,
)


class NetCommand:
    """A command received from or sent to the peer."""

    next_seq = 0

    # Protocol where each line is a new message (text is quoted to prevent
    # embedded newlines).
    QUOTED_LINE_PROTOCOL = 'quoted-line'

    # Uses HTTP framing to provide a new message:
    # Content-Length:xxx\r\n\r\npayload
    HTTP_PROTOCOL = 'http'

    protocol = QUOTED_LINE_PROTOCOL
    _showing_debug_info = 0
    _show_debug_info_lock = threading.RLock()

    def __init__(self, cmd_id, seq, text):
        """
        Generate a sequence number when ``seq`` is zero; otherwise preserve
        the supplied response sequence.
        """
        self.id = cmd_id
        if seq == 0:
            NetCommand.next_seq += 2
            seq = NetCommand.next_seq
        self.seq = seq

        assert isinstance(text, str)

        self._show_debug_info(cmd_id, seq, text)

        if self.protocol == self.HTTP_PROTOCOL:
            msg = '%s\t%s\t%s\n' % (cmd_id, seq, text)
        else:
            encoded = quote(str(text), '/<>_=" \t')
            msg = '%s\t%s\t%s\n' % (cmd_id, seq, encoded)

        if isinstance(msg, str):
            msg = msg.encode('utf-8')
        assert isinstance(msg, bytes)
        self._as_bytes = msg

    def send(self, sock):
        as_bytes = self._as_bytes
        if self.protocol == self.HTTP_PROTOCOL:
            sock.sendall(
                ('Content-Length: %s\r\n\r\n' % len(as_bytes)).encode('ascii')
            )

        sock.sendall(as_bytes)

    @classmethod
    def _show_debug_info(cls, cmd_id, seq, text):
        pqi_log.debug(
            'sending cmd --> %20s %s' % (
                ID_TO_MEANING.get(str(cmd_id), 'UNKNOWN'),
                text.replace('\n', ' '),
            )
        )


class NetCommandFactory:
    def make_dict(self, **kwargs):
        return kwargs

    def _dump_json(self, obj):
        return json.dumps(obj, indent=None, separators=(',', ':'))

    def make_json(self, **kwargs):
        return self._dump_json(kwargs)

    def make_widget_info_message(self, widget_info: QWidgetInfo):
        return NetCommand(
            CMD_WIDGET_INFO,
            0,
            self.make_json(**dataclasses.asdict(widget_info)),
        )

    def make_exec_code_message(self, code: str):
        return NetCommand(CMD_EXEC_CODE, 0, code)

    def make_exec_code_result_message(self, result: str):
        return NetCommand(CMD_EXEC_CODE_RESULT, 0, result)

    def make_exec_code_err_message(self, err_msg: str):
        return NetCommand(CMD_EXEC_CODE_ERROR, 0, err_msg)

    def make_enable_inspect_message(self, extra: OptionalDict = None):
        if extra is None:
            extra = {}
        return NetCommand(CMD_ENABLE_INSPECT, 0, self._dump_json(extra))

    def make_disable_inspect_message(self):
        return NetCommand(CMD_DISABLE_INSPECT, 0, '')

    def make_inspect_finished_message(self):
        return NetCommand(CMD_INSPECT_FINISHED, 0, '')

    def make_set_widget_highlight_message(
            self,
            widget_id: int,
            is_highlight: bool,
    ):
        return NetCommand(
            CMD_SET_WIDGET_HIGHLIGHT,
            0,
            self.make_json(
                widget_id=widget_id,
                is_highlight=is_highlight,
            ),
        )

    def make_select_widget_message(self, widget_id: int):
        return NetCommand(CMD_SELECT_WIDGET, 0, str(widget_id))

    def make_req_widget_info_message(
            self,
            widget_id: int,
            extra: OptionalDict = None,
    ):
        if extra is None:
            extra = {}
        return NetCommand(
            CMD_REQ_WIDGET_INFO,
            0,
            self.make_json(
                widget_id=widget_id,
                extra=extra,
            ),
        )

    def make_req_children_info_message(self, widget_id: int):
        return NetCommand(CMD_REQ_CHILDREN_INFO, 0, str(widget_id))

    def make_children_info_message(
            self,
            children_info: QWidgetChildrenInfo,
    ):
        return NetCommand(
            CMD_CHILDREN_INFO,
            0,
            self.make_json(**dataclasses.asdict(children_info)),
        )

    def make_req_control_tree_message(self, extra: OptionalDict = None):
        if extra is None:
            extra = {}
        return NetCommand(CMD_REQ_CONTROL_TREE, 0, self._dump_json(extra))

    def make_control_tree_message(
            self,
            control_tree: typing.List[typing.Dict],
            extra: typing.Dict,
    ):
        return NetCommand(
            CMD_CONTROL_TREE,
            0,
            self._dump_json({
                TreeViewResultKeys.TREE_INFO_KEY: control_tree,
                TreeViewResultKeys.EXTRA_KEY: extra,
            }),
        )

    def make_req_widget_props_message(self, widget_id: int):
        return NetCommand(CMD_REQ_WIDGET_PROPS, 0, str(widget_id))

    def make_widget_props_message(
            self,
            widget_props: typing.List[typing.Dict],
    ):
        return NetCommand(
            CMD_WIDGET_PROPS,
            0,
            self._dump_json(widget_props),
        )

    def make_settings_changed_message(self, settings: dict):
        return NetCommand(
            CMD_SETTINGS_CHANGED,
            0,
            self._dump_json(settings),
        )

    def make_exit_message(self):
        return NetCommand(CMD_EXIT, 0, '')

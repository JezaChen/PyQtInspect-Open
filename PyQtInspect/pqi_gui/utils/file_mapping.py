# -*- encoding:utf-8 -*-
# todo 目前仅支持cc模板的路径映射

import re

_CC_TEMPLATE_ANCHORLIVE_PATTERN = re.compile(r'(?s:.*)\\anchorlive_r\d+\\anchorlive\\(?P<src>.*)')
_CC_TEMPLATE_GAMELIVE_PATTERN = re.compile(r'(?s:.*)\\gamelive_r\d+\\gamelive\\(?P<src>.*)')
_CC_TEMPLATE_COMMON_MODULE_PATTERN = re.compile(r'(?s:.*)\\common_module\\(?P<src>.*)')
_CC_TEMPLATE_OTHERS_PATTERN = re.compile(r'(?s:.*)\\pack_temp\\(?P<src>.*)')  # apps, appsmall

# 从前到后匹配，匹配成功则返回
_PATTERNS = [
    (_CC_TEMPLATE_ANCHORLIVE_PATTERN, r'\\transformer\\anchorlive\\\g<src>'),
    (_CC_TEMPLATE_GAMELIVE_PATTERN, r'\\transformer\\gamelive\\\g<src>'),
    (_CC_TEMPLATE_COMMON_MODULE_PATTERN, r'\\common_module\\\g<src>'),
    (_CC_TEMPLATE_OTHERS_PATTERN, r'\\\g<src>'),
]


def map_to_local_path(origin: str, parent_dir_path: str):
    """
    :param origin: 原始路径
    :param parent_dir_path: 目标父目录路径
    :return: 映射后的路径

    map_to_local_path(r'..\pack_temp\gamelive_r100\anchorlive\game_assistant_v2', r'D:\cctemplate')
    -> "D:\\cctemplate\\transformer\\anchorlive\\game_assistant_v2"
    """
    for pattern, repl in _PATTERNS:
        result, n = re.subn(pattern, re.escape(parent_dir_path) + repl, origin)
        if n == 1:
            return result
    return None

# -*- encoding:utf-8 -*-

"""
Developed by Jianzhang Chen
LICENSE: MIT
"""
import sys

if sys.platform != 'win32':
    raise NotImplementedError('Only support Windows platform')

import threading

from ctypes import POINTER, cast, byref, Structure, WinError, get_last_error, c_int, WinDLL, WINFUNCTYPE
from ctypes.wintypes import WPARAM, LPARAM, HANDLE, DWORD, BOOL, HINSTANCE, UINT, MSG, HHOOK, HWND

__all__ = ['grab']

user32 = WinDLL('user32', use_last_error=True)

HC_ACTION = 0
WH_KEYBOARD_LL = 13

WM_NULL = 0x0000
WM_QUIT = 0x0012

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

VK_F8 = 0x77  # 目前只使用F8键


WM_TO_TEXT = {
    WM_KEYDOWN: 'WM_KEYDOWN',
    WM_KEYUP: 'WM_KEYUP',
    WM_SYSKEYDOWN: 'WM_SYSKEYDOWN',
    WM_SYSKEYUP: 'WM_SYSKEYUP',
}

IMAGE_CURSOR = 2
LR_SHARED = 0x00008000
LR_COPYFROMRESOURCE = 0x00004000

SPI_SETCURSORS = 0x0057

ULONG_PTR = WPARAM
LRESULT = LPARAM
LPMSG = POINTER(MSG)
HCURSOR = HANDLE

HOOKPROC = WINFUNCTYPE(LRESULT, c_int, WPARAM, LPARAM)
LowLevelKeyboardProc = HOOKPROC


class KBDLLHOOKSTRUCT(Structure):
    _fields_ = (('vkCode', DWORD),
                ('scanCode', DWORD),
                ('flags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))


LPKBDLLHOOKSTRUCT = POINTER(KBDLLHOOKSTRUCT)


def errcheck_bool(result, func, args):
    if not result:
        raise WinError(get_last_error())
    return args


# ===================================
#  SetWindowsHookEx
#  https://learn.microsoft.com/zh-cn/windows/win32/api/winuser/nf-winuser-setwindowshookexw
# ===================================
user32.SetWindowsHookExW.errcheck = errcheck_bool
user32.SetWindowsHookExW.restype = HHOOK
user32.SetWindowsHookExW.argtypes = (
    # _In_ idHook
    c_int,
    # _In_ lpfn
    HOOKPROC,
    # _In_ hMod
    HINSTANCE,
    # _In_ dwThreadId
    DWORD,
)

# ===================================
#  PostThreadMessageW
#  https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-postthreadmessagew
# ===================================
user32.PostThreadMessageW.restype = BOOL
user32.PostThreadMessageW.argtypes = (
    # _In_ idThread
    DWORD,
    # _In_ Msg
    UINT,
    # _In_ wParam
    WPARAM,
    # _In_ lParam
    LPARAM,
)

# ===================================
#  UnhookWindowsHookEx
#  https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-unhookwindowshookex
# ===================================
user32.UnhookWindowsHookEx.restype = BOOL
user32.UnhookWindowsHookEx.argtypes = (
    # _In_ hhk
    HHOOK,
)

# ===================================
#  CallNextHookEx
#  https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-callnexthookex
# ===================================
user32.CallNextHookEx.restype = LRESULT
user32.CallNextHookEx.argtypes = (
    # _In_opt_ hhk
    HHOOK,
    # _In_     nCode
    c_int,
    # _In_     wParam
    WPARAM,
    # _In_     lParam
    LPARAM,
)

# ===================================
#  GetMessageW
#  https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getmessagew
# ===================================
user32.GetMessageW.argtypes = (
    # _Out_    lpMsg
    LPMSG,
    # _In_opt_ hWnd
    HWND,
    # _In_     wMsgFilterMin
    UINT,
    # _In_     wMsgFilterMax
    UINT,
)

# ===================================
#  TranslateMessage
#  https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-translatemessage
# ===================================
user32.TranslateMessage.argtypes = (
    # _In_ lpMsg
    LPMSG,
)

# ===================================
#  DispatchMessageW
#  https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-dispatchmessagew
# ===================================
user32.DispatchMessageW.argtypes = (
    # _In_ lpMsg
    LPMSG,
)


# Whether to print debug messages
_is_debug = False

# The result of the grab
_result = 0

# The target virtual key
_target_vk = 0


def _print_keyboard_msg(wParam, msg):
    msg_id = WM_TO_TEXT.get(wParam, str(wParam))
    msg_to_print = (msg.vkCode, msg.scanCode, msg.flags, msg.time, msg.dwExtraInfo)
    print('{:15s}: {}'.format(msg_id, msg_to_print))


@LowLevelKeyboardProc
def _LLKeyboardProc(nCode, wParam, lParam):
    """ Low-level mouse input event hook procedure. """
    global _result

    if nCode == HC_ACTION:
        msg = cast(lParam, LPKBDLLHOOKSTRUCT)[0]

        if _is_debug:
            _print_keyboard_msg(wParam, msg)

        if wParam == WM_KEYUP and msg.vkCode == _target_vk:
            # Post a WM_NULL message to the current thread to exit the message loop when the grab is finished.
            _result = 1
            user32.PostThreadMessageW(threading.current_thread().ident, WM_NULL, 0, 0)
            return 1
    return user32.CallNextHookEx(None, nCode, wParam, lParam)


def _msg_loop():
    """ Start a message loop to grab the PID of the window under the cursor. """
    hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, _LLKeyboardProc, None, 0)
    msg = MSG()

    while _result == 0:  # Wait until the grab is finished (when _result is not zero).
        bRet = user32.GetMessageW(byref(msg), None, 0, 0)
        if not bRet:
            break
        if bRet == -1:
            raise WinError(get_last_error())
        user32.TranslateMessage(byref(msg))
        user32.DispatchMessageW(byref(msg))

    user32.UnhookWindowsHookEx(hook)
    return _result


# region The public API
def grab(virtual_key, callback, _debug=False):
    global _is_debug, _result, _target_vk
    _is_debug = _debug
    _target_vk = virtual_key

    _result = 0
    _msg_loop()
    callback()
    return


# endregion


if __name__ == '__main__':
    grab(VK_F8, callback=lambda: print('<!UP!>'), _debug=False)

"""Typing keys on the Mac.

Uses CoreGraphics directly through ctypes -- the same call keyboard drivers and
remapping tools use -- so there's nothing extra to install. macOS only lets an
app do this once it has Accessibility permission.
"""
import ctypes

_CG = ctypes.cdll.LoadLibrary(
    "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
)
_CF = ctypes.cdll.LoadLibrary(
    "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
)

_CG.CGPreflightPostEventAccess.restype = ctypes.c_bool
_CG.CGRequestPostEventAccess.restype = ctypes.c_bool
_CG.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
_CG.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool]
_CG.CGEventSetFlags.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
_CG.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
_CF.CFRelease.argtypes = [ctypes.c_void_p]

_HID_EVENT_TAP = 0  # kCGHIDEventTap: inject as if from a real keyboard


def can_type() -> bool:
    """True if macOS will let this app type keys."""
    return _CG.CGPreflightPostEventAccess()


def ask_permission() -> None:
    """Show macOS's 'allow this app to control your computer' prompt."""
    _CG.CGRequestPostEventAccess()


def _post(keycode: int, down: bool) -> None:
    event = _CG.CGEventCreateKeyboardEvent(None, keycode, down)
    # Clear modifiers so a held Shift or Cmd can't turn F into a shortcut.
    _CG.CGEventSetFlags(event, 0)
    _CG.CGEventPost(_HID_EVENT_TAP, event)
    _CF.CFRelease(event)


def key_down(keycode: int) -> None:
    _post(keycode, True)


def key_up(keycode: int) -> None:
    _post(keycode, False)

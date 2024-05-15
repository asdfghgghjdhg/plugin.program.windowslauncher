import ctypes
import ctypes.wintypes

import xbmc

SEE_MASK_NOCLOSEPROCESS             = 0x00000040
SEE_MASK_NOASYNC                    = 0x00000100
SEE_MASK_FLAG_NO_UI                 = 0x00000400
SEE_MASK_WAITFORINPUTIDLE           = 0x02000000

INFINITE                            = -1

WAIT_ABANDONED                      = 0x00000080
WAIT_OBJECT_0                       = 0x00000000
WAIT_TIMEOUT                        = 0x00000102
WAIT_FAILED                         = 0xFFFFFFFF

SW_SHOWNORMAL                       = 1

STILL_ACTIVE                        = 259

class ShellExecuteInfo(ctypes.Structure):
    _fields_ = (
        ("cbSize", ctypes.wintypes.DWORD),
        ("fMask", ctypes.c_ulong),
        ("hwnd", ctypes.wintypes.HANDLE),
        ("lpVerb", ctypes.c_char_p),
        ("lpFile", ctypes.c_char_p),
        ("lpParameters", ctypes.c_char_p),
        ("lpDirectory", ctypes.c_char_p),
        ("nShow", ctypes.c_int),
        ("hInstApp", ctypes.wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", ctypes.c_char_p),
        ("hKeyClass", ctypes.wintypes.HKEY),
        ("dwHotKey", ctypes.wintypes.DWORD),
        ("hIconOrMonitor", ctypes.wintypes.HANDLE),
        ("hProcess", ctypes.wintypes.HANDLE),
    )

    def __init__(self, **kw):
        ctypes.Structure.__init__(self)
        self.cbSize = ctypes.sizeof(self)
        for field_name, field_value in kw.items():
            setattr(self, field_name, field_value)

shellExecuteEx = ctypes.windll.shell32.ShellExecuteEx
shellExecuteEx.restype = ctypes.wintypes.BOOL

waitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
waitForSingleObject.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD)
waitForSingleObject.restype = ctypes.wintypes.DWORD

closeHandle = ctypes.windll.kernel32.CloseHandle
closeHandle.argtypes = (ctypes.wintypes.HANDLE, )
closeHandle.restype = ctypes.wintypes.BOOL

getExitCodeProcess = ctypes.windll.kernel32.GetExitCodeProcess
getExitCodeProcess.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.LPDWORD)
getExitCodeProcess.restype = ctypes.wintypes.BOOL

def log(tag: str, level: int, msg: str, *args):
    xbmc.log(tag + ': ' + msg.format(*args), level)

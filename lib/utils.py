import ctypes
import ctypes.wintypes

import xbmc

SEE_MASK_NOCLOSEPROCESS             = 0x00000040
SEE_MASK_NOASYNC                    = 0x00000100
SEE_MASK_WAITFORINPUTIDLE           = 0x02000000

INFINITE                            = -1

WAIT_ABANDONED                      = 0x00000080
WAIT_OBJECT_0                       = 0x00000000
WAIT_TIMEOUT                        = 0x00000102
WAIT_FAILED                         = 0xFFFFFFFF

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

def log(tag: str, level: int, msg: str, *args):
    xbmc.log(tag + ': ' + msg.format(*args), level)

def startandwait(target: str, args: str = '', directory: str = ''):
    result = False

    mask = SEE_MASK_NOCLOSEPROCESS + SEE_MASK_NOASYNC + SEE_MASK_WAITFORINPUTIDLE
    seInfo = ShellExecuteInfo(fMask = mask, lpVerb = 'open'.encode('utf-8'), lpFile = target.encode('utf-8'), lpParameters = args.encode('utf-8'), lpDirectory = directory.encode('utf-8'), nShow = 5)
    if shellExecuteEx(ctypes.byref(seInfo)): result = True

    return result
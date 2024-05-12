import xbmc

def log(tag: str, level: int, msg: str, *args):
    xbmc.log(tag + ': ' + msg.format(*args), level)

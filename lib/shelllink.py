# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-shllink/

import os
import sys
import locale
import struct
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

def _getItemIDList(data):
    result = []

    pos = 0
    itemIDSize = int.from_bytes(data[pos:pos + 2], 'little', signed = False)
    while itemIDSize != 0:
        result.append(ItemID(data[pos:]))

        pos += itemIDSize
        itemIDSize = int.from_bytes(data[pos:pos + 2], 'little')

    return result

def _nullTerminatedString(data, isUnicode):
    result = ''

    pos = 0
    while pos < len(data):
        if not isUnicode:
            if data[pos] == 0x00:
                break

            result += data[pos:pos + 1].decode(locale.getpreferredencoding())
            pos += 1
        else:
            if int.from_bytes(data[pos:pos + 2], 'little') == 0x0000:
                break

            result += chr(int.from_bytes(data[pos:pos + 2], 'little'))
            pos += 2

    return result

def _decodeString(data, isUnicode):
    if not isUnicode:
        if len(data) == 0:
            return ''
        else:
            return data.decode(locale.getpreferredencoding())
    else:
        result = ''

        pos = 0
        while pos < len(data):
            result += chr(int.from_bytes(data[pos:pos + 2], 'little'))
            pos += 2

        return result

class LinkFlags:
    def __init__(self, data):
        self._hasLinkTargetIDList             = data[0] & 0b00000001 == 0b00000001
        self._hasLinkInfo                     = data[0] & 0b00000010 == 0b00000010
        self._hasName                         = data[0] & 0b00000100 == 0b00000100
        self._hasRelativePath                 = data[0] & 0b00001000 == 0b00001000
        self._hasWorkingDir                   = data[0] & 0b00010000 == 0b00010000
        self._hasArguments                    = data[0] & 0b00100000 == 0b00100000
        self._hasIconLocation                 = data[0] & 0b01000000 == 0b01000000
        self._isUnicode                       = data[0] & 0b10000000 == 0b10000000

        self._forceNoLinkInfo                 = data[1] & 0b00000001 == 0b00000001
        self._hasExpString                    = data[1] & 0b00000010 == 0b00000010
        self._runInSeparateProcess            = data[1] & 0b00000100 == 0b00000100
        self._hasDarwinID                     = data[1] & 0b00010000 == 0b00010000
        self._runAsUser                       = data[1] & 0b00100000 == 0b00100000
        self._hasExpIcon                      = data[1] & 0b01000000 == 0b01000000
        self._noPidlAlias                     = data[1] & 0b10000000 == 0b10000000

        self._runWithShimLayer                = data[2] & 0b00000010 == 0b00000010
        self._forceNoLinkTrack                = data[2] & 0b00000100 == 0b00000100
        self._enableTargetMetadata            = data[2] & 0b00001000 == 0b00001000
        self._disableLinkPathTracking         = data[2] & 0b00010000 == 0b00010000
        self._disableKnownFolderTracking      = data[2] & 0b00100000 == 0b00100000
        self._disableKnownFolderAlias         = data[2] & 0b01000000 == 0b01000000
        self._allowLinkToLink                 = data[2] & 0b10000000 == 0b10000000

        self._unaliasOnSave                   = data[3] & 0b00000001 == 0b00000001
        self._preferEnvironmentPath           = data[3] & 0b00000010 == 0b00000010
        self._keepLocalIDListForUNCTarget     = data[3] & 0b00000100 == 0b00000100

        return super().__init__()

    def __str__(self):
        result = 'LinkFlags {{\nhasLinkTargetIDList: {}\nhasLinkInfo: {}\nhasName: {}\nhasRelativePath: {}\nhasWorkingDir: {}\nhasArguments: {}\nhasIconLocation: {}\nisUnicode: {}\nforceNoLinkInfo: {}\nhasExpString: {}\nrunInSeparateProcess: {}\nhasDarwinID: {}\nrunAsUser: {}\nhasExpIcon: {}\nnoPidlAlias: {}\nrunWithShimLayer: {}\nforceNoLinkTrack: {}\nenableTargetMetadata: {}\ndisableLinkPathTracking: {}\ndisableKnownFolderTracking: {}\ndisableKnownFolderAlias: {}\nallowLinkToLink: {}\nunaliasOnSave: {}\npreferEnvironmentPath: {}\nkeepLocalIDListForUNCTarget: {}\n}}'
        return result.format(self._hasLinkTargetIDList, self._hasLinkInfo, self._hasName, self._hasRelativePath, self._hasWorkingDir, self._hasArguments, self._hasIconLocation, self._isUnicode, self._forceNoLinkInfo, self._hasExpString, self._runInSeparateProcess, self._hasDarwinID, self._runAsUser, self._hasExpIcon, self._noPidlAlias, self._runWithShimLayer, self._forceNoLinkTrack, self._enableTargetMetadata, self._disableLinkPathTracking, self._disableKnownFolderTracking, self._disableKnownFolderAlias, self._allowLinkToLink, self._unaliasOnSave, self._preferEnvironmentPath, self._keepLocalIDListForUNCTarget)

    def _getHasLinkTargetIDList(self):
        return self._hasLinkTargetIDList
    def _getHasLinkInfo(self):
        return self._hasLinkInfo
    def _getHasName(self):
        return self._hasName
    def _getHasRelativePath(self):
        return self._hasRelativePath
    def _getHasWorkingDir(self):
        return self._hasWorkingDir
    def _getHasArguments(self):
        return self._hasArguments
    def _getHasIconLocation(self):
        return self._hasIconLocation
    def _getIsUnicode(self):
        return self._isUnicode
    def _getForceNoLinkInfo(self):
        return self._forceNoLinkInfo
    def _getHasExpString(self):
        return self._hasExpString
    def _getRunInSeparateProcess(self):
        return self._runInSeparateProcess
    def _getHasDarwinID(self):
        return self._hasDarwinID
    def _getRunAsUser(self):
        return self._runAsUser
    def _getHasExpIcon(self):
        return self._hasExpIcon
    def _getNoPidlAlias(self):
        return self._noPidlAlias
    def _getRunWithShimLayer(self):
        return self._runWithShimLayer
    def _getForceNoLinkTrack(self):
        return self._forceNoLinkTrack
    def _getEnableTargetMetadata(self):
        return self._enableTargetMetadata
    def _getDisableLinkPathTracking(self):
        return self._disableLinkPathTracking
    def _getDisableKnownFolderTracking(self):
        return self._disableKnownFolderTracking
    def _getDisableKnownFolderAlias(self):
        return self._disableKnownFolderAlias
    def _getAllowLinkToLink(self):
        return self._allowLinkToLink
    def _getUnaliasOnSave(self):
        return self._unaliasOnSave
    def _getPreferEnvironmentPath(self):
        return self._preferEnvironmentPath
    def _getKeepLocalIDListForUNCTarget(self):
        return self._keepLocalIDListForUNCTarget

    hasLinkTargetIDList = property(fget = _getHasLinkTargetIDList, fset = None, fdel = None, doc = None)
    hasLinkInfo = property(fget = _getHasLinkInfo, fset = None, fdel = None, doc = None)
    hasName = property(fget = _getHasName, fset = None, fdel = None, doc = None)
    hasRelativePath = property(fget = _getHasRelativePath, fset = None, fdel = None, doc = None)
    hasWorkingDir = property(fget = _getHasWorkingDir, fset = None, fdel = None, doc = None)
    hasArguments = property(fget = _getHasArguments, fset = None, fdel = None, doc = None)
    hasIconLocation = property(fget = _getHasIconLocation, fset = None, fdel = None, doc = None)
    isUnicode = property(fget = _getIsUnicode, fset = None, fdel = None, doc = None)
    forceNoLinkInfo = property(fget = _getForceNoLinkInfo, fset = None, fdel = None, doc = None)
    hasExpString = property(fget = _getHasExpString, fset = None, fdel = None, doc = None)
    runInSeparateProcess = property(fget = _getRunInSeparateProcess, fset = None, fdel = None, doc = None)
    hasDarwinID = property(fget = _getHasDarwinID, fset = None, fdel = None, doc = None)
    runAsUser = property(fget = _getRunAsUser, fset = None, fdel = None, doc = None)
    hasExpIcon = property(fget = _getHasExpIcon, fset = None, fdel = None, doc = None)
    noPidlAlias = property(fget = _getNoPidlAlias, fset = None, fdel = None, doc = None)
    runWithShimLayer = property(fget = _getRunWithShimLayer, fset = None, fdel = None, doc = None)
    forceNoLinkTrack = property(fget = _getForceNoLinkTrack, fset = None, fdel = None, doc = None)
    enableTargetMetadata = property(fget = _getEnableTargetMetadata, fset = None, fdel = None, doc = None)
    disableLinkPathTracking = property(fget = _getDisableLinkPathTracking, fset = None, fdel = None, doc = None)
    disableKnownFolderTracking = property(fget = _getDisableKnownFolderTracking, fset = None, fdel = None, doc = None)
    disableKnownFolderAlias = property(fget = _getDisableKnownFolderAlias, fset = None, fdel = None, doc = None)
    allowLinkToLink = property(fget = _getAllowLinkToLink, fset = None, fdel = None, doc = None)
    unaliasOnSave = property(fget = _getUnaliasOnSave, fset = None, fdel = None, doc = None)
    preferEnvironmentPath = property(fget = _getPreferEnvironmentPath, fset = None, fdel = None, doc = None)
    keepLocalIDListForUNCTarget = property(fget = _getKeepLocalIDListForUNCTarget, fset = None, fdel = None, doc = None)

class FileAttributesFlags:
    def __init__(self, data):
        self._fileAttributeReadOnly             = data[0] & 0b00000001 == 0b00000001
        self._fileAttributeHidden               = data[0] & 0b00000010 == 0b00000010
        self._fileAttributeSystem               = data[0] & 0b00000100 == 0b00000100
        self._fileAttributeDirectory            = data[0] & 0b00010000 == 0b00010000
        self._fileAttributeArchive              = data[0] & 0b00100000 == 0b00100000
        self._fileAttributeNormal               = data[0] & 0b10000000 == 0b10000000

        self._fileAttributeTemporary            = data[1] & 0b00000001 == 0b00000001
        self._fileAttributeSparseFile           = data[1] & 0b00000010 == 0b00000010
        self._fileAttributeReparsePoint         = data[1] & 0b00000100 == 0b00000100
        self._fileAttributeCompressed           = data[1] & 0b00001000 == 0b00001000
        self._fileAttributeOffline              = data[1] & 0b00010000 == 0b00010000
        self._fileAttributeNotContentIndexed    = data[1] & 0b00100000 == 0b00100000
        self._fileAttributeEncrypted            = data[1] & 0b01000000 == 0b01000000

        return super().__init__()

    def __str__(self):
        result = 'FileAttributesFlags {{\nfileAttributeReadOnly: {}\nfileAttributeHidden: {}\nfileAttributeSystem: {}\nfileAttributeDirectory: {}\nfileAttributeArchive: {}\nfileAttributeNormal: {}\nfileAttributeTemporary: {}\nfileAttributeSparseFile: {}\nfileAttributeReparsePoint: {}\nfileAttributeCompressed: {}\nfileAttributeOffline: {}\nfileAttributeNotContentIndexed: {}\nfileAttributeEncrypted: {}\n}}'
        return result.format(self._fileAttributeReadOnly, self._fileAttributeHidden, self._fileAttributeSystem, self._fileAttributeDirectory, self._fileAttributeArchive, self._fileAttributeNormal, self._fileAttributeTemporary, self._fileAttributeSparseFile, self._fileAttributeReparsePoint, self._fileAttributeCompressed, self._fileAttributeOffline, self._fileAttributeNotContentIndexed, self._fileAttributeEncrypted)

    def _getFileAttributeReadOnly(self):
        return self._fileAttributeReadOnly
    def _getFileAttributeHidden(self):
        return self._fileAttributeHidden
    def _getFileAttributeSystem(self):
        return self._fileAttributeSystem
    def _getFileAttributeDirectory(self):
        return self._fileAttributeDirectory
    def _getFileAttributeArchive(self):
        return self._fileAttributeArchive
    def _getFileAttributeNormal(self):
        return self._fileAttributeNormal
    def _getFileAttributeTemporary(self):
        return self._fileAttributeTemporary
    def _getFileAttributeSparseFile(self):
        return self._fileAttributeSparseFile
    def _getFileAttributeReparsePoint(self):
        return self._fileAttributeReparsePoint
    def _getFileAttributeCompressed(self):
        return self._fileAttributeCompressed
    def _getFileAttributeOffline(self):
        return self._fileAttributeOffline
    def _getFileAttributeNotContentIndexed(self):
        return self._fileAttributeNotContentIndexed
    def _getFileAttributeEncrypted(self):
        return self._fileAttributeEncrypted

    fileAttributeReadOnly = property(fget = _getFileAttributeReadOnly, fset = None, fdel = None, doc = None)
    fileAttributeHidden = property(fget = _getFileAttributeHidden, fset = None, fdel = None, doc = None)
    fileAttributeSystem = property(fget = _getFileAttributeSystem, fset = None, fdel = None, doc = None)
    fileAttributeDirectory = property(fget = _getFileAttributeDirectory, fset = None, fdel = None, doc = None)
    fileAttributeArchive = property(fget = _getFileAttributeArchive, fset = None, fdel = None, doc = None)
    fileAttributeNormal = property(fget = _getFileAttributeNormal, fset = None, fdel = None, doc = None)
    fileAttributeTemporary = property(fget = _getFileAttributeTemporary, fset = None, fdel = None, doc = None)
    fileAttributeSparseFile = property(fget = _getFileAttributeSparseFile, fset = None, fdel = None, doc = None)
    fileAttributeReparsePoint = property(fget = _getFileAttributeReparsePoint, fset = None, fdel = None, doc = None)
    fileAttributeCompressed = property(fget = _getFileAttributeCompressed, fset = None, fdel = None, doc = None)
    fileAttributeOffline = property(fget = _getFileAttributeOffline, fset = None, fdel = None, doc = None)
    fileAttributeNotContentIndexed = property(fget = _getFileAttributeNotContentIndexed, fset = None, fdel = None, doc = None)
    fileAttributeEncrypted = property(fget = _getFileAttributeEncrypted, fset = None, fdel = None, doc = None)

class FILETIME:
    def __init__(self, dwLowDateTime = 0, dwHighDateTime = 0, bytes = None):
        if (bytes is None) and isinstance(dwLowDateTime, int) and isinstance(dwHighDateTime, int):
            self._dwLowDateTime = dwLowDateTime
            self._dwHighDateTime = dwHighDateTime
        elif not bytes is None:
            self._dwLowDateTime = int.from_bytes(bytes[0:4], 'little', signed = False)
            self._dwHighDateTime = int.from_bytes(bytes[4:8], 'little', signed = False)
        else:
            raise ValueError('Invalid FILETIME')

        return super().__init__()

    def __str__(self):
        return '{}'.format(self._getDateTime())

    def _getLowDateTime(self):
        return self._dwLowDateTime
    def _setLowDateTime(self, dwLowDateTime):
        self._dwLowDateTime = dwLowDateTime

    def _getHighDateTime(self):
        return self._dwHighDateTime
    def _setHighDateTime(self, dwHighDateTime):
        self._dwHighDateTime = dwHighDateTime

    def _getDateTime(self):
        mcs = ((self._dwHighDateTime << 32) | self._dwLowDateTime) / 10
        return datetime(1601, 1, 1, 0, 0, 0) + timedelta(microseconds = mcs)

    dwLowDateTime = property(fget = _getLowDateTime, fset = _setLowDateTime, fdel = None, doc = None)
    dwHighDateTime = property(fget = _getHighDateTime, fset = _setHighDateTime, fdel = None, doc = None)
    dateTime = property(fget = _getDateTime, fset = None, fdel = None, doc = None)

class HotKeyFlags:
    HOTKEYF_SHIFT   = 0x01
    HOTKEYF_CONTROL = 0x02
    HOTKEYF_ALT     = 0x04

    def __init__(self, data):
        self._lowByte = data[0]
        self._highByte = data[1]

        return super().__init__()

    def __str__(self):
        result = 'HotKeyFlags {{\nkey: {}\nmodifiers: {}\n}}'
        return result.format(self._lowByte, self._getModifiers())

    def _getKey(self):
        return self._lowByte
    def _getModifiers(self):
        result = []
        if self._highByte & HotKeyFlags.HOTKEYF_SHIFT == HotKeyFlags.HOTKEYF_SHIFT:
            result.append(HOTKEYF_SHIFT)
        if self._highByte & HotKeyFlags.HOTKEYF_CONTROL == HotKeyFlags.HOTKEYF_CONTROL:
            result.append(HOTKEYF_CONTROL)
        if self._highByte & HotKeyFlags.HOTKEYF_ALT == HotKeyFlags.HOTKEYF_ALT:
            result.append(HOTKEYF_ALT)
        return result

    key = property(fget = _getKey, fset = None, fdel = None, doc = None)
    modifiers = property(fget = _getModifiers, fset = None, doc = None)

class ShellLinkHeader:
    _SHELL_LINK_HEADER_SIZE  = 0x0000004C

    SW_SHOWNORMAL           = 0x00000001
    SW_SHOWMAXIMIZED        = 0x00000003
    SW_SHOWMINNOACTIVE      = 0x00000007

    def __init__(self, data):
        self._headerSize = int.from_bytes(data[0:4], 'little')
        if self._headerSize != ShellLinkHeader._SHELL_LINK_HEADER_SIZE:
            raise ValueError('Not valid Shell Link Header')

        self._linkCLSID = UUID(bytes_le = data[4:20])
        if self._linkCLSID != UUID('00021401-0000-0000-C000-000000000046'):
            raise ValueError('Not valid Shell Link Header')

        self._linkFlags = LinkFlags(data[20:24])
        self._fileAttributes = FileAttributesFlags(data[24:28])

        self._creationTime = FILETIME(bytes = data[28:36])
        self._accessTime = FILETIME(bytes = data[36:44])
        self._writeTime = FILETIME(bytes = data[44:52])

        self._fileSize = int.from_bytes(data[52:56], 'little', signed = False)
        self._iconIndex = int.from_bytes(data[56:60], 'little', signed = True)
        self._showCommand = int.from_bytes(data[60:64], 'little', signed = False)

        self._hotKey = HotKeyFlags(data[64:66])
        
        return super().__init__()

    def _getHeaderSize(self):
        return self._headerSize
    def _getCLSID(self):
        return self._linkCLSID
    def _getFlags(self):
        return self._linkFlags
    def _getFileAttributes(self):
        return self._fileAttributes
    def _getCreationTime(self):
        return self._creationTime
    def _getAccessTime(self):
        return self._accessTime
    def _getWriteTime(self):
        return self._writeTime
    def _getFileSize(self):
        return self._fileSize
    def _getIconIndex(self):
        return self._iconIndex
    def _getShowCommand(self):
        return self._showCommand
    def _getHotKey(self):
        return self._hotKey

    #headerSize = property(fget = _getHeaderSize, fset = None, fdel = None, doc = None)
    linkCLSID = property(fget = _getCLSID, fset = None, fdel = None, doc = None)
    linkFlags = property(fget = _getFlags, fset = None, fdel = None, doc = None)
    fileAttributes = property(fget = _getFileAttributes, fset = None, fdel = None, doc = None)
    creationTime = property(fget = _getCreationTime, fset = None, fdel = None, doc = None)
    accessTime = property(fget = _getAccessTime, fset = None, fdel = None, doc = None)
    writeTime = property(fget = _getWriteTime, fset = None, fdel = None, doc = None)
    fileSize = property(fget = _getFileSize, fset = None, fdel = None, doc = None)
    iconIndex = property(fget = _getIconIndex, fset = None, fdel = None, doc = None)
    showCommand = property(fget = _getShowCommand, fset = None, fdel = None, doc = None)
    hotKey = property(fget = _getHotKey, fset = None, fdel = None, doc = None)

class ItemID:
    def __init__(self, data):
        self._itemIDSize = int.from_bytes(data[0:2], 'little', signed = False)
        self._data = data[2:self._itemIDSize - 2]

        return super().__init__()

    def _getItemIDSize(self):
        return self._itemIDSize
    def _getData(self):
        return self._data

    #itemIDSize = property(fget = _getItemIDSize, fset = None, fdel = None, doc = None)
    data = property(fget = _getData, fset = None, fdel = None, doc = None)

class LinkTargetIDList:
    def __init__(self, data):
        self._idListSize = int.from_bytes(data[0:2], 'little', signed = False)
        self._idList = _getItemIDList(data[2:])

        return super().__init__()

    def _getIDListSize(self):
        return self._idListSize
    def _getIDList(self):
        return self._idList

    #idListSize = property(fget = _getIDListSize, fset = None, fdel = None, doc = None)
    idList = property(fget = _getIDList, fset = None, fdel = None, doc = None)

class LinkInfoFlags:
    def __init__(self, data):
        self._volumeIDAndLocalBasePath = data[0] & 0b00000001 == 0b00000001
        self._commonNetworkRelativeLinkAndPathSuffix = data[0] & 0b00000010 == 0b00000010

        return super().__init__()

    def __str__(self):
        result = 'LinkInfoFlags {{\nvolumeIDAndLocalBasePath: {}\ncommonNetworkRelativeLinkAndPathSuffix: {}\n}}'
        return result.format(self._volumeIDAndLocalBasePath, self._commonNetworkRelativeLinkAndPathSuffix)

    def _getVolumeIDAndLocalBasePath(self):
        return self._volumeIDAndLocalBasePath
    def _getCommonNetworkRelativeLinkAndPathSuffix(self):
        return self._commonNetworkRelativeLinkAndPathSuffix

    volumeIDAndLocalBasePath = property(fget = _getVolumeIDAndLocalBasePath, fset = None, fdel = None, doc = None)
    commonNetworkRelativeLinkAndPathSuffix = property(fget = _getCommonNetworkRelativeLinkAndPathSuffix, fset = None, fdel = None, doc = None)

class VolumeID:
    DRIVE_UNKNOWN       = 0x00000000
    DRIVE_NO_ROOT_DIR   = 0x00000001
    DRIVE_REMOVABLE     = 0x00000002
    DRIVE_FIXED         = 0x00000003
    DRIVE_REMOTE        = 0x00000004
    DRIVE_CDROM         = 0x00000005
    DRIVE_RAMDISK       = 0x00000006

    def __init__(self, data):
        self._volumeIDSize = int.from_bytes(data[0:4], 'little', signed = False)
        if self._volumeIDSize <= 0x00000010:
            raise ValueError('Not valid Volume ID')

        self._driveType = int.from_bytes(data[4:8], 'little', signed = False)
        self._driveSerialNumber = int.from_bytes(data[8:12], 'little', signed = False)
        self._volumeLabelOffset = int.from_bytes(data[12:16], 'little', signed = False)

        self._volumeLabelOffsetUnicode = 0
        if self._volumeLabelOffset == 0x00000014:
            self._volumeLabelOffsetUnicode = int.from_bytes(data[16:20], 'little', signed = False)
            self._data = _nullTerminatedString(data[self._volumeLabelOffsetUnicode:], True)
        else:
            self._data = _nullTerminatedString(data[self._volumeLabelOffset:], False)

        return super().__init__()

    def __str__(self):
        result = 'VolumeID {{driveType: 0x{:0>8x}, driveSerialNumber: {}, volumeLabel: "{}"}}'
        return result.format(self._driveType, self._driveSerialNumber, self._data)

    def _getVolumeIDSize(self):
        return self._volumeIDSize
    def _getDriveType(self):
        return self._driveType
    def _getDriveSerialNumber(self):
        return self._driveSerialNumber
    def _getVolumeLabel(self):
        return self._data

    driveType = property(fget = _getDriveType, fset = None, fdel = None, doc = None)
    driveSerialNumber = property(fget = _getDriveSerialNumber, fset = None, fdel = None, doc = None)
    volumeLabel = property(fget = _getVolumeLabel, fset = None, fdel = None, doc = None)

class CommonNetworkRelativeLinkFlags:
    def __init__(self, data):
        self._validDevice   = data[0] & 0b00000001 == 0b00000001
        self._validNetType  = data[0] & 0b00000010 == 0b00000010

        return super().__init__()

    def __str__(self):
        result = 'CommonNetworkRelativeLinkFlags {{\nvalidDevice: {}\nvalidNetType: {}\n}}'
        return result.format(self._validDevice, self._validNetType)

    def _getValidDevice(self):
        return self._validDevice
    def _getValidNetType(self):
        return self._validNetType

    validDevice = property(fget = _getValidDevice, fset = None, fdel = None, doc = None)
    validNetType = property(fget = _getValidNetType, fset = None, fdel = None, doc = None)

class CommonNetworkRelativeLink:
    WNNC_NET_AVID           = 0x001A0000
    WNNC_NET_DOCUSPACE      = 0x001B0000
    WNNC_NET_MANGOSOFT      = 0x001C0000
    WNNC_NET_SERNET         = 0x001D0000
    WNNC_NET_RIVERFRONT1    = 0X001E0000
    WNNC_NET_RIVERFRONT2    = 0x001F0000
    WNNC_NET_DECORB         = 0x00200000
    WNNC_NET_PROTSTOR       = 0x00210000
    WNNC_NET_FJ_REDIR       = 0x00220000
    WNNC_NET_DISTINCT       = 0x00230000
    WNNC_NET_TWINS          = 0x00240000
    WNNC_NET_RDR2SAMPLE     = 0x00250000
    WNNC_NET_CSC            = 0x00260000
    WNNC_NET_3IN1           = 0x00270000
    WNNC_NET_EXTENDNET      = 0x00290000
    WNNC_NET_STAC           = 0x002A0000
    WNNC_NET_FOXBAT         = 0x002B0000
    WNNC_NET_YAHOO          = 0x002C0000
    WNNC_NET_EXIFS          = 0x002D0000
    WNNC_NET_DAV            = 0x002E0000
    WNNC_NET_KNOWARE        = 0x002F0000
    WNNC_NET_OBJECT_DIRE    = 0x00300000
    WNNC_NET_MASFAX         = 0x00310000
    WNNC_NET_HOB_NFS        = 0x00320000
    WNNC_NET_SHIVA          = 0x00330000
    WNNC_NET_IBMAL          = 0x00340000
    WNNC_NET_LOCK           = 0x00350000
    WNNC_NET_TERMSRV        = 0x00360000
    WNNC_NET_SRT            = 0x00370000
    WNNC_NET_QUINCY         = 0x00380000
    WNNC_NET_OPENAFS        = 0x00390000
    WNNC_NET_AVID1          = 0X003A0000
    WNNC_NET_DFS            = 0x003B0000
    WNNC_NET_KWNP           = 0x003C0000
    WNNC_NET_ZENWORKS       = 0x003D0000
    WNNC_NET_DRIVEONWEB     = 0x003E0000
    WNNC_NET_VMWARE         = 0x003F0000
    WNNC_NET_RSFX           = 0x00400000
    WNNC_NET_MFILES         = 0x00410000
    WNNC_NET_MS_NFS         = 0x00420000
    WNNC_NET_GOOGLE         = 0x00430000

    def __init__(self, data):
        self._commonNetworkRelativeLinkSize = int.from_bytes(data[0:4], 'little', signed = False)
        if self._commonNetworkRelativeLinkSize < 0x00000014:
            raise ValueError('Not valid CommonNetworkRelativeLink')

        self._commonNetworkRelativeLinkFlags = CommonNetworkRelativeLinkFlags(data[4:8])

        self._netNameOffset = int.from_bytes(data[8:12], 'little', signed = False)
        self._deviceNameOffset = int.from_bytes(data[12:16], 'little', signed = False)

        self._networkProviderType = 0x00000000
        if self._commonNetworkRelativeLinkFlags.validNetType:
            self._networkProviderType = int.from_bytes(data[16:20], 'little', signed = False)

        self._netNameOffsetUnicode = 0
        if self._commonNetworkRelativeLinkSize == 0x00000018:
            self._netNameOffsetUnicode = int.from_bytes(data[20:24], 'little', signed = False)

        self._deviceNameOffsetUnicode = 0
        if self._commonNetworkRelativeLinkSize == 0x0000001C:
            self._deviceNameOffsetUnicode = int.from_bytes(data[24:28], 'little', signed = False)

        self._netName = None
        self._deviceName = None
        self._netNameUnicode = None
        self._deviceNameUnicode = None

        if self._netNameOffset > 0:
            self._netName = _nullTerminatedString(data[self._netNameOffset:], False)

        if self._deviceNameOffset > 0:
            self._deviceName = _nullTerminatedString(data[self._deviceNameOffset:], False)

        if self._netNameOffsetUnicode > 0:
            self._netNameUnicode = _nullTerminatedString(data[self._netNameOffsetUnicode:], True)

        if self._deviceNameOffsetUnicode > 0:
            self._deviceNameUnicode = _nullTerminatedString(data[self._deviceNameOffsetUnicode:], True)

        return super().__init__()

    def __str__(self):
        result = 'CommonNetworkRelativeLink {{networkProviderType: 0x{:0>8x}, netName: {}, deviceName: {}}}'

        if self._netNameUnicode != None:
            netName = self._netNameUnicode
        else:
            netName = self._netName

        if self._deviceNameUnicode != None:
            deviceName = self._deviceNameUnicode
        else:
            deviceName = self._deviceName

        return result.format(self._networkProviderType, netName, deviceName)

    def _getCommonNetworkRelativeLinkFlags(self):
        return self._commonNetworkRelativeLinkFlags
    def _getNetworkProviderType(self):
        return self._networkProviderType

    def _getNetName(self):
        if self._netNameUnicode != None:
            return self._netNameUnicode
        else:
            return self._netName

    def _getDeviceName(self):
        if self._deviceNameUnicode != None:
            return self._deviceNameUnicode
        else:
            return self._deviceName

    commonNetworkRelativeLinkFlags = property(fget = _getCommonNetworkRelativeLinkFlags, fset = None, fdel = None, doc = None)
    networkProviderType = property(fget = _getNetworkProviderType, fset = None, fdel = None, doc = None)
    netName = property(fget = _getNetName, fset = None, fdel = None, doc = None)
    deviceName = property(fget = _getDeviceName, fset = None, fdel = None, doc = None)

class LinkInfo:
    def __init__(self, data):
        self._linkInfoSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._linkInfoHeaderSize = int.from_bytes(data[4:8], 'little', signed = False)
        self._linkInfoFlags = LinkInfoFlags(data[8:12])
        self._volumeIDOffset = int.from_bytes(data[12:16], 'little', signed = False)
        self._localBasePathOffset = int.from_bytes(data[16:20], 'little', signed = False)
        self._commonNetworkRelativeLinkOffset = int.from_bytes(data[20:24], 'little', signed = False)
        self._commonPathSuffixOffset = int.from_bytes(data[24:28], 'little', signed = False)

        pos = 28
        self._localBasePathOffsetUnicode = 0
        if self._linkInfoHeaderSize >= 0x00000024 and self._linkInfoFlags.volumeIDAndLocalBasePath:
            self._localBasePathOffsetUnicode = int.from_bytes(data[pos:pos + 4], 'little', signed = False)
            pos += 4
        self._commonPathSuffixOffsetUnicode = 0
        if self._linkInfoHeaderSize >= 0x00000024:
            self._commonPathSuffixOffsetUnicode = int.from_bytes(data[pos:pos + 4], 'little', signed = False)

        self._volumeID = None
        self._localBasePath = None
        self._commonNetworkRelativeLink = None
        self._commonPathSuffix = None
        self._localBasePathUnicode = None
        self._commonPathSuffixUnicode = None

        if self._volumeIDOffset > 0:
            self._volumeID = VolumeID(data[self._volumeIDOffset:])

        if self._localBasePathOffset > 0:
            self._localBasePath = _nullTerminatedString(data[self._localBasePathOffset:], False)

        if self._commonNetworkRelativeLinkOffset > 0:
            self._commonNetworkRelativeLink = CommonNetworkRelativeLink(data[self._commonNetworkRelativeLinkOffset:])

        if self._commonPathSuffixOffset > 0:
            self._commonPathSuffix = _nullTerminatedString(data[self._commonPathSuffixOffset:], False)

        if self._localBasePathOffsetUnicode > 0:
            self._localBasePathUnicode = _nullTerminatedString(data[self._localBasePathOffsetUnicode:], True)

        if self._commonPathSuffixOffsetUnicode > 0:
            self._commonPathSuffixUnicode = _nullTerminatedString(data[self._commonPathSuffixOffsetUnicode:], True)

        return super().__init__()

    def _getLinkInfoSize(self):
        return self._linkInfoSize
    def _getLinkInfoHeaderSize(self):
        return self._linkInfoHeaderSize
    def _getLinkInfoFlags(self):
        return self._linkInfoFlags
    def _getVolumeID(self):
        return self._volumeID
    def _getLocalBasePath(self):
        if self._localBasePathUnicode != None:
            return self._localBasePathUnicode
        else:
            return self._localBasePath
    def _getCommonNetworkRelativeLink(self):
        return self._commonNetworkRelativeLink
    def _getCommonPathSuffix(self):
        if self._commonPathSuffixUnicode != None:
            return self._commonPathSuffixUnicode
        else:
            return self._commonPathSuffix
    def _getCommonPathSuffixUnicode(self):
        return self._commonPathSuffixUnicode

    linkInfoFlags = property(fget = _getLinkInfoFlags, fset = None, fdel = None, doc = None)
    volumeID = property(fget = _getVolumeID, fset = None, fdel = None, doc = None)
    localBasePath = property(fget = _getLocalBasePath, fset = None, fdel = None, doc = None)
    commonNetworkRelativeLink = property(fget = _getCommonNetworkRelativeLink, fset = None, fdel = None, doc = None)
    commonPathSuffix = property(fget = _getCommonPathSuffix, fset = None, fdel = None, doc = None)

class StringData:
    def __init__(self, nameString = None, relativePath = None, workingDir = None, commandLineArguments = None, iconLocation = None):
        self._nameString = nameString
        self._relativePath = relativePath
        self._workingDir = workingDir
        self._commandLineArguments = commandLineArguments
        self._iconLocation = iconLocation

        return super().__init__()

    def __str__(self):
        result = 'StringData {{\nnameString: {}\nrelativePath: {}\nworkingDir: {}\ncommandLineArguments: {}\niconLocation: {}\n}}'
        return result.format(self._nameString, self._relativePath, self._workingDir, self._commandLineArguments, self._iconLocation)

    def _getNameString(self):
        return self._nameString
    def _getRelativePath(self):
        return self._relativePath
    def _getWorkingDir(self):
        return self._workingDir
    def _getCommandLineArguments(self):
        return self._commandLineArguments
    def _getIconLocation(self):
        return self._iconLocation

    nameString = property(fget = _getNameString, fset = None, fdel = None, doc = None)
    relativePath = property(fget = _getRelativePath, fset = None, fdel = None, doc = None)
    workingDir = property(fget = _getWorkingDir, fset = None, fdel = None, doc = None)
    commandLineArguments = property(fget = _getCommandLineArguments, fset = None, fdel = None, doc = None)
    iconLocation = property(fget = _getIconLocation, fset = None, fdel = None, doc = None)

class FontFamily:
    FF_DONTCARE                     = 0x0000
    FF_ROMAN                        = 0x0010
    FF_SWISS                        = 0x0020
    FF_MODERN                       = 0x0030
    FF_SCRIPT                       = 0x0040
    FF_DECORATIVE                   = 0x0050

    TMPF_NONE                       = 0x0000
    TMPF_FIXED_PITCH                = 0x0001
    TMPF_VECTOR                     = 0x0002
    TMPF_TRUETYPE                   = 0x0004
    TMPF_DEVICE                     = 0x0008

    def __init__(self, data):
        fontFamily = int.from_bytes(data, 'little', signed = False)

        self._family = FontFamily.FF_DONTCARE
        if (fontFamily >> 4) << 4 == FontFamily.FF_ROMAN:
            self._family = FontFamily.FF_ROMAN
        elif (fontFamily >> 4) << 4 == FontFamily.FF_SWISS:
            self._family = FontFamily.FF_SWISS
        elif (fontFamily >> 4) << 4 == FontFamily.FF_MODERN:
            self._family = FontFamily.FF_MODERN
        elif (fontFamily >> 4) << 4 == FontFamily.FF_SCRIPT:
            self._family = FontFamily.FF_SCRIPT
        elif (fontFamily >> 4) << 4 == FontFamily.FF_DECORATIVE:
            self._family = FontFamily.FF_DECORATIVE

        self._pitch = []
        if fontFamily & FontFamily.TMPF_FIXED_PITCH == FontFamily.TMPF_FIXED_PITCH:
            self._pitch.append(FontFamily.TMPF_FIXED_PITCH)
        if fontFamily & FontFamily.TMPF_VECTOR == FontFamily.TMPF_VECTOR:
            self._pitch.append(FontFamily.TMPF_VECTOR)
        if fontFamily & FontFamily.TMPF_TRUETYPE == FontFamily.TMPF_TRUETYPE:
            self._pitch.append(FontFamily.TMPF_TRUETYPE)
        if fontFamily & FontFamily.TMPF_DEVICE == FontFamily.TMPF_DEVICE:
            self._pitch.append(FontFamily.TMPF_DEVICE)
        if len(self._pitch) == 0:
            self._pitch = [FontFamily.TMPF_NONE]

        return super().__init__()

    def _getFamily(self):
        return self._family
    def _getPitch(self):
        return self._pitch

    family = property(fget = _getFamily, fset = None, fdel = None, doc = None)
    pitch = property(fget = _getPitch, fset = None, fdel = None, doc = None)

class FontSize:
    def __init__(self, data):
        self._width = int.from_bytes(data[0:2], 'little', signed = False)
        self._height = int.from_bytes(data[2:4], 'little', signed = False)

        return super().__init__()

    def _getHeight(self):
        return self._height
    def _getWidth(self):
        return self._width

    height = property(fget = _getHeight, fset = None, fdel = None, doc = None)
    width = property(fget = _getWidth, fset = None, fdel = None, doc = None)

class ConsoleDataBlock:
    _CONSOLE_PROPS                  = 0xA0000002

    FOREGROUND_BLUE                 = 0x0001
    FOREGROUND_GREEN                = 0x0002
    FOREGROUND_RED                  = 0x0004
    FOREGROUND_INTENSITY            = 0x0008
    BACKGROUND_BLUE                 = 0x0010
    BACKGROUND_GREEN                = 0x0020
    BACKGROUND_RED                  = 0x0040
    BACKGROUND_INTENSITY            = 0x0080

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize != 0x000000CC:
            raise ValueError('Not valid ConsoleDataBlock')
        if self._blockSignature != ConsoleDataBlock._CONSOLE_PROPS:
            raise ValueError('Not valid ConsoleDataBlock')

        self._fillAttributes = []
        fillAttributes = int.from_bytes(data[8:10], 'little', signed = False)
        if fillAttributes & ConsoleDataBlock.FOREGROUND_BLUE == ConsoleDataBlock.FOREGROUND_BLUE:
            self._fillAttributes.append(ConsoleDataBlock.FOREGROUND_BLUE)
        if fillAttributes & ConsoleDataBlock.FOREGROUND_GREEN == ConsoleDataBlock.FOREGROUND_GREEN:
            self._fillAttributes.append(ConsoleDataBlock.FOREGROUND_GREEN)
        if fillAttributes & ConsoleDataBlock.FOREGROUND_RED == ConsoleDataBlock.FOREGROUND_RED:
            self._fillAttributes.append(ConsoleDataBlock.FOREGROUND_RED)
        if fillAttributes & ConsoleDataBlock.FOREGROUND_INTENSITY == ConsoleDataBlock.FOREGROUND_INTENSITY:
            self._fillAttributes.append(ConsoleDataBlock.FOREGROUND_INTENSITY)
        if fillAttributes & ConsoleDataBlock.BACKGROUND_BLUE == ConsoleDataBlock.BACKGROUND_BLUE:
            self._fillAttributes.append(ConsoleDataBlock.BACKGROUND_BLUE)
        if fillAttributes & ConsoleDataBlock.BACKGROUND_GREEN == ConsoleDataBlock.BACKGROUND_GREEN:
            self._fillAttributes.append(ConsoleDataBlock.BACKGROUND_GREEN)
        if fillAttributes & ConsoleDataBlock.BACKGROUND_RED == ConsoleDataBlock.BACKGROUND_RED:
            self._fillAttributes.append(ConsoleDataBlock.BACKGROUND_RED)
        if fillAttributes & ConsoleDataBlock.BACKGROUND_INTENSITY == ConsoleDataBlock.BACKGROUND_INTENSITY:
            self._fillAttributes.append(ConsoleDataBlock.BACKGROUND_INTENSITY)

        self._popupFillAttributes = []
        popupFillAttributes = int.from_bytes(data[10:12], 'little', signed = False)
        if popupFillAttributes & ConsoleDataBlock.FOREGROUND_BLUE == ConsoleDataBlock.FOREGROUND_BLUE:
            self._popupFillAttributes.append(ConsoleDataBlock.FOREGROUND_BLUE)
        if popupFillAttributes & ConsoleDataBlock.FOREGROUND_GREEN == ConsoleDataBlock.FOREGROUND_GREEN:
            self._popupFillAttributes.append(ConsoleDataBlock.FOREGROUND_GREEN)
        if popupFillAttributes & ConsoleDataBlock.FOREGROUND_RED == ConsoleDataBlock.FOREGROUND_RED:
            self._popupFillAttributes.append(ConsoleDataBlock.FOREGROUND_RED)
        if popupFillAttributes & ConsoleDataBlock.FOREGROUND_INTENSITY == ConsoleDataBlock.FOREGROUND_INTENSITY:
            self._popupFillAttributes.append(ConsoleDataBlock.FOREGROUND_INTENSITY)
        if popupFillAttributes & ConsoleDataBlock.BACKGROUND_BLUE == ConsoleDataBlock.BACKGROUND_BLUE:
            self._popupFillAttributes.append(ConsoleDataBlock.BACKGROUND_BLUE)
        if popupFillAttributes & ConsoleDataBlock.BACKGROUND_GREEN == ConsoleDataBlock.BACKGROUND_GREEN:
            self._popupFillAttributes.append(ConsoleDataBlock.BACKGROUND_GREEN)
        if popupFillAttributes & ConsoleDataBlock.BACKGROUND_RED == ConsoleDataBlock.BACKGROUND_RED:
            self._popupFillAttributes.append(ConsoleDataBlock.BACKGROUND_RED)
        if popupFillAttributes & ConsoleDataBlock.BACKGROUND_INTENSITY == ConsoleDataBlock.BACKGROUND_INTENSITY:
            self._popupFillAttributes.append(ConsoleDataBlock.BACKGROUND_INTENSITY)

        self._screenBufferSizeX = int.from_bytes(data[12:14], 'little', signed = True)
        self._screenBufferSizeY = int.from_bytes(data[14:16], 'little', signed = True)

        self._windowSizeX = int.from_bytes(data[16:18], 'little', signed = True)
        self._windowSizeY = int.from_bytes(data[18:20], 'little', signed = True)

        self._windowOriginX = int.from_bytes(data[20:22], 'little', signed = True)
        self._windowOriginY = int.from_bytes(data[22:24], 'little', signed = True)

        self._fontSize = FontSize(data[32:36])
        self._fontFamily = FontFamily(data[36:40])
        self._fontWeight = int.from_bytes(data[40:44], 'little', signed = False)
        self._faceName = _nullTerminatedString(data[44:108], True)

        self._cursorSize = int.from_bytes(data[108:112], 'little', signed = False)

        self._fullScreen = int.from_bytes(data[112:116], 'little', signed = False) > 0x00000000
        self._quickEdit = int.from_bytes(data[116:120], 'little', signed = False) > 0x00000000
        self._insertMode = int.from_bytes(data[120:124], 'little', signed = False) > 0x00000000
        self._autoPosition = int.from_bytes(data[124:128], 'little', signed = False) > 0x00000000

        self._historyBufferSize = int.from_bytes(data[128:132], 'little', signed = False)
        self._numberOfHistoryBuffers = int.from_bytes(data[132:136], 'little', signed = False)
        self._historyNoDup = int.from_bytes(data[136:140], 'little', signed = False) > 0x00000000

        self._colorTable = data[140:204]

        return super().__init__()

    def _getFillAttributes(self):
        return self._fillAttributes
    def _getPopupFillAttributes(self):
        return self._popupFillAttributes
    def _getScreenBufferSizeX(self):
        return self._screenBufferSizeX
    def _getScreenBufferSizeY(self):
        return self._screenBufferSizeY
    def _getWindowSizeX(self):
        return self._windowSizeX
    def _getWindowSizeY(self):
        return self._windowSizeY
    def _getWindowOriginX(self):
        return self._windowOriginX
    def _getWindowOriginY(self):
        return self._windowOriginY
    def _getFontSize(self):
        return self._fontSize
    def _getFontFamily(self):
        return self._fontFamily
    def _getFontWeight(self):
        return self._fontWeight
    def _getFaceName(self):
        return self._faceName
    def _getCursorSize(self):
        return self._cursorSize
    def _getFullScreen(self):
        return self._fullScreen
    def _getQuickEdit(self):
        return self._quickEdit
    def _getInsertMode(self):
        return self._insertMode
    def _getAutoPosition(self):
        return self._autoPosition
    def _getHistoryBufferSize(self):
        return self._historyBufferSize
    def _getNumberOfHistoryBuffers(self):
        return self._numberOfHistoryBuffers
    def _getHistoryNoDup(self):
        return self._historyNoDup
    def _getColorTable(self):
        return self._colorTable

    fillAttributes = property(fget = _getFillAttributes, fset = None, fdel = None, doc = None)
    popupFillAttributes = property(fget = _getPopupFillAttributes, fset = None, fdel = None, doc = None)
    screenBufferSizeX = property(fget = _getScreenBufferSizeX, fset = None, fdel = None, doc = None)
    screenBufferSizeY = property(fget = _getScreenBufferSizeY, fset = None, fdel = None, doc = None)
    windowSizeX = property(fget = _getWindowSizeX, fset = None, fdel = None, doc = None)
    windowSizeY = property(fget = _getWindowSizeY, fset = None, fdel = None, doc = None)
    windowOriginX = property(fget = _getWindowOriginX, fset = None, fdel = None, doc = None)
    windowOriginY = property(fget = _getWindowOriginY, fset = None, fdel = None, doc = None)
    fontSize = property(fget = _getFontSize, fset = None, fdel = None, doc = None)
    fontFamily = property(fget = _getFontFamily, fset = None, fdel = None, doc = None)
    fontWeight = property(fget = _getFontWeight, fset = None, fdel = None, doc = None)
    faceName = property(fget = _getFaceName, fset = None, fdel = None, doc = None)
    cursorSize = property(fget = _getCursorSize, fset = None, fdel = None, doc = None)
    fullScreen = property(fget = _getFullScreen, fset = None, fdel = None, doc = None)
    quickEdit = property(fget = _getQuickEdit, fset = None, fdel = None, doc = None)
    insertMode = property(fget = _getInsertMode, fset = None, fdel = None, doc = None)
    autoPosition = property(fget = _getAutoPosition, fset = None, fdel = None, doc = None)
    historyBufferSize = property(fget = _getHistoryBufferSize, fset = None, fdel = None, doc = None)
    numberOfHistoryBuffers = property(fget = _getNumberOfHistoryBuffers, fset = None, fdel = None, doc = None)
    historyNoDup = property(fget = _getHistoryNoDup, fset = None, fdel = None, doc = None)
    colorTable = property(fget = _getColorTable, fset = None, fdel = None, doc = None)

class ConsoleFEDataBlock:
    _CONSOLE_FE_PROPS               = 0xA0000004

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize != 0x0000000C:
            raise ValueError('Not valid ConsoleFEDataBlock')
        if self._blockSignature != ConsoleFEDataBlock._CONSOLE_FE_PROPS:
            raise ValueError('Not valid ConsoleFEDataBlock')

        self._codePage = int.from_bytes(data[8:12], 'little', signed = False)

        return super().__init__()

    def _getCodePage(self):
        return self._codePage

    codePage = property(fget = _getCodePage, fset = None, fdel = None, doc = None)

class DarwinDataBlock:
    _DARWIN_PROPS                   = 0xA0000006

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize != 0x00000314:
            raise ValueError('Not valid DarwinDataBlock')
        if self._blockSignature != DarwinDataBlock._DARWIN_PROPS:
            raise ValueError('Not valid DarwinDataBlock')

        self._darwinDataANSI = _nullTerminatedString(data[8:268], False)
        self._darwinDataUnicode = _nullTerminatedString(data[268:788], True)

        return super().__init__()

    def _getDarwinDataANSI(self):
        return self._darwinDataANSI
    def _getDarwinDataUnicode(self):
        return self._darwinDataUnicode

    darwinDataANSI = property(fget = _getDarwinDataANSI, fset = None, fdel = None, doc = None)
    darwinDataUnicode = property(fget = _getDarwinDataUnicode, fset = None, fdel = None, doc = None)

class EnvironmentVariableDataBlock:
    _ENVIRONMENT_PROPS              = 0xA0000001

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize != 0x00000314:
            raise ValueError('Not valid EnvironmentVariableDataBlock')
        if self._blockSignature != EnvironmentVariableDataBlock._ENVIRONMENT_PROPS:
            raise ValueError('Not valid EnvironmentVariableDataBlock')

        self._targetANSI = _nullTerminatedString(data[8:268], False)
        self._targetUnicode = _nullTerminatedString(data[268:788], True)

        return super().__init__()

    def _getTargetANSI(self):
        return self._targetANSI
    def _getTargetUnicode(self):
        return self._targteUnicode

    targetANSI = property(fget = _getTargetANSI, fset = None, fdel = None, doc = None)
    targetUnicode = property(fget = _getTargetUnicode, fset = None, fdel = None, doc = None)

class IconEnvironmentDataBlock:
    _ICON_ENVIRONMENT_PROPS         = 0xA0000007

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize != 0x00000314:
            raise ValueError('Not valid IconEnvironmentDataBlock')
        if self._blockSignature != IconEnvironmentDataBlock._ICON_ENVIRONMENT_PROPS:
            raise ValueError('Not valid IconEnvironmentDataBlock')

        self._targetANSI = _nullTerminatedString(data[8:268], False)
        self._targetUnicode = _nullTerminatedString(data[268:788], True)

        return super().__init__()

    def _getTargetANSI(self):
        return self._targetANSI
    def _getTargetUnicode(self):
        return self._targteUnicode

    targetANSI = property(fget = _getTargetANSI, fset = None, fdel = None, doc = None)
    targetUnicode = property(fget = _getTargetUnicode, fset = None, fdel = None, doc = None)

class KnownFolderDataBlock:
    _KNOWN_FOLDER_PROPS             = 0xA000000B

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize != 0x0000001C:
            raise ValueError('Not valid KnownFolderDataBlock')
        if self._blockSignature != KnownFolderDataBlock._KNOWN_FOLDER_PROPS:
            raise ValueError('Not valid KnownFolderDataBlock')

        self._knownFolderID = UUID(bytes_le = data[8:24])
        self._offset = int.from_bytes(data[24:28], 'little', signed = False)

        return super().__init__()

    def _getKnownFolderID(self):
        return self._knownFolderID
    def _getOffset(self):
        return self._offset

    knownFolderID = property(fget = _getKnownFolderID, fset = None, fdel = None, doc = None)
    offset = property(fget = _getOffset, fset = None, fdel = None, doc = None)

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-oleps/
class TypedPropertyValue:
    VT_EMPTY            = 0x0000
    VT_NULL             = 0x0001
    VT_I2               = 0x0002
    VT_I4               = 0x0003
    VT_R4               = 0x0004
    VT_R8               = 0x0005
    VT_CY               = 0x0006
    VT_DATE             = 0x0007
    VT_BSTR             = 0x0008
    VT_ERROR            = 0x000A
    VT_BOOL             = 0x000B
    VT_DECIMAL          = 0x000E
    VT_I1               = 0x0010
    VT_UI1              = 0x0011
    VT_UI2              = 0x0012
    VT_UI4              = 0x0013
    VT_I8               = 0x0014
    VT_UI8              = 0x0015
    VT_INT              = 0x0016
    VT_UINT             = 0x0017
    VT_LPSTR            = 0x001E
    VT_LPWSTR           = 0x001F
    VT_FILETIME         = 0x0040
    # todo: 
    VT_CLSID            = 0x0048
    # todo:

    def __init__(self, data):
        self._type = int.from_bytes(data[0:2], 'little', signed = False)
        self._value = data[4:]

        return super().__init__()

    def _getValue(self):
        if self._type == TypedPropertyValue.VT_EMPTY:
            return None
        if self._type == TypedPropertyValue.VT_NULL:
            return None
        if self._type == TypedPropertyValue.VT_I2:
            return int.from_bytes(self._value[0:4], 'little', signed = True)
        if self._type == TypedPropertyValue.VT_I4:
            return int.from_bytes(self._value[0:4], 'little', signed = True)
        if self._type == TypedPropertyValue.VT_R4:
            return struct.unpack('<f', self._value[0:4])[0]
        if self._type == TypedPropertyValue.VT_R8:
            return struct.unpack('<f', self._value[0:8])[0]
        if self._type == TypedPropertyValue.VT_CY:
            return int.from_bytes(self._value[0:8], 'little', signed = True) / 10000
        if self._type == TypedPropertyValue.VT_DATE:
            return datetime(1899, 12, 31) + timedelta(days = struct.unpack('<f', self._value[0:8])[0])
        if self._type == TypedPropertyValue.VT_BSTR:
            size = int.from_bytes(self._value[0:4], 'little', signed = False)
            if length != 0:
                return _nullTerminatedString(self._value[4:], False)
            else:
                return ''
        if self._type == TypedPropertyValue.VT_ERROR:
            return int.from_bytes(self._value[0:4], 'little')
        if self._type == TypedPropertyValue.VT_BOOL:
            return int.from_bytes(self._value[0:4], 'little') != 0x00000000
        if self._type == TypedPropertyValue.VT_DECIMAL:                             # todo:
            return None
        if self._type == TypedPropertyValue.VT_I1:
            return int.from_bytes(self._value[0:4], 'little', signed = True)
        if self._type == TypedPropertyValue.VT_UI1:
            return int.from_bytes(self._value[0:4], 'little', signed = False)
        if self._type == TypedPropertyValue.VT_UI2:
            return int.from_bytes(self._value[0:4], 'little', signed = False)
        if self._type == TypedPropertyValue.VT_UI4:
            return int.from_bytes(self._value[0:4], 'little', signed = False)
        if self._type == TypedPropertyValue.VT_I8:
            return int.from_bytes(self._value[0:8], 'little', signed = True)
        if self._type == TypedPropertyValue.VT_UI8:
            return int.from_bytes(self._value[0:8], 'little', signed = False)
        if self._type == TypedPropertyValue.VT_INT:
            return int.from_bytes(self._value[0:4], 'little', signed = True)
        if self._type == TypedPropertyValue.VT_UINT:
            return int.from_bytes(self._value[0:4], 'little', signed = False)
        if self._type == TypedPropertyValue.VT_LPSTR:
            size = int.from_bytes(self._value[0:4], 'little', signed = False)
            if length != 0:
                return _nullTerminatedString(self._value[4:], False)
            else:
                return ''
        if self._type == TypedPropertyValue.VT_LPWSTR:
            length = int.from_bytes(self._value[0:4], 'little', signed = False)
            if length != 0:
                return _nullTerminatedString(self._value[4:], True)
            else:
                return ''
        if self._type == TypedPropertyValue.VT_FILETIME:
            return FILETIME(bytes = self._value)
        # todo:
        if self._type == TypedPropertyValue.VT_CLSID:
            return UUID(bytes_le = self._value[0:16])
        # todo:

        return None

    value = property(fget = _getValue, fset = None, fdel = None, doc = None)

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-propstore/
class SerializedPropertyValueStringName:
    def __init__(self, data):
        self._valueSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._nameSize = int.from_bytes(data[4:8], 'little', signed = False)

        self._name = _nullTerminatedString(data[9:9 + self._nameSize], True)
        self._value = TypedPropertyValue(data[9 + self._nameSize:]).value

        return super().__init__()

    def _getName(self):
        return self._name
    def _getValue(self):
        return self._value

    name = property(fget = _getName, fset = None, fdel = None, doc = None)
    value = property(fget = _getValue, fset = None, fdel = None, doc = None)

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-propstore/
class SerializedPropertyValueIntegerName:
    def __init__(self, data):
        self._valueSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._id = int.from_bytes(data[4:8], 'little', signed = False)

        self._value = TypedPropertyValue(data[9:]).value

        return super().__init__()

    def _getID(self):
        return self._id
    def _getValue(self):
        return self._value

    id = property(fget = _getID, fset = None, fdel = None, doc = None)
    value = property(fget = _getValue, fset = None, fdel = None, doc = None)

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-propstore/
class SerializedPropertyStorage:
    def __init__(self, data):
        self._storageSize = int.from_bytes(data[0:4], 'little', signed = False)

        self._verison = int.from_bytes(data[4:8], 'little', signed = False)
        if self._verison != 0x53505331:
            raise ValueError('Not valid SerializedPropertyStorage')

        self._formatID = UUID(bytes_le = data[8:24])

        self._propertyValues = dict()
        pos = 24
        valueSize = int.from_bytes(data[pos:pos + 4], 'little', signed = False)
        while pos < len(data):
            if valueSize == 0:
                break

            if self._formatID == UUID('D5CDD505-2E9C-101B-9397-08002B2CF9AE'):
                propertyValue = SerializedPropertyValueStringName(data[pos:pos + valueSize])
                self._propertyValues[propertyValue.name] = propertyValue.value
            else:
                propertyValue = SerializedPropertyValueIntegerName(data[pos:pos + valueSize])
                self._propertyValues[propertyValue.id] = propertyValue.value

            pos += valueSize
            valueSize = int.from_bytes(data[pos:pos + 4], 'little', signed = False)

        return super().__init__()

class PropertyStoreDataBlock:
    _PROPERTY_STORE_PROPS           = 0xA0000009

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize < 0x0000000C:
            raise ValueError('Not valid PropertyStoreDataBlock')
        if self._blockSignature != PropertyStoreDataBlock._PROPERTY_STORE_PROPS:
            raise ValueError('Not valid PropertyStoreDataBlock')

        self._propertyStore = SerializedPropertyStorage(data[8:])

        return super().__init__()

    def _getPropertyStore(self):
        return self._propertyStore

    propertyStore = property(fget = _getPropertyStore, fset = None, fdel = None, doc = None)

class ShimDataBlock:
    _SHIM_PROPS                     = 0xA0000008

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize < 0x00000088:
            raise ValueError('Not valid ShimDataBlock')
        if self._blockSignature != ShimDataBlock._SHIM_PROPS:
            raise ValueError('Not valid ShimDataBlock')

        self._layerName = _decodeString(data[8:], True)

        return super().__init__()

    def _getLayerName(self):
        return self._layerName

    layerName = property(fget = _getLayerName, fset = None, fdel = None, doc = None)

class SpecialFolderDataBlock:
    _SPECIAL_FOLDER_PROPS           = 0xA0000005

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize != 0x00000010:
            raise ValueError('Not valid SpecialFolderDataBlock')
        if self._blockSignature != SpecialFolderDataBlock._SPECIAL_FOLDER_PROPS:
            raise ValueError('Not valid SpecialFolderDataBlock')

        self._specialFolderID = int.from_bytes(data[8:12], 'little', signed = False)
        self._offset = int.from_bytes(data[12:16], 'little', signed = False)

        return super().__init__()

    def _getSpecialFolderID(self):
        return self._specialFolderID
    def _getOffset(self):
        return self._offset

    specialFolderID = property(fget = _getSpecialFolderID, fset = None, fdel = None, doc = None)
    offset = property(fget = _getOffset, fset = None, fdel = None, doc = None)

class TrackerDataBlock:
    _TRACKER_PROPS                  = 0xA0000003

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSize != 0x00000060:
            raise ValueError('Not valid TrackerDataBlock')
        if self._blockSignature != TrackerDataBlock._TRACKER_PROPS:
            raise ValueError('Not valid TrackerDataBlock')

        self._length = int.from_bytes(data[8:12], 'little', signed = False)
        if self._length != 0x00000058:
            raise ValueError('Not valid TrackerDataBlock')

        self._version = int.from_bytes(data[12:16], 'little', signed = False)
        if self._version != 0x00000000:
            raise ValueError('Not valid TrackerDataBlock')

        self._machineID = _nullTerminatedString(data[16:32], False)

        self._driod = [UUID(bytes_le = data[32:48]), UUID(bytes_le = data[48:64])]
        self._droidBirth = [UUID(bytes_le = data[64:80]), UUID(bytes_le = data[80:96])]

        return super().__init__()

    def getVersion(self):
        return self._version
    def getMachineID(self):
        return self._machineID
    def getDriod(self):
        return self._driod
    def getDroidBirth(self):
        return self._droidBirth

    version = property(fget = getVersion, fset = None, fdel = None, doc = None)
    machineID = property(fget = getMachineID, fset = None, fdel = None, doc = None)
    driod = property(fget = getDriod, fset = None, fdel = None, doc = None)
    droidBirth = property(fget = getDroidBirth, fset = None, fdel = None, doc = None)

class VistaAndAboveIDListDataBlock:
    _VISTA_AND_ABOVE_IDLIST_PROPS   = 0xA000000C

    def __init__(self, data):
        self._blockSize = int.from_bytes(data[0:4], 'little', signed = False)
        self._blockSignature = int.from_bytes(data[4:8], 'little', signed = False)

        if self._blockSignature != VistaAndAboveIDListDataBlock._VISTA_AND_ABOVE_IDLIST_PROPS:
            raise ValueError('Not valid VistaAndAboveIDListDataBlock')

        self._idList = _getItemIDList(data[8:])

        return super().__init__()

    def getIDList(self):
        return self._idList

    idList = property(fget = getIDList, fset = None, fdel = None, doc = None)

class ExtraData:
    def __init__(self, data):
        self._consoleProps = None
        self._consoleFEProps = None
        self._darwinProps = None
        self._environmentProps = None
        self._iconEnvironmentProps = None
        self._knownFolderProps = None
        self._propertyStoreProps = None
        self._shimProps = None
        self._specialFolderProps = None
        self._trackerProps = None
        self._vistaAndAboveIDListProps = None

        pos = 0
        blockSize = int.from_bytes(data[pos:pos + 4], 'little', signed = False)
        while blockSize >= 0x00000004:
            blockSignature = int.from_bytes(data[pos + 4:pos + 8], 'little', signed = False)

            if blockSignature == ConsoleDataBlock._CONSOLE_PROPS:
                self._consoleProps = ConsoleDataBlock(data[pos:pos + blockSize])
            elif blockSignature == ConsoleFEDataBlock._CONSOLE_FE_PROPS:
                self._consoleFEProps = ConsoleFEDataBlock(data[pos:pos + blockSize])
            elif blockSignature == DarwinDataBlock._DARWIN_PROPS:
                self._darwinProps = DarwinDataBlock(data[pos:pos + blockSize])
            elif blockSignature == EnvironmentVariableDataBlock._ENVIRONMENT_PROPS:
                self._environmentProps = EnvironmentVariableDataBlock(data[pos:pos + blockSize])
            elif blockSignature == IconEnvironmentDataBlock._ICON_ENVIRONMENT_PROPS:
                self._iconEnvironmentProps = IconEnvironmentDataBlock(data[pos:pos + blockSize])
            elif blockSignature == KnownFolderDataBlock._KNOWN_FOLDER_PROPS:
                self._knownFolderProps = KnownFolderDataBlock(data[pos:pos + blockSize])
            elif blockSignature == PropertyStoreDataBlock._PROPERTY_STORE_PROPS:
                self._propertyStoreProps = PropertyStoreDataBlock(data[pos:pos + blockSize])
            elif blockSignature == ShimDataBlock._SHIM_PROPS:
                self._shimProps = ShimDataBlock(data[pos:pos + blockSize])
            elif blockSignature == SpecialFolderDataBlock._SPECIAL_FOLDER_PROPS:
                self._specialFolderProps = SpecialFolderDataBlock(data[pos:pos + blockSize])
            elif blockSignature == TrackerDataBlock._TRACKER_PROPS:
                self._trackerProps = TrackerDataBlock(data[pos:pos + blockSize])
            elif blockSignature == VistaAndAboveIDListDataBlock._VISTA_AND_ABOVE_IDLIST_PROPS:
                self._vistaAndAboveIDListProps = VistaAndAboveIDListDataBlock(data[pos:pos + blockSize])

            pos += blockSize
            blockSize = int.from_bytes(data[pos:pos + 4], 'little', signed = False)

        return super().__init__()

    def _getConsoleProps(self):
        return self._consoleProps
    def _getConsoleFEProps(self):
        return self._consoleFEProps
    def _getDarwinProps(self):
        return self._darwinProps
    def _getEnvironmentProps(self):
        return self._environmentProps
    def _getIconEnvironmentProps(self):
        return self._iconEnvironmentProps
    def _getKnownFolderProps(self):
        return self._knownFolderProps
    def _getPropertyStoreProps(self):
        return self._propertyStoreProps
    def _getShimProps(self):
        return self._shimProps
    def _getSpecialFolderProps(self):
        return self._specialFolderProps
    def _getTrackerProps(self):
        return self._trackerProps
    def _getVistaAndAboveIDListProps(self):
        return self._vistaAndAboveIDListProps

    consoleProps = property(fget = _getConsoleProps, fset = None, fdel = None, doc = None)
    consoleFEProps = property(fget = _getConsoleFEProps, fset = None, fdel = None, doc = None)
    darwinProps = property(fget = _getDarwinProps, fset = None, fdel = None, doc = None)
    environmentProps = property(fget = _getEnvironmentProps, fset = None, fdel = None, doc = None)
    iconEnvironmentProps = property(fget = _getIconEnvironmentProps, fset = None, fdel = None, doc = None)
    knownFolderProps = property(fget = _getKnownFolderProps, fset = None, fdel = None, doc = None)
    propertyStoreProps = property(fget = _getPropertyStoreProps, fset = None, fdel = None, doc = None)
    shimProps = property(fget = _getShimProps, fset = None, fdel = None, doc = None)
    specialFolderProps = property(fget = _getSpecialFolderProps, fset = None, fdel = None, doc = None)
    trackerProps = property(fget = _getTrackerProps, fset = None, fdel = None, doc = None)
    vistaAndAboveIDListProps = property(fget = _getVistaAndAboveIDListProps, fset = None, fdel = None, doc = None)

class ShellLink:
    def __init__(self, lnkFile):
        self._linkPath = os.path.abspath(lnkFile)
        
        file = open(lnkFile, mode = 'rb')

        try:
            data = file.read(ShellLinkHeader._SHELL_LINK_HEADER_SIZE)
            self._shellLinkHeader = ShellLinkHeader(data)

            if self._shellLinkHeader.linkFlags.hasLinkTargetIDList:
                data = file.read(2)
                idListSize = int.from_bytes(data, 'little', signed = False)
                data += file.read(idListSize)

                self._linkTargetIdList = LinkTargetIDList(data)

            if self._shellLinkHeader.linkFlags.hasLinkInfo:
                data = file.read(4)
                linkInfoSize = int.from_bytes(data, 'little', signed = False)
                data = data + file.read(linkInfoSize - 4)

                self._linkInfo = LinkInfo(data)

            nameString = None
            relativePath = None
            workingDir = None
            commandLineArguments = None
            iconLocation = None

            if self._shellLinkHeader.linkFlags.hasName:
                data = file.read(2)
                count = int.from_bytes(data, 'little', signed = False)
                if self._shellLinkHeader.linkFlags.isUnicode:
                    count = count * 2
                data = file.read(count)
                nameString = _decodeString(data, self._shellLinkHeader.linkFlags.isUnicode)

            if self._shellLinkHeader.linkFlags.hasRelativePath:
                data = file.read(2)
                count = int.from_bytes(data, 'little', signed = False)
                if self._shellLinkHeader.linkFlags.isUnicode:
                    count = count * 2
                data = file.read(count)
                relativePath = _decodeString(data, self._shellLinkHeader.linkFlags.isUnicode)

            if self._shellLinkHeader.linkFlags.hasWorkingDir:
                data = file.read(2)
                count = int.from_bytes(data, 'little', signed = False)
                if self._shellLinkHeader.linkFlags.isUnicode:
                    count = count * 2
                data = file.read(count)
                workingDir = _decodeString(data, self._shellLinkHeader.linkFlags.isUnicode)

            if self._shellLinkHeader.linkFlags.hasArguments:
                data = file.read(2)
                count = int.from_bytes(data, 'little', signed = False)
                if self._shellLinkHeader.linkFlags.isUnicode:
                    count = count * 2
                data = file.read(count)
                commandLineArguments = _decodeString(data, self._shellLinkHeader.linkFlags.isUnicode)

            if self._shellLinkHeader.linkFlags.hasIconLocation:
                data = file.read(2)
                count = int.from_bytes(data, 'little', signed = False)
                if self._shellLinkHeader.linkFlags.isUnicode:
                    count = count * 2
                data = file.read(count)
                iconLocation = _decodeString(data, self._shellLinkHeader.linkFlags.isUnicode)

            self._stringData = StringData(nameString, relativePath, workingDir, commandLineArguments, iconLocation)

            data = file.read()
            self._extraData = ExtraData(data)

        except:
            raise ValueError('Not valid Shell Link File')
        finally:
            file.close()
        
        return super().__init__()

    def _getLinkPath(self):
        return self._linkPath
    def _getLinkFile(self):
        return os.path.basename(self._linkPath)
    def _getHeader(self):
        return self._shellLinkHeader
    def _getLinkTargetIdList(self):
        return self._linkTargetIdList
    def _getLinkInfo(self):
        return self._linkInfo
    def _getStringData(self):
        return self._stringData
    def _getExtraData(self):
        return self._extraData

    linkPath = property(fget = _getLinkPath, fset = None, fdel = None, doc = None)
    linkFile = property(fget = _getLinkFile, fset = None, fdel = None, doc = None)
    shellLinkHeader = property(fget = _getHeader, fset = None, fdel = None, doc = None)
    linkTargetIdList = property(fget = _getLinkTargetIdList, fset = None, fdel = None, doc = None)
    linkInfo = property(fget = _getLinkInfo, fset = None, fdel = None, doc = None)
    stringData = property(fget = _getStringData, fset = None, fdel = None, doc = None)
    extraData = property(fget = _getExtraData, fset = None, fdel = None, doc = None)


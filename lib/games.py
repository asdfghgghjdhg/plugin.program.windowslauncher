import os

import xml.etree.ElementTree as elementtree

import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui

import lib.utils

from lib.shelllink import ShellLink
from lib.urlfile import UrlFile

LOG_TAG = 'plugin.program.windowslauncher'

class Shortcut:
    def __init__(self, path: str):
        path = path.strip()

        if path == '':
            raise ValueError('Invalid shortcut file')

        if not xbmcvfs.exists(xbmcvfs.translatePath(path)):
            raise ValueError('Invalid shortcut file')

        link = None
        try:
            if path[-4:] == '.lnk':
                link = ShellLink(xbmcvfs.translatePath(path))
            elif path[-4:] == '.url':
                link = UrlFile(xbmcvfs.translatePath(path))
        except:
            raise ValueError('Invalid shortcut file')

        if not link: raise ValueError('Invalid shortcut file')

        self._name = link.file
        self._lnkFile = link.path
        self._title = self._name[0:-4]
        self._target = ''
        self._arguments = ''
        self._workingDir = ''

        if isinstance(link, ShellLink):
            #if link.shellLinkHeader.linkFlags.hasName:
            #    self._title = link.stringData.nameString

            if link.shellLinkHeader.linkFlags.hasLinkInfo:
                self._target = link.linkInfo.localBasePath
            elif link.shellLinkHeader.linkFlags.hasName:
                self._target = link.stringData.nameString

            if link.stringData.commandLineArguments: self._arguments = link.stringData.commandLineArguments
            if link.stringData.workingDir: self._workingDir = link.stringData.workingDir
        else:
            self._target = link.urlData['url']
            self._workingDir = link.urlData.get('workingdirectory', '')

        return super().__init__()

    @property
    def path(self):
        return self._lnkFile

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._title

    @property
    def target(self):
        return self._target

    @property
    def workingDir(self):
        return self._workingDir

    @property
    def arguments(self):
        return self._arguments

    def getListItem(self):
        listItem = xbmcgui.ListItem(self._name, path = self._lnkFile)
        listItem.setProperty('IsPlayable', 'false')

        menuItemStartGame = (xbmcaddon.Addon().getLocalizedString(30921), 'RunPlugin(plugin://plugin.program.windowslauncher?action=start&game={})'.format(self._title))
        menuItemUpdateInfo = (xbmcaddon.Addon().getLocalizedString(30912), 'RunPlugin(plugin://plugin.program.windowslauncher?action=update_info&game={})'.format(self._title))
        listItem.addContextMenuItems([menuItemStartGame, menuItemUpdateInfo])

        return listItem

class Game(Shortcut):
    def __init__(self, path: str, metadataPath: str):
        result = super().__init__(path)

        self._nfoFile = metadataPath.strip()
        if self.hasMetadata: self._name = self._title

        self._altTitle = None
        self._platform = None
        self._publisher = None
        self._developer = None
        self._overview = None
        self._genres = None
        self._year = None
        self._rating = None
        self._thumbs = None
        self._fanarts = None

        self._scraperId = None

        self._readMetadata()

        return result

    def __str__(self):
        result = 'Game {{name: \\\'{}\\\', title: \\\'{}\\\', id: {}'
        return result.format(self._name, self._title, self._scraperId)

    def _getHasMetadata(self):
        if not self._nfoFile or self._nfoFile == '':
            return False

        return xbmcvfs.exists(xbmcvfs.translatePath(self._nfoFile))

    def _readMetadata(self):
        if not self.hasMetadata:
            lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'shortcut "{}" has no metadata', self._name)
            return

        try:
            metadata = elementtree.parse(xbmcvfs.translatePath(self._nfoFile))
            root = metadata.getroot()
        except:
            lib.utils.log(LOG_TAG, xbmc.LOGERROR, 'cannnot open metadata file "{}"', self._nfoFile)
            return

        if root.tag != 'game':
            lib.utils.log(LOG_TAG, xbmc.LOGERROR, 'wrong metadata file "{}"', self._nfoFile)
            return

        self._title = root.findtext('title', self._title)
        self._platform = root.findtext('platform')
        self._developer = root.findtext('developer')
        self._publisher = root.findtext('publisher')
        self._overview = root.findtext('overview')
        self._altTitle = root.findtext('alt_title')
                
        self._genres = []
        for element in root.iterfind('genre'):
            if element.text and element.text != '':
                self._genres.append(element.text)
        if len(self._genres) == 0: self._genres = None

        try:
            self._year = int(root.findtext('year'))
        except:
            self._year = None

        self._thumbs = dict()
        for element in root.iterfind('thumb'):
            if element.text and element.text != '' and element.get('aspect'):
                self._thumbs[element.attrib['aspect']] = element.text
        if len(self._thumbs) == 0: self._thumbs = None

        self._fanarts = []
        fanart = root.find('fanart')
        if fanart:
            for element in fanart.iterfind('thumb'):
                if element.text and element.text != '':
                    self._fanarts.append({'image': element.text, 'preview': element.get('preview', '')})
        if len(self._fanarts) == 0: self._fanarts = None

        self._rating = dict()
        element = root.find('rating')
        try: 
            self._rating['rating'] = float(element.text)
            self._rating['type'] = element.get('type', '')
            self._rating['votes'] = int(element.get('votes', '0'))
        except:
                pass
        if len(self._rating) == 0: self._rating = None
        
        self._scraperId = root.findtext('id')

    def _writeMetadata(self):
        root = elementtree.Element('game')

        elementtree.SubElement(root, 'title').text = self._title
        if self._altTitle:
            elementtree.SubElement(root, 'alt_title').text = self._altTitle
        if self._platform:
            elementtree.SubElement(root, 'platform').text = self._platform
        if self._developer:
            elementtree.SubElement(root, 'developer').text = self._developer
        if self._publisher:
            elementtree.SubElement(root, 'publisher').text = self._publisher
        if self._overview:
            elementtree.SubElement(root, 'overview').text = self._overview
        if self._year:
            elementtree.SubElement(root, 'year').text = str(self._year)

        if self._genres:
            for genre in self._genres:
                element = elementtree.SubElement(root, 'genre')
                element.text = genre

        if self._thumbs:
            for aspect, image in self._thumbs.items():
                element = elementtree.SubElement(root, 'thumb', {'spoof': '', 'cache': '', 'aspect': aspect, 'preview': ''})
                element.text = image


        fanartElement = elementtree.SubElement(root, 'fanart')
        if self._fanarts:
            for fanart in self._fanarts:
                element = elementtree.SubElement(fanartElement, 'thumb', {'colors': '', 'preview': fanart['preview']})
                element.text = fanart['image']

        if self._rating:
            element = elementtree.SubElement(root, 'rating', {'type': self._rating['type'], 'votes': str(self._rating['votes'])})
            element.text = str(self._rating['rating'])
        
        if self._scraperId:
            elementtree.SubElement(root, 'id').text = str(self._scraperId)

        # todo: save images locally

        metadata = elementtree.ElementTree(root)
        try:
            metadata.write(xbmcvfs.translatePath(self._nfoFile), 'utf-8', True)
        except Exception as e:
            lib.utils.log(LOG_TAG, xbmc.LOGERROR, 'cannot write metadata file "{}" - {}', self._nfoFile, e)
            return False

        return True

    def _removeMetadata(self):
        if xbmcvfs.exists(xbmcvfs.translatePath(self._nfoFile)):
            try:
                xbmcvfs.delete(self._nfoFile)
            except:
                lib.utils.log(LOG_TAG, xbmc.LOGERROR, 'cannot delete metadata file "{}"', self._nfoFile)
                return False

        self._hasMetadata = False
        self._altTitle = None
        self._platform = None
        self._publisher = None
        self._developer = None
        self._overview = None
        self._genres = None
        self._year = None
        self._ratings = None
        self._thumbs = None
        self._fanarts = None

        self._scraperId = None

        return True

    @property
    def nfoFile(self):
        return self._nfoFile

    @property
    def hasMetadata(self):
        return self._getHasMetadata()

    @property
    def platform(self):
        return self._platform

    @property
    def developer(self):
        return self._developer

    @property
    def publisher(self):
        return self._publisher

    @property
    def overview(self):
        return self._overview

    @property
    def year(self):
        return self._year

    @property
    def genres(self):
        return self._genres

    @property
    def thumbs(self):
        return self._thumbs

    @property
    def fanarts(self):
        return self._fanarts

    @property
    def rating(self):
        return self._rating

    @property
    def scraperId(self):
        return self._scraperId

    def saveMetadata(self, newMetadata: dict = None):
        if isinstance(newMetadata, dict):
            self._scraperId = newMetadata.get('id', self._scraperId)
            self._title = newMetadata.get('title', self._title)

            self._altTitle = newMetadata.get('altTitle')
            self._developer = newMetadata.get('developer')
            self._publisher = newMetadata.get('publisher')
            self._platform = newMetadata.get('platform')
            self._year = newMetadata.get('year')
            self._overview = newMetadata.get('overview')
            self._genres = newMetadata.get('genres')
            self._rating = newMetadata.get('rating')
            self._thumbs = newMetadata.get('thumbs')
            self._fanarts = newMetadata.get('fanarts')

        return self._writeMetadata()

    def removeMetadata(self):
        return self._removeMetadata()

    def getListItem(self):
        listItem = super().getListItem()
        
        if self.hasMetadata:
            listItem.setLabel(self._title)
            if self._altTitle: listItem.setLabel2(self._altTitle)
            listItem.setProperty('IsPlayable', 'True')

            tag = listItem.getVideoInfoTag()
            tag.setTitle(self._title)
            if self._genres: tag.setGenres(self._genres)
            if self._overview: tag.setPlot(self._overview)
            if self._year: tag.setYear(self._year)

            if self._publisher and self._developer:
                tag.setStudios([self._developer, self._publisher])
            elif self._publisher:
                tag.setStudios([self._publisher])
            elif self._developer:
                tag.setStudios([self._developer])

            tag.setOriginalTitle(self._title)
            tag.setDbId(0)
            tag.setUniqueID('')

            if self._rating:
                tag.setRating(self._rating['rating'], self._rating['votes'], self._rating['type'], True)

            tag.setPath(self._lnkFile)

            if self._fanarts:
                for fanart in self._fanarts:
                    tag.addAvailableArtwork(fanart['image'], 'fanart', fanart['preview'])

            tag = listItem.getGameInfoTag()
            tag.setTitle(self._title)
            if self._platform: tag.setPlatform(self._platform)
            if self._genres: tag.setGenres(self._genres)
            if self._publisher: tag.setPublisher(self._publisher)
            if self._developer: tag.setDeveloper(self._developer)
            if self._overview: tag.setOverview(self._overview)
            if self._year: tag.setYear(self._year)

            if self._thumbs:
                for aspect, image in self._thumbs.items():
                    listItem.setArt({aspect : image})

            if self._fanarts:
                listItem.setAvailableFanart(self._fanarts)

            listItem.setProperty('OverrideInfotag', 'True')

            menuItemStartGame = (xbmcaddon.Addon().getLocalizedString(30921), 'RunPlugin(plugin://plugin.program.windowslauncher?action=start&game={})'.format(self._name))
            menuItemShowInfo = (xbmcaddon.Addon().getLocalizedString(30902), 'RunPlugin(plugin://plugin.program.windowslauncher?action=show_info&game={})'.format(self._name))
            menuItemUpdateInfo = (xbmcaddon.Addon().getLocalizedString(30903), 'RunPlugin(plugin://plugin.program.windowslauncher?action=update_info&game={})'.format(self._name))
            menuItemRemoveLink = (xbmcaddon.Addon().getLocalizedString(30904), 'RunPlugin(plugin://plugin.program.windowslauncher?action=remove&game={})'.format(self._name))
            listItem.addContextMenuItems([menuItemStartGame, menuItemShowInfo, menuItemUpdateInfo, menuItemRemoveLink])

        return listItem

class GamesLibrary():
    def __init__(self):
        self._metadataPath = os.path.join(xbmcaddon.Addon().getAddonInfo('profile'), 'metadata')
        if not xbmcvfs.exists(xbmcvfs.translatePath(self._metadataPath)):
            xbmcvfs.mkdir(self._metadataPath)

        return super().__init__()

    def _getGames(self):
        games = []

        if self.source == '':
            lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'library source not set')
            return games

        dirs, files = xbmcvfs.listdir(self.metadataPath)
        for file in files:
            if file[-4:] != '.nfo':
                lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'file "{}" is not metadata file, skipping', file)
                continue
            
            try:
                game = Game(os.path.join(self.source, file[0:-4] + '.lnk'), os.path.join(self.metadataPath, file))
                games.append(game)
            except:
                try:
                    game = Game(os.path.join(self.source, file[0:-4] + '.url'), os.path.join(self.metadataPath, file))
                    games.append(game)
                except:
                    lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'error openning shortcut file for game "{}"', file[0:-4])
                    continue

        return games

    def _getShortcuts(self):
        shortcuts = []

        if self.source == '':
            lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'library source not set')
            return shortcuts

        dirs, files = xbmcvfs.listdir(self.source)
        for file in files:
            if file[-4:].lower() != '.lnk' and file[-4:].lower() != '.url':
                lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'file "{}" is not shortcut file, skipping', file)
                continue

            try:
                shortcut = Game(os.path.join(self.source, file), os.path.join(self.metadataPath, file[0:-4] + '.nfo'))
                shortcuts.append(shortcut)
            except:
                lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'error openning shortcut file "{}"', file)
                continue

        return shortcuts

    def _getSource(self):
        return xbmcaddon.Addon().getSettings().getString('source').strip()

    def _setSource(self, source: str):
        #xbmcaddon.Addon().getSettings().setString('source', source)

        #saving changes immediatly
        try:
            metadata = elementtree.parse(xbmcvfs.translatePath(os.path.join(xbmcaddon.Addon().getAddonInfo('profile'), 'settings.xml')))
            root = metadata.getroot()
        except Exception as e:
            utils.log(LOG_TAG, xbmc.LOGWARNING, 'cannot open settings file, trying to create new one')
            root = ElementTree.Element('settings', {'version': '2'})

        success = False
        for element in root.iterfind('setting'):
            if element.get('id', '') == 'source':
                element.text = source
                success = True
                break
        if not success:
            elementtree.SubElement(root, 'setting', {'id': 'source'}).text = result

        tree = elementtree.ElementTree(root)
        try:
            tree.write(xbmcvfs.translatePath(os.path.join(xbmcaddon.Addon().getAddonInfo('profile'), 'settings.xml')), 'utf-8', False)
        except Exception as e:
            utils.log(LOG_TAG, xbmc.LOGERROR, 'cannot write settings file - ', e)

    @property
    def shortcuts(self):
        return self._getShortcuts()

    @property
    def games(self):
        return self._getGames()

    @property
    def source(self):
        return self._getSource()

    @source.setter
    def source(self, value: str):
        self._setSource(value)

    @property
    def metadataPath(self):
        return self._metadataPath

    def clear(self):
        dirs, files = xbmcvfs.listdir(self.metadataPath)
        for file in files:
            if file[-4:] != '.nfo':
                lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'file "{}" is not metadata file, skipping', file)
                continue

            xbmcvfs.delete(os.path.join(self.metadataPath, file))
            lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'metadata file "{}" deleted', file)

    def getGame(self, name: str):
        try:
            game = Game(os.path.join(self.source, name + '.lnk'), os.path.join(self.metadataPath, name + '.nfo'))
            return game
        except:
            try:
                game = Game(os.path.join(self.source, name + '.url'), os.path.join(self.metadataPath, name + '.nfo'))
                return game
            except:
                lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'error openning shortcut file for game "{}"', name)

        return None
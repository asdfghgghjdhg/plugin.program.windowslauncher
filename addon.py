import sys
import os

import ctypes
import ctypes.wintypes
#import subprocess

import re
import json
import requests
import urllib.parse as Parse
import xml.etree.ElementTree as ElementTree

from html.parser import HTMLParser
from lib.shelllink import ShellLink

import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmc
import xbmcvfs

#import web_pdb; web_pdb.set_trace()

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

class Game:
    SCRAPER_SOURCE_PLAYGROUND       = 0x01

    def __init__(self, name):
        self.addonHandle = int(sys.argv[1])
        self.sourcePath = xbmcaddon.Addon().getSettingString('source')
        self.addonPath = xbmcaddon.Addon().getAddonInfo('path')
        self.metadataPath = os.path.join(xbmcaddon.Addon().getAddonInfo('profile'), 'metadata')

        if not name or name == '': raise ValueError('Invalid game source')

        exists = False;
        for root, dirs, files in os.walk(xbmcvfs.translatePath(self.sourcePath)):
            for file in files:
                if file.lower() == name.lower() + '.lnk':
                    name = file[0:-4]
                    exists = True
                    break

        if not exists: raise ValueError('Invalid game source')

        try:
            link = ShellLink(xbmcvfs.translatePath(os.path.join(self.sourcePath, name + '.lnk')))
        except:
            raise ValueError('Invalid game source')
        
        if not link.shellLinkHeader.linkFlags.hasLinkInfo:
            raise ValueError('Invalid game source')
        #if not link.linkInfo.linkInfoFlags.volumeIDAndLocalBasePath:
        #    raise ValueError('Invalid game source')
        #if link.linkInfo.localBasePath == '':
        #    raise ValueError('Invalid game source')

        self._name = link.linkFile[0:-4]

        if link.shellLinkHeader.linkFlags.hasName:
            self._title = link.stringData.nameString
        else:
            self._title = self._name

        self._target = link.linkInfo.localBasePath

        self._arguments = ''
        if link.stringData.commandLineArguments: self._arguments = link.stringData.commandLineArguments
        self._workingDir = ''
        if link.stringData.workingDir: self._workingDir = link.stringData.workingDir

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
        
        self._readMetadata()

        return super().__init__()

    def __str__(self):
        result = 'Game {{name: \\\'{}\\\', title: \\\'{}\\\', hasMetadata: {}, playgroundId: {}'
        return result.format(self._name, self._title, self._hasMetadata, self._playgroundId)

    def _readMetadata(self):
        if not xbmcvfs.exists(self.nfoFile): return

        try:
            metadata = ElementTree.parse(self.nfoFile)
            root = metadata.getroot()
        except:
            return

        if root.tag != 'game': return

        self._hasMetadata = True

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

        #pgElement = root.find('playground')
        #if pgElement:
        #    try:
        #        pg_id = int(pgElement.get('id'))
        #    except:
        #        pg_id = None
        #    pg_slug = pgElement.get('slug')
        #    if pg_id and pg_slug:
        #        self._playgroundId = {'id': pg_id, 'slug': pg_slug}

        #    self._ratings = dict()
        #    for element in pgElement.iterfind('rating'):
        #        if element.text and element.text != '' and element.get('name'):
        #            self._ratings[element.attrib['name']] = element.text
        #    if len(self._ratings) == 0: self._ratings = None

        self._scraperId = root.findtext('id')

    def _writeMetadata(self):
        if not self._hasMetadata: return False

        try:
            metadata = ElementTree.parse(xbmcvfs.translatePath(os.path.join(self.addonPath, 'resources', 'template.nfo')))
            root = metadata.getroot()
        except:
            return False

        root.find('title').text = self._title
        if self._platform: root.find('platform').text = self._platform
        if self._developer: root.find('developer').text = self._developer
        if self._publisher: root.find('publisher').text = self._publisher
        if self._overview: root.find('overview').text = self._overview
        if self._year: root.find('year').text = str(self._year)
        if self._altTitle: root.find('alt_title').text = str(self._altTitle)
        
        for element in root.findall('genre'):
            root.remove(element)
        if self._genres:
            for genre in self._genres:
                element = ElementTree.SubElement(root, 'genre')
                element.text = genre

        for element in root.findall('thumb'):
            root.remove(element)
        if self._thumbs:
            for aspect, image in self._thumbs.items():
                element = ElementTree.SubElement(root, 'thumb', {'spoof': '', 'cache': '', 'aspect': aspect, 'preview': ''})
                element.text = image

        fanartElement = root.find('fanart')
        for element in fanartElement.findall('thumb'):
            fanartElement.remove(element)
        if self._fanarts:
            for fanart in self._fanarts:
                element = ElementTree.SubElement(fanartElement, 'thumb', {'colors': '', 'preview': fanart['preview']})
                element.text = fanart['image']

        #pgElement = root.find('playground')
        #if self._playgroundId:
        #    pgElement.set('id', str(self._playgroundId['id']))
        #    pgElement.set('slug', self._playgroundId['slug'])
        #for element in pgElement.findall('rating'):
        #    pgElement.remove(element)
        #if self._ratings:
        #    for name, value in self._ratings.items():
        #        element = ElementTree.SubElement(pgElement, 'rating', {'name': name})
        #        element.text = value

        if self._scraperId: root.find('id').text = str(self._scraperId)

        # todo: save images locally

        try:
            metadata.write(self.nfoFile, 'utf-8', True)
        except:
            return False

        return True

    def _removeMetadata(self):
        if not self._hasMetadata: return True

        try:
            xbmcvfs.delete(self.nfoFile)
        except:
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

        self._playgroundId = None

        return True

    def _scrapeFromPlayground(self):
        if not self._scraperId: return False

        response = requests.get('https://www.playground.ru/gallery/{}/'.format(self._scraperId))
        if not response.ok: return False
        
        gameInfo = re.search('<div class="modal-content" style="background-image: url\(.+\)">[\s\S]*?(?=<script>)', response.text)
        if not gameInfo: return False

        title = re.findall('<div class="game-title">\s+<a href=".+">\s+(.+)\s+(<span class="game-title-alt">(.+)</span>)?\s+</a>', gameInfo.group(0))
        if title:
            self._hasMetadata = True
            self._title = title[0][0].strip()
            self._altTitle = title[0][2].strip()
        else: return False

        self._thumbs = dict()
        poster = re.findall('<div class="modal-content" style="background-image: url\((.+)\)">', gameInfo.group(0))
        if poster:
            self._thumbs['poster'] = poster[0].strip()
        thumb = re.findall('<div class="game-poster">[\s\S]+<img.+src="(.+?)"', gameInfo.group(0))
        if thumb:
            self._thumbs['thumb'] = thumb[0].strip()

        self._genres = []
        genres = re.findall('<a class="item" href="\/games\/.+?">(.+?)<\/a>', gameInfo.group(0))
        if genres:
            for genre in genres:
                self._genres.append(genre.strip())
        if len(self._genres) == 0: self._genres = None

        self._year = None
        self._platform = None
        dates = re.findall('<div class="release-item">\s+?<span class="date">([\s\S]+?)<\/span>\s+<a class="platform-item (.+)" href="\/games\/.+">', gameInfo.group(0))
        if dates:
            for platform in dates:
                if platform[1].strip() == 'pc':
                    try:
                        self._year = int(platform[0].strip()[-4:])
                        self._platform = 'PC'
                    except:
                        pass

        self._developer = None
        developer = re.findall('<a title="все игры этого разработчика"\s+href="\/games\?company=.+">\s+<span>(.+?)<\/span>', gameInfo.group(0))
        if developer:
            self._developer = developer[0].strip()

        self._publisher = None
        publisher = re.findall('<a title="все игры этого издателя"\s+href="\/games\?company=.+">\s+<span>(.+?)<\/span>', gameInfo.group(0))
        if publisher:
            self._publisher = publisher[0].strip()

        self._ratings = dict()
        ratings = re.findall('<span class="value">\s*(.+)?<\/span>\s+(.+?)\s+<\/div>', gameInfo.group(0))
        if ratings:
            for rating in ratings:
                self._ratings[rating[1].strip()] = rating[0].strip()
        if len(self._ratings) == 0: self._ratings = None

        self._overview = None
        plot = re.findall('<div class="description-wrapper">([\s\S]+?)<\/div>', gameInfo.group(0))
        if plot:
            plot = re.sub('<.*?>', '', plot[0].strip().replace('<br>', '\n').replace('<br/>', '\n'))
            self._overview = HTMLParser().unescape(plot)

        self._fanarts = []
        screenshotsBlock = re.search('<div class="module clearfix screenshots-module">(.+?)(?=<\/div><\/div><\/div>)', response.text)
        if screenshotsBlock:
            screenshots = re.findall('<div class="gallery-item thumb"><a data-fancybox="gallery" href="(.+?)".+?<img src="(.+?)" alt="', screenshotsBlock.group(0))
            if screenshots:
                for screenshot in screenshots:
                    self._fanarts.append({'image': screenshot[0], 'preview': screenshot[1]})

        if len(self._fanarts) > 0:
            self._thumbs['fanart'] = self._fanarts[0]['image']
        else:
            self._fanarts = None

        if len(self._thumbs) == 0: self._thumbs = None

        return True

    @property
    def name(self):
        return self._name

    @property
    def lnkFile(self):
        return xbmcvfs.translatePath(os.path.join(self.sourcePath, self._name + '.lnk'))

    @property
    def nfoFile(self):
        return xbmcvfs.translatePath(os.path.join(self.metadataPath, self._name + '.nfo'))

    @property
    def title(self):
        return self._title

    @property
    def hasMetadata(self):
        return self._hasMetadata

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
    def ratings(self):
        return self._ratings

    @property
    def scraperId(self):
        return self._scraperId

    def scrapeMetadata(self, source, newScraperId = None):
        if newScraperId:
            self._scraperId = newScraperId

        if source == Game.SCRAPER_SOURCE_PLAYGROUND: return self._scrapeFromPlayground()

        return False

    def saveMetadata(self):
        return self._writeMetadata()

    def removeMetadata(self):
        return self._removeMetadata()

    def getListItem(self):
        altTitle = ''
        if self._altTitle: altTitle = self._altTitle

        listItem = xbmcgui.ListItem(self._title, altTitle, 'plugin://plugin.program.windowslinks?action=start&game={}'.format(self._name))
        listItem.setProperty('IsPlayable', 'True')

        if self._hasMetadata:
            tag = listItem.getVideoInfoTag()
            tag.setTitle(self._title)
            if self._genres: tag.setGenres(self._genres)
            if self._overview: tag.setPlot(self._overview)
            if self._year: tag.setYear(self._year)

            if self._publisher and self._developer:
                tag.setStudios([self._developer, self._publisher])
            elif self._publisher:
                tag.setStudios([self._publisher])
            elif game.developer:
                tag.setStudios([self._developer])

            tag.setOriginalTitle(self._title)
            tag.setDbId(0)
            tag.setUniqueID('')

            tag.setPath(self.lnkFile)

            #if self._ratings:
            #    ratings = dict()
            #    for type, rating in self._ratings.items():
            #        ratings[type] = (8.9, 0)
            #    tag.setRatings(ratings)

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

        return listItem

    def start(self):
        result = False

        listitem = xbmcgui.ListItem(path = os.path.join(self.addonPath, 'resources', 'media', 'blank.png'))
        
        try:
            #ctypes.windll.shell32.ShellExecuteW(None, 'open', self._target, self._arguments, self._workingDir, 1)

            #seInfo = ShellExecuteInfo(fMask = 0x00000140, lpVerb = 'open'.encode('utf-8'), lpFile = self._target.encode('utf-8'), lpParameters = self._arguments.encode('utf-8'), lpDirectory = self._workingDir.encode('utf-8'), nShow = 5)
            seInfo = ShellExecuteInfo(fMask = 0x00000140, lpVerb = 'open'.encode('utf-8'), lpFile = self.lnkFile.encode('utf-8'), nShow = 5)
            if shellExecuteEx(ctypes.byref(seInfo)): result = True
        except:
            raise
            result = False

        if result:
            try:
                # wait for 30 seconds for game to run
                waitForSingleObject(seInfo.hProcess, 30000)
                closeHandle(seInfo.hProcess)
            except:
                raise

        xbmcplugin.setResolvedUrl(self.addonHandle, result, listitem)
        return result

class Addon(xbmcaddon.Addon):
    def __init__(self):
        self.url = sys.argv[0]
        self.handle = int(sys.argv[1])

        self.params = dict(Parse.parse_qsl(sys.argv[2][1:]))

        self.source = self.getSettingString('source')
        self.libraryPath = os.path.join(self.getAddonInfo('profile'), 'metadata')
        if not xbmcvfs.exists(self.libraryPath):
            xbmcvfs.mkdir(self.libraryPath)
        
        self.selectedScraper = self.getSettingInt('scraper')
        self.contentType = self.getSettingString('content_type').lower()
        
        return super().__init__(id = None)

    def _getSourceLinksList(self):
        result = []

        for root, dirs, files in os.walk(xbmcvfs.translatePath(self.source)):
            for file in files:
                try:
                    game = Game(file[0:-4])
                    result.append(game)
                except:
                    continue

        return result

    def _searchPlayground(self, name):
        result = []

        response = requests.get('https://www.playground.ru/api/game.search?query={}&include_addons=0'.format(Parse.quote_plus(name)))
        if response.ok:
            try:
                data = json.loads(response.text)
            except:
                return result

            if isinstance(data, list):
                for element in data:
                    if isinstance(element, dict):
                        id = element.get('slug', '').strip()
                        name = element.get('name', '').strip()
                        image = element.get('image', '').strip()
                        if id != '' and name != '':
                            result.append({'id': id, 'name': name, 'image': image})

        return result

    def _scraperSearch(self, name):
        if self.selectedScraper == Game.SCRAPER_SOURCE_PLAYGROUND: return self._searchPlayground(name)

        return []

    def listItems(self):
        if self.source == '':
            xbmcgui.Dialog().ok(self.getAddonInfo('name'), self.getLocalizedString(30901))
            xbmcgui.Window().close()
            self.openSettings()
            return

        xbmcplugin.setContent(self.handle, self.contentType)
        xbmcplugin.setPluginCategory(self.handle, self.getAddonInfo('name'))

        games = self._getSourceLinksList()
        for game in games:
            if not game.hasMetadata: continue

            listItem = game.getListItem()
            
            menuItemShowInfo = (self.getLocalizedString(30902), 'RunPlugin({}?action=show_info&game={})'.format(self.url, game.name))
            menuItemUpdateInfo = (self.getLocalizedString(30903), 'RunPlugin({}?action=update_info&game={})'.format(self.url, game.name))
            menuItemRemoveLink = (self.getLocalizedString(30904), 'RunPlugin({}?action=remove&game={})'.format(self.url, game.name))
            listItem.addContextMenuItems([menuItemShowInfo, menuItemUpdateInfo, menuItemRemoveLink])

            xbmcplugin.addDirectoryItem(self.handle, '{}?action=start&game={}'.format(self.url, game.name), listItem, False)
        
        xbmcplugin.endOfDirectory(self.handle, True, True, False)
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)

    def showInfo(self, name):
        try:
            game = Game(name)
        except:
            return

        if not game.hasMetadata: return

        xbmcgui.Dialog().info(game.getListItem())

    def startGame(self, name):
        try:
            game = Game(name)
        except:
            return

        xbmc.Player().stop()
        game.start()

    def selectSource(self):
        result = xbmcgui.Dialog().browse(0, self.getLocalizedString(30001), 'files', defaultt = self.source)
        if result == self.source: return
        if not self.setSettingString('source', result): return
        
        #saving changes immediatly
        try:
            metadata = ElementTree.parse(xbmcvfs.translatePath(os.path.join(self.getAddonInfo('profile'), 'settings.xml')))
            root = metadata.getroot()
        except:
            root = ElementTree.Element('settings', {'version': '2'})

        success = False
        for element in root.iterfind('setting'):
            if element.get('id', '') == 'source':
                element.text = result
                success = True
                break
        if not success:
            ElementTree.SubElement(root, 'setting', {'id': 'source'}).text = result

        tree = ElementTree.ElementTree(root)
        try:
            tree.write(xbmcvfs.translatePath(os.path.join(self.getAddonInfo('profile'), 'settings.xml')), 'utf-8', False)
        except:
            return
        
        if xbmcgui.Dialog().yesno(self.getAddonInfo('name'), self.getLocalizedString(30905), defaultbutton = xbmcgui.DLG_YESNO_YES_BTN):
            #self.updateSource()
            xbmc.executebuiltin('RunPlugin(plugin://plugin.program.windowslauncher/?action=update_source)')

    def updateSource(self):
        games = self._getSourceLinksList()
        if len(games) > 0:
            progressDlg = xbmcgui.DialogProgressBG()
            progressDlg.create(self.getLocalizedString(30909), '')

            for i, game in enumerate(games):
                percent = int(i / len(games) * 100)
                progressDlg.update(percent, self.getLocalizedString(30909), game.name + '.lnk')
                
                searchResults = self._scraperSearch(game.title)

                resultIndex = -1
                for j, result in enumerate(searchResults):
                    if result.get('name', '').lower() == game.title.lower():
                        resultIndex = j
                        break
                if resultIndex < 0 and len(searchResults) > 0:
                    resultIndex = 0

                gameId = ''
                gameTitle = game.title
                if resultIndex >= 0:
                    gameTitle = searchResults[resultIndex]['name']
                    gameId = searchResults[resultIndex]['id']
                    #if self.selectedScraper == Game.SCRAPER_SOURCE_PLAYGROUND and searchResults[resultIndex].get('id') and searchResults[resultIndex].get('slug'):
                    #    game.playgroundId = {'id': searchResults[resultIndex]['id'], 'slug': searchResults[resultIndex]['slug']}

                percent = int((i + 1) / len(games) * 100)
                progressDlg.update(percent, self.getLocalizedString(30909), gameTitle)

                if gameId != '':
                    if game.scrapeMetadata(self.selectedScraper, gameId):
                        game.saveMetadata()

                xbmc.sleep(500)

            progressDlg.close()

    def listFiles(self):
        if self.source == '':
            xbmcgui.Dialog().ok(self.getAddonInfo('name'), self.getLocalizedString(30901))
            return

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.setPluginCategory(self.handle, self.getAddonInfo('name'))

        games = self._getSourceLinksList()
        for game in games:
            listItem = game.getListItem()
            listItem.setProperty('IsPlayable', 'False')
            if not game.hasMetadata:
                listItem.setLabel(game.name + '.lnk')
                menuItemUpdateInfo = (self.getLocalizedString(30903), 'RunPlugin({}?action=update_info&game={})'.format(self.url, game.name))
                listItem.addContextMenuItems([menuItemUpdateInfo])
            else:
                menuItemShowInfo = (self.getLocalizedString(30902), 'RunPlugin({}?action=show_info&game={})'.format(self.url, game.name))
                menuItemUpdateInfo = (self.getLocalizedString(30903), 'RunPlugin({}?action=update_info&game={})'.format(self.url, game.name))
                menuItemRemoveLink = (self.getLocalizedString(30904), 'RunPlugin({}?action=remove&game={})'.format(self.url, game.name))
                listItem.addContextMenuItems([menuItemShowInfo, menuItemUpdateInfo, menuItemRemoveLink])

            xbmcplugin.addDirectoryItem(self.handle, '{}?action=open&game={}'.format(self.url, game.name), listItem, False)
        
        xbmcplugin.endOfDirectory(self.handle, True, True, False)

    def clearSource(self):
        games = self._getSourceLinksList()

        if len(games) > 0:
            if not xbmcgui.Dialog().yesno(self.getAddonInfo('name'), self.getLocalizedString(30907)): return

            progressDlg = xbmcgui.DialogProgressBG()
            progressDlg.create(self.getLocalizedString(30906), '')

            for i, game in enumerate(games):
                gameName = game.title
                game.removeMetadata()

                percent = int((i + 1) / len(games) * 100)
                progressDlg.update(percent, self.getLocalizedString(30906), gameName)

            progressDlg.close()

        xbmcgui.Dialog().ok(self.getAddonInfo('name'), self.getLocalizedString(30908))

    def updateInfo(self, name):
        try:
            game = Game(name)
        except:
            return

        searchName = game.name
        selectedIndex = -1
        
        searchResults = self._scraperSearch(searchName)
        while True:
            if len(searchResults) == 0:
                searchName = xbmcgui.Dialog().input(self.getLocalizedString(30911), searchName, xbmcgui.INPUT_ALPHANUM)
                if searchName == '':
                    break
                else:
                    searchResults = self._scraperSearch(searchName)
            else:
                items = []
                for result in searchResults:
                    listItem = xbmcgui.ListItem(result['name'])
                    listItem.setArt({'thumb' : result['image']})
                    items.append(listItem)
                selectedIndex = xbmcgui.Dialog().select(self.getLocalizedString(30910), items, useDetails = True)
                if selectedIndex < 0:
                    searchResults = []
                else:
                    break

        if len(searchResults) == 0 or selectedIndex < 0: return

        #success = False
        #if self.selectedScraper == Game.SCRAPER_SOURCE_PLAYGROUND and searchResults[selectedIndex].get('id') and searchResults[selectedIndex].get('slug'):
        #    game.playgroundId = {'id': searchResults[selectedIndex]['id'], 'slug': searchResults[selectedIndex]['slug']}
        #    success = game.scrapeMetadata(self.selectedScraper)
        #else:
        #    return

        #if success:
        if game.scrapeMetadata(self.selectedScraper, searchResults[selectedIndex]['id']):
            if game.saveMetadata():
                xbmc.executebuiltin('Container.Refresh()', False)

    def removeGame(self, name):
        try:
            game = Game(name)
        except:
            return

        if game.removeMetadata():
            xbmc.executebuiltin('Container.Refresh()', False)

    def showFiles(self):
        xbmc.executebuiltin('Dialog.Close(all, true)', True)
        xbmc.executebuiltin('ActivateWindow(10001, plugin://plugin.program.windowslauncher/?action=list_files, return)', False)

    def main(self):
        if not self.params:
            self.listItems()
            return

        action = self.params.get('action', '').lower()
        gameName = self.params.get('game', '').lower()
        
        if action == 'select_source':
            self.selectSource()
        elif action == 'update_source':
            self.updateSource()
        elif action == 'list_files':
            self.listFiles()
        elif action == 'clear_source':
            self.clearSource()
        elif action == 'show_info':
            self.showInfo(gameName)
        elif action == 'start':
            self.startGame(gameName)
        elif action == 'update_info':
            self.updateInfo(gameName)
        elif action == 'remove':
            self.removeGame(gameName)
        elif action == 'show_files':
            self.showFiles()
        else:
            self.listItems()

addon = Addon()

if __name__ == '__main__':
    addon.main()
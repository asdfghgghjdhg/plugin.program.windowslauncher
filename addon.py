import sys
import os
import re
import ctypes

import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin

import lib.utils
import lib.scrapers

from urllib.parse import parse_qsl
from lib.games import GamesLibrary

#import web_pdb; web_pdb.set_trace()

LOG_TAG = 'plugin.program.windowslauncher'

class Addon(xbmcaddon.Addon):
    def __init__(self):
        self._url = sys.argv[0]
        self._handle = int(sys.argv[1])

        self._params = dict(parse_qsl(sys.argv[2][1:]))
        if not self._params: self._params = {'action': 'list_games'}
        if not self._params.get('action'): self._params['action'] = 'list_games'

        self._library = GamesLibrary()

        return super().__init__(id = None)

    @property
    def name(self):
        return self.getAddonInfo('name')

    def listGames(self):
        if self._library.source == '':
            lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'library source not set')
            xbmcgui.Dialog().ok(self.name, self.getLocalizedString(30901))
            xbmcgui.Window().close()
            self.openSettings()
            return

        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'creating game list')

        xbmcplugin.setContent(self._handle, self.getSettings().getString('content_type').lower())
        xbmcplugin.setPluginCategory(self._handle, self.name)

        games = self._library.games
        for game in games:
            listItem = game.getListItem()
            xbmcplugin.addDirectoryItem(self._handle, 'plugin://plugin.program.windowslauncher?action=start&game={}'.format(game.name), listItem, False)
        
        xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
        xbmcplugin.endOfDirectory(self._handle, True, True, False)

        del games
        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'game list created')

    def changeSource(self):
        newSource = xbmcgui.Dialog().browse(0, self.getLocalizedString(30001), 'files', defaultt = self._library.source)
        if newSource == self._library.source: return
        
        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'changing library source to "{}"', newSource)
        self._library.source = newSource

        if self._library.source == newSource:
            lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'library source changed to "{}"', newSource)
            if xbmcgui.Dialog().yesno(self.name, self.getLocalizedString(30905), defaultbutton = xbmcgui.DLG_YESNO_YES_BTN):
                self.updateGames()
                #xbmc.executebuiltin('RunPlugin(plugin://plugin.program.windowslauncher/?action=update_source)')

        self.openSettings()

    def updateGames(self):
        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'updating games metadata')

        scraperType = self.getSettings().getInt('scraper')
        if scraperType == lib.scrapers.SCRAPER_SOURCE_PLAYGROUND:
            scraper = lib.scrapers.PGScraper()
        elif scraperType == lib.scrapers.SCRAPER_SOURCE_IGDB:
            scraper = lib.scrapers.IGDBScraper(self.getSettingString('twitch_client_id'), self.getSettingString('twitch_client_secret'))
        elif scraperType == lib.scrapers.SCRAPER_SOURCE_RAWG:
            scraper = lib.scrapers.RAWGScraper()
        elif scraperType == lib.scrapers.SCRAPER_SOURCE_MOBYGAMES:
            scraper = lib.scrapers.MGScraper()
        else:
            scraper = lib.scrapers.GameScraper()

        games = self._library.shortcuts
        if len(games) > 0:
            progressDlg = xbmcgui.DialogProgressBG()
            progressDlg.create(self.getLocalizedString(30909), '')

            for i, game in enumerate(games):
                percent = int(i / len(games) * 100)
                progressDlg.update(percent, self.getLocalizedString(30909), os.path.basename(game.path))
                
                searchResults = scraper.search(game.title)
                if searchResults is None:
                    lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'cannot find game "{}" in {} database', game.title, scraper)
                    continue

                resultIndex = -1
                for j, result in enumerate(searchResults):
                    if re.findall('(\w+)', result['name'].lower()) == re.findall('(\w+)', game.title.lower()):
                        resultIndex = j
                        break
                if resultIndex < 0 and len(searchResults) > 0:
                    resultIndex = 0

                gameId = ''
                gameTitle = game.title
                if resultIndex >= 0:
                    gameTitle = searchResults[resultIndex]['name']
                    gameId = searchResults[resultIndex]['id']

                percent = int((i + 1) / len(games) * 100)
                progressDlg.update(percent, self.getLocalizedString(30909), gameTitle)

                if gameId != '':
                    metadata = scraper.getInfo(gameId)
                    if metadata is None:
                        lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'cannot get metadata for game "{}" in {} database', game.title, scraper)
                    else:
                        game.saveMetadata(metadata)

                xbmc.sleep(500)

            progressDlg.close()
            del progressDlg

        del games
        del scraper
        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'updating games metadata finished')
        xbmc.executebuiltin('Container.Refresh()', False)

    def showShortcuts(self):
        xbmc.executebuiltin('Dialog.Close(all, true)', True)
        xbmc.executebuiltin('ActivateWindow(10001, plugin://plugin.program.windowslauncher/?action=list_files, return)', False)

    def listShortcuts(self):
        if self._library.source == '':
            lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'library source not set')
            xbmcgui.Dialog().ok(self.name, self.getLocalizedString(30901))
            xbmcgui.Window().close()
            self.openSettings()
            return

        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'creating shortcuts list')

        xbmcplugin.setContent(self._handle, 'files')
        xbmcplugin.setPluginCategory(self._handle, self.getLocalizedString(30920))

        shortcuts = self._library.shortcuts
        for shortcut in shortcuts:
            listItem = shortcut.getListItem()
            listItem.setProperty('IsPlayable', 'False')
            xbmcplugin.addDirectoryItem(self._handle, 'plugin://plugin.program.windowslauncher?action=start&game={}'.format(shortcut.name), listItem, False)
        
        xbmcplugin.endOfDirectory(self._handle, True, True, False)

        del shortcuts
        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'shortcuts list created')

    def clearSource(self):
        if not xbmcgui.Dialog().yesno(self.name, self.getLocalizedString(30907)): return

        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'clearing library')

        self._library.clear()

        xbmcgui.Dialog().notification(self.name, self.getLocalizedString(30908), xbmcgui.NOTIFICATION_INFO)
        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'library cleared')
        xbmc.executebuiltin('Container.Refresh()', False)

    def startGame(self):
        name = self._params.get('game')
        if not name:
            lib.utils.log(LOG_TAG, xbmc.LOGERROR, 'bad params {}', self._params)
            return

        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'starting game "{}"', name)

        try:
            game = self._library.getGame(name)
            if game is None: raise ValueError('bad game name')
        except Exception as e:
            xbmcgui.Dialog().ok(self.name, self.getLocalizedString(30918).format(name))
            return

        xbmc.Player().stop()
        xbmc.audioSuspend()
        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'xbmc audio disabled')

        blankItem = xbmcgui.ListItem(path = os.path.join(self.getAddonInfo('path'), 'resources', 'media', 'blank.png'))
        
        success = False
        seInfo = lib.utils.ShellExecuteInfo(fMask = lib.utils.SEE_MASK_NOCLOSEPROCESS + lib.utils.SEE_MASK_WAITFORINPUTIDLE + lib.utils.SEE_MASK_FLAG_NO_UI, lpFile = game.path.encode('utf-8'), nShow = lib.utils.SW_SHOWNORMAL)
        if lib.utils.shellExecuteEx(ctypes.byref(seInfo)) and seInfo.hInstApp > 32:
            lib.utils.log(LOG_TAG, xbmc.LOGINFO, '{} started successfuly'.format(game.name))
            success = True
        else:
            lib.utils.log(LOG_TAG, xbmc.LOGERROR, 'cannot start {} - error code {}'.format(game.name, seInfo.hInstApp))
            xbmcgui.Dialog().ok(self.name, self.getLocalizedString(30918).format(game.title))

        dlgRunning = None
        if success:
            if self.getSettings().getBool('show_running_window'):
                dlgRunning = xbmcgui.DialogProgress()
                dlgRunning.create(self.name, self.getLocalizedString(30917).format(game.title))
                dlgRunning.update(100, self.getLocalizedString(30917).format(game.title))

            while seInfo.hProcess:
                xbmc.sleep(1000)
                exitCode = ctypes.wintypes.DWORD()
                if not lib.utils.getExitCodeProcess(seInfo.hProcess, ctypes.byref(exitCode)):
                    lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'cannot wait to finish {}'.format(game.name))
                    break
                if exitCode.value != lib.utils.STILL_ACTIVE:
                    lib.utils.log(LOG_TAG, xbmc.LOGINFO, '{} finished with code {}'.format(game.name, exitCode.value))
                    break

            lib.utils.closeHandle(seInfo.hProcess)
        
        if not dlgRunning is None:
            while not dlgRunning.iscanceled(): xbmc.sleep(100)
            dlgRunning.close()
            del dlgRunning

        xbmcplugin.setResolvedUrl(self._handle, success, blankItem)

        xbmc.audioResume()
        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'xbmc audio enabled')

        del game
    
    def showInfo(self):
        name = self._params.get('game')
        if not name:
            lib.utils.log(LOG_TAG, xbmc.LOGERROR, 'bad params {}', self._params)
            return

        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'showing game info for game "{}"', name)

        try:
            game = self._library.getGame(name)
            if game is None: raise ValueError('bad game name')
        except Exception as e:
            return

        xbmcgui.Dialog().info(game.getListItem())
        del game

    def updateInfo(self):
        name = self._params.get('game')
        if not name:
            lib.utils.log(LOG_TAG, xbmc.LOGERROR, 'bad params {}', self._params)
            return

        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'updating metadata for game "{}"', name)

        try:
            game = self._library.getGame(name)
            if game is None: raise ValueError('bad game name')
        except Exception as e:
            return

        scraperType = self.getSettings().getInt('scraper')
        if scraperType == lib.scrapers.SCRAPER_SOURCE_PLAYGROUND:
            scraper = lib.scrapers.PGScraper()
        elif scraperType == lib.scrapers.SCRAPER_SOURCE_IGDB:
            scraper = lib.scrapers.IGDBScraper(self.getSettingString('twitch_client_id'), self.getSettingString('twitch_client_secret'))
        elif scraperType == lib.scrapers.SCRAPER_SOURCE_RAWG:
            scraper = lib.scrapers.RAWGScraper()
        elif scraperType == lib.scrapers.SCRAPER_SOURCE_MOBYGAMES:
            scraper = lib.scrapers.MGScraper()
        else:
            scraper = lib.scrapers.GameScraper()

        searchName = game._title
        selectedIndex = -1
        
        progressDlg = xbmcgui.DialogProgress()
        progressDlg.create(self.name, self.getLocalizedString(30915).format(searchName))
        searchResults = scraper.search(searchName)
        if progressDlg.iscanceled(): return
        progressDlg.close()

        if searchResults is None:
            xbmcgui.Dialog().notification(self.name, self.getLocalizedString(30913).format(self.scraper))
            lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'cannot find game "{}" in {} database', searchName, scraper)
            return

        while True:
            if len(searchResults) == 0:
                searchName = xbmcgui.Dialog().input(self.getLocalizedString(30911), searchName, xbmcgui.INPUT_ALPHANUM)
                if searchName == '':
                    break
                else:
                    progressDlg.create(self.getAddonInfo('name'), self.getLocalizedString(30915).format(searchName))
                    searchResults = scraper.search(searchName)
                    if progressDlg.iscanceled():
                        searchResults = None
                        break
                    progressDlg.close()

                    if searchResults is None:
                        xbmcgui.Dialog().notification(self.name, self.getLocalizedString(30913).format(self.scraper))
                        lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'cannot find game "{}" in {} database', searchName, scraper)
                        break
            else:
                for i, result in enumerate(searchResults):
                    if re.findall('(\w+)', result['name'].lower()) == re.findall('(\w+)', game.name.lower()):
                        searchResults.insert(0, searchResults.pop(i))

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

        if not searchResults or selectedIndex < 0: return

        progressDlg.create(self.name, self.getLocalizedString(30916).format(searchResults[selectedIndex]['name']))
        metadata = scraper.getInfo(searchResults[selectedIndex]['id'])
        if progressDlg.iscanceled(): return
        progressDlg.close()

        if metadata is None:
            xbmcgui.Dialog().notification(self.name, self.getLocalizedString(30913).format(self.scraper))
            lib.utils.log(LOG_TAG, xbmc.LOGWARNING, 'cannot get metadata for game "{}" in {} database', game.title, scraper)
            return

        if not game.saveMetadata(metadata):
            xbmcgui.Dialog().notification(self.getAddonInfo('name'), self.getLocalizedString(30914))
        else:
            lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'metadata for game "{}" updated', name)

        del progressDlg
        del scraper
        del game
        xbmc.executebuiltin('Container.Refresh()', False)

    def removeGame(self):
        name = self._params.get('game')
        if not name:
            lib.utils.log(LOG_TAG, xbmc.LOGERROR, 'bad params {}', self._params)
            return

        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'clearing metadata for game "{}"', name)

        try:
            game = self._library.getGame(name)
            if game is None: raise ValueError('bad game name')
        except Exception as e:
            return

        if game.removeMetadata():
            xbmc.executebuiltin('Container.Refresh()', False)
        else:
            xbmcgui.Dialog().notification(self.getAddonInfo('name'), self.getLocalizedString(30919).format(game.name), xbmcgui.NOTIFICATION_ERROR)

        del game

    def main(self):
        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'entering main thread with params {}', self._params)

        action = self._params['action'].lower()
        
        if action == 'list_games':
            self.listGames()
        if action == 'select_source':
            self.changeSource()
        elif action == 'update_source':
            self.updateGames()
        elif action == 'list_files':
            self.listShortcuts()
        elif action == 'clear_source':
            self.clearSource()
        elif action == 'show_info':
            self.showInfo()
        elif action == 'start':
            self.startGame()
        elif action == 'update_info':
            self.updateInfo()
        elif action == 'remove':
            self.removeGame()
        elif action == 'show_files':
            self.showShortcuts()
        else:
            return

        lib.utils.log(LOG_TAG, xbmc.LOGDEBUG, 'exiting main thread')

addon = Addon()
if __name__ == '__main__':
    addon.main()

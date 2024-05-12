import time
import json
import requests
import xbmc
import xbmcgui

from datetime import datetime, timedelta
from urllib import parse
from lib.utils import log
from lib.scrapers.scraper import GameScraper

LOG_TAG                         = 'igdb.com'

class IGDBScraper(GameScraper):
    def __init__(self, clientId: str, clientSecret: str):
        self._clientId = clientId.strip()
        self._clientSecret = clientSecret.strip()

        self._authData = None

        return super().__init__()

    def __str__(self):
        return 'igdb.com'

    def _updateAuthData(self):
        self._authData = None

        if self._clientId == '' or self._clientSecret == '':
            log(LOG_TAG, xbmc.LOGWARNING, 'twitch client id and client secret not set, returning')
            return

        authData = xbmcgui.Window(10000).getProperty('TwitchAuthData')
        if authData:
            authData = json.loads(authData)
            log(LOG_TAG, xbmc.LOGINFO, 'found cached twitch auth token expires {}'.format(datetime.fromtimestamp(authData['expires'])))

        if not authData or authData['expires'] < time.time() + 60:
            log(LOG_TAG, xbmc.LOGINFO, 'getting new twitch auth token')
            query = 'https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials'.format(self._clientId, self._clientSecret)
            try:
                response = requests.post(query)
                if response.ok:
                    authData = json.loads(response.text)
                else:
                    log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {}', query)
                    return
            except Exception as e:
                log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {} - {}', query, e)
                return

            if not authData.get('access_token') or not authData.get('token_type') or not authData.get('expires_in'):
                log(LOG_TAG, xbmc.LOGERROR, 'wrong response from {}', query)
                return

            authData['expires'] = time.time() + authData['expires_in']

            log(LOG_TAG, xbmc.LOGINFO, 'received new twitch auth token expires {}'.format(datetime.fromtimestamp(authData['expires'])))

            xbmcgui.Window(10000).setProperty('TwitchAuthData', json.dumps(authData))
        
        self._authData = authData

    def _query(self, endpoint: str, body: str):
        url = 'https://api.igdb.com/v4/{}'.format(endpoint)
        headers = {'Content-Type': 'text/plain', 'Client-ID': self._clientId, 'Authorization': '{} {}'.format(self._authData['token_type'], self._authData['access_token'])}
        result = None
        try:
            response = requests.post(url, body.encode('utf-8'), headers = headers)
            if response.ok:
                result = json.loads(response.text)
            else:
                log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {}', url)
        except Exception as e:
            log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {} - {}', url, e)

        return result

    @property
    def clientId(self):
        return self._clientId

    @property
    def clientSecret(self):
        return self._clientSecret

    def search(self, name: str):
        results = None
        log(LOG_TAG, xbmc.LOGDEBUG, 'starting search for name "{}"', name)

        self._updateAuthData()
        if not self._authData:
            log(LOG_TAG, xbmc.LOGDEBUG, 'failed to update access token with client_id = {} and client_secret = {}', self._clientId, self._clientSecret)
            return results

        body = 'search "{}"; fields name, cover.image_id, platforms; where version_parent = null & platforms = (6); limit 50;'.format(name)
        data = self._query('games', body)
        
        if not isinstance(data, list):
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from /games')
            return results

        results = []
        for element in data:
            id = ''
            name = ''
            image = ''

            if isinstance(element, dict):
                id = str(element.get('id', '')).strip()
                name = element.get('name', '').strip()
            
            if element.get('cover') and element['cover'].get('image_id'):
                image = 'https://images.igdb.com/igdb/image/upload/t_720p/{}.jpg'.format(element['cover']['image_id'])

            if id != '' and name != '':
                results.append({'id': id, 'name': name, 'image': image})

        return results

    def getInfo(self, id: str):
        info = {'id': id, 'title': None, 'altTitle': None, 'platform': None, 'year': None, 'developer': None, 'publisher': None, 'genres': None, 'overview': None, 'rating': None, 'thumbs': None, 'fanarts': None}
        log(LOG_TAG, xbmc.LOGDEBUG, 'scraping metadata for game "{}"', id)

        self._updateAuthData()
        if not self._authData:
            log(LOG_TAG, xbmc.LOGDEBUG, 'failed to update access token with client_id = {} and client_secret = {}', self._clientId, self._clientSecret)
            return None

        body = 'fields id, name, cover.image_id, alternative_names.name, artworks.image_id, genres.name, involved_companies.company.name, involved_companies.developer, release_dates.platform, release_dates.date, screenshots.image_id, storyline, summary, total_rating, total_rating_count; where id = {} & platforms = (6);'.format(id)
        games = self._query('games', body)

        if not isinstance(games, list):
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from /games')
            return None

        data = games[0]

        info['id'] = data.get('id')
        info['title'] = data.get('name')
        if not info['id'] and not info['title']:
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from /games')
            return None

        if data.get('alternative_names') and data['alternative_names'][0].get('name'):
            info['altTitle'] = data['alternative_names'][0]['name']

        info['platform'] = 'PC'
        if data.get('release_dates'):
            for date in data['release_dates']:
                if date.get('platform', 0) == 6:
                    info['year'] = datetime.utcfromtimestamp(date['date']).year
                    break

        if data.get('involved_companies'):
            for company in data['involved_companies']:
                if company.get('developer', False):
                    info['developer'] = company.get('company', {}).get('name')
                else:
                    info['publisher'] = company.get('company', {}).get('name')

        info['overview'] = data.get('summary')

        if data.get('genres'):
            info['genres'] = []
            for genre in data['genres']:
                info['genres'].append(genre.get('name'))

        if data.get('total_rating'):
            info['rating'] = {'rating': data['total_rating'] / 10, 'type': 'igdb', 'votes': data.get('total_rating_count', 0)}

        if data.get('cover') and data['cover'].get('image_id'):
            info['thumbs'] = dict()
            info['thumbs']['thumb'] = 'https://images.igdb.com/igdb/image/upload/t_cover_big/{}.jpg'.format(data['cover']['image_id'])
            info['thumbs']['poster'] = 'https://images.igdb.com/igdb/image/upload/t_1080p/{}.jpg'.format(data['cover']['image_id'])

        if data.get('artworks'):
            if info['thumbs'] is None: info['thumbs'] = dict()
            info['thumbs']['fanart'] = 'https://images.igdb.com/igdb/image/upload/t_1080p/{}.jpg'.format(data['artworks'][0]['image_id'])

        if data.get('screenshots'):
            info['fanarts'] = []
            for screenshot in data['screenshots']:
                image = 'https://images.igdb.com/igdb/image/upload/t_screenshot_huge/{}.jpg'.format(screenshot['image_id'])
                preview = 'https://images.igdb.com/igdb/image/upload/t_screenshot_med/{}.jpg'.format(screenshot['image_id'])
                info['fanarts'].append({'image': image, 'preview': preview})

        return info

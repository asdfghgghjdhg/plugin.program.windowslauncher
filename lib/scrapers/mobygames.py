import re
import json
import html
import requests
import xbmc

from datetime import datetime, timedelta
from urllib import parse
from lib.utils import log
from lib.scrapers.scraper import GameScraper

LOG_TAG                         = 'mobygames.com'
API_KEY                         = 'moby_WJ7m8xxjspSAuMWgROjfN5TO0ed'

class MGScraper(GameScraper):
    def __init__(self):
        self._apiKey = API_KEY
        
        return super().__init__()

    def __str__(self):
        return 'mobygames.com'

    def _query(self, endpoint: str, params: dict):
        url = 'https://api.mobygames.com/v1/{}'.format(endpoint)
        params['api_key'] = self._apiKey
        result = None
        try:
            response = requests.get(url, params = params)
            if response.ok:
                result = json.loads(response.text)
            else:
                log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {}', url)
        except Exception as e:
            log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {} - {}', url, e)

        return result

    def search(self, name: str):
        results = None
        log(LOG_TAG, xbmc.LOGDEBUG, 'starting search for name "{}"', name)

        params = {'title': name, 'format': 'normal', 'platform': '3'}
        data = self._query('games', params)
        
        if not isinstance(data, dict) or not isinstance(data.get('games'), list):
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from /games')
            return results

        results = []
        for element in data['games']:
            id = ''
            name = ''
            image = ''

            if isinstance(element, dict):
                id = str(element.get('game_id', '')).strip()
                name = element.get('title', '').strip()
                if element.get('sample_cover'):
                    image = element['sample_cover'].get('image', '').strip()

            if id != '' and name != '':
                results.append({'id': id, 'name': name, 'image': image})

        return results

    def getInfo(self, id: str):
        info = {'id': id, 'title': None, 'altTitle': None, 'platform': None, 'year': None, 'developer': None, 'publisher': None, 'genres': None, 'overview': None, 'rating': None, 'thumbs': None, 'fanarts': None}
        log(LOG_TAG, xbmc.LOGDEBUG, 'scraping metadata for game "{}"', id)

        params = {'id': id, 'format': 'normal'}
        data = self._query('games', params)

        if not isinstance(data, dict) or not isinstance(data.get('games'), list) or not data['games']:
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from /games'.format(id))
            return None

        data = data['games'][0]

        info['id'] = data.get('id')
        info['title'] = data.get('title')
        if not info['id'] and not info['title']:
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from /games'.format(id))
            return None

        if data.get('alternate_titles'):
            info['altTitle'] = data['alternate_titles'][0]

        info['platform'] = 'PC'
        if data.get('platforms'):
            for platform in data['platforms']:
                if platform.get('platform_id') == 3:
                    releasedDate = platform.get('first_release_date', '').strip()
                    try:
                        info['year'] = datetime.strptime(releasedDate, '%y-%m-%d').year
                    except:
                        pass
                    break

        #if data.get('developers'):
        #    info['developer'] = data['developers'][0].get('name')
        #if data.get('publishers'):
        #    info['publishers'] = data['publishers'][0].get('name')

        if data.get('description'):
            desc = data.get('description', '').strip().replace('<br>', '\n').replace('<br/>', '\n')
            desc = html.unescape(re.sub('<.*?>', '', desc))
            if desc != '':
                info['overview'] = desc
        
        if data.get('genres'):
            info['genres'] = []
            for genre in data['genres']:
                info['genres'].append(genre.get('genre_name'))

        if data.get('moby_score'):
            info['rating'] = {'rating': data['moby_score'], 'type': 'moby', 'votes': data.get('num_votes', 0)}

        if data.get('sample_cover') and data['sample_cover'].get('image'):
            info['thumbs'] = dict()
            info['thumbs']['thumb'] = data['sample_cover']['image'].strip()
            info['thumbs']['poster'] = data['sample_cover']['image'].strip()

        if data.get('sample_screenshots'):
            info['fanarts'] = []
            for screenshot in data['sample_screenshots']:
                image = screenshot.get('image', '').strip()
                preview = ''
                info['fanarts'].append({'image': image, 'preview': preview})

        if info['fanarts']:
            if info['thumbs'] is None: info['thumbs'] = dict()
            info['thumbs']['fanart'] = info['fanarts'][0]['image']

        return info

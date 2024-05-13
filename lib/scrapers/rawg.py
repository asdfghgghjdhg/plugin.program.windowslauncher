import json
import requests
import xbmc

from datetime import datetime, timedelta
from urllib import parse
from lib.utils import log
from lib.scrapers.scraper import GameScraper

LOG_TAG                         = 'rawg.io'
API_KEY                         = 'da1483483c1c497e8e71d65f11094623'

class RAWGScraper(GameScraper):
    def __init__(self):
        self._apiKey = API_KEY
        
        return super().__init__()

    def __str__(self):
        return 'rawg.io'

    def _query(self, endpoint: str, params: dict):
        url = 'https://api.rawg.io/api/{}'.format(endpoint)
        params['key'] = self._apiKey
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

        params = {'search': parse.quote_plus(name), 'search_exact': 'true', 'platforms': '4', 'page_size': 100}
        data = self._query('games', params)
        
        if not isinstance(data, dict) or not data.get('results') or not isinstance(data['results'], list):
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from /games')
            return results

        results = []
        for element in data['results']:
            id = ''
            name = ''
            image = ''

            if isinstance(element, dict):
                id = str(element.get('id', '')).strip()
                name = element.get('name', '').strip()
                image = element.get('background_image', '')

            if id != '' and name != '':
                results.append({'id': id, 'name': name, 'image': image})

        return results

    def getInfo(self, id: str):
        info = {'id': id, 'title': None, 'altTitle': None, 'platform': None, 'year': None, 'developer': None, 'publisher': None, 'genres': None, 'overview': None, 'rating': None, 'thumbs': None, 'fanarts': None}
        log(LOG_TAG, xbmc.LOGDEBUG, 'scraping metadata for game "{}"', id)

        data = self._query('games/{}'.format(id), {})

        if not isinstance(data, dict):
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from /games/{}'.format(id))
            return None

        info['id'] = data.get('id')
        info['title'] = data.get('name')
        if not info['id'] and not info['title']:
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from /games/{}'.format(id))
            return None

        if data.get('alternative_names'):
            info['altTitle'] = data['alternative_names'][0]

        info['platform'] = 'PC'
        if data.get('platforms'):
            for platform in data['platforms']:
                if platform.get('platform') and platform['platform'].get('id') and platform['platform']['id'] == 4:
                    releasedDate = platform.get('released_at', '').strip()
                    try:
                        info['year'] = datetime.strptime(releasedDate, '%y-%m-%d').year
                    except:
                        pass
                    break

        if data.get('developers'):
            info['developer'] = data['developers'][0].get('name')
        if data.get('publishers'):
            info['publishers'] = data['publishers'][0].get('name')

        info['overview'] = data.get('description_raw')

        if data.get('genres'):
            info['genres'] = []
            for genre in data['genres']:
                info['genres'].append(genre.get('name'))

        if data.get('rating'):
            info['rating'] = {'rating': data['rating'] * 2, 'type': 'rawg', 'votes': data.get('ratings_count', 0)}

        if data.get('background_image'):
            info['thumbs'] = dict()
            info['thumbs']['thumb'] = data['background_image'].strip()
            info['thumbs']['poster'] = data['background_image'].strip()
            info['thumbs']['fanart'] = data['background_image'].strip()

        if data.get('background_image_additional'):
            if info['thumbs'] is None: info['thumbs'] = dict()
            info['thumbs']['fanart'] = data['background_image_additional'].strip()

        if data.get('screenshots_count', 0) > 0:
            info['fanarts'] = []
            # todo: get screenshots

        return info

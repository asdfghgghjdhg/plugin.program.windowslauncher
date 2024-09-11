import re
import html
import json
import requests
import xbmc

from urllib import parse
from lib.utils import log
from .scraper import GameScraper

LOG_TAG                         = 'playground.ru'

class PGScraper(GameScraper):
    def __init__(self):
        return super().__init__()

    def __str__(self):
        return 'playground.ru'

    def search(self, name: str):
        results = None
        log(LOG_TAG, xbmc.LOGDEBUG, 'starting search for name "{}"', name)

        data = None
        query = 'https://www.playground.ru/api/game.search?query={}&include_addons=0'.format(parse.quote_plus(name))
        try:
            response = requests.get(query)
            if response.ok:
                data = json.loads(response.text)
            else:
                log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {}', query)
                return results
        except Exception as e:
            log(xbmc.LOGERROR, 'failed to get response from {} - {}', query, e)
            return results

        if not isinstance(data, list):
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from {}', query)
            return

        results = []
        for element in data:
            if isinstance(element, dict):
                id = element.get('slug', '').strip()
                name = element.get('name', '').strip()
                image = element.get('image', '').strip()
                if id != '' and name != '':
                    results.append({'id': id, 'name': name, 'image': image})

        log(LOG_TAG, xbmc.LOGINFO, 'found {} results for name "{}"', len(results), name)
        return results

    def getInfo(self, id: str):
        info = {'id': id, 'title': None, 'altTitle': None, 'platform': None, 'year': None, 'developer': None, 'publisher': None, 'genres': None, 'overview': None, 'rating': None, 'thumbs': None, 'fanarts': None}
        log(LOG_TAG, xbmc.LOGDEBUG, 'scraping metadata for game "{}"', id)
        
        query = 'https://www.playground.ru/api/game.get?game_slug={}'.format(id)
        try:
            response = requests.get(query)
            if response.ok:
                data = json.loads(response.text)
            else:
                log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {}', query)
                return results
        except Exception as e:
            log(xbmc.LOGERROR, 'failed to get response from {} - {}', query, e)
            return results

        if not isinstance(data, dict):
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from {}', query)
            return

        info['title'] = data.get('name', '').strip()
        if not info['title']:
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from {}', query)
            return None

        info['thumbs'] = dict()
        info['thumbs']['poster'] = data.get('image', '').strip()
        info['thumbs']['thumb'] = data.get('image', '').strip()

        info['genres'] = []
        tags = data.get('tags')
        if isinstance(tags, list):
            for element in tags:
                if element.get('name'):
                    info['genres'].append(element.get('name').strip())

        if data.get('releases') and data.get('releases').get('pc') and data.get('releases').get('pc').get('date'):
            info['year'] = int(data.get('releases').get('pc').get('date').strip()[1:4])
            info['platform'] = 'PC'

        if data.get('developer'):
            info['developer'] = data.get('developer').get('name', '').strip()
        if data.get('publisher'):
            info['publisher'] = data.get('publisher').get('name', '').strip()

        info['rating'] = dict()
        try:
            info['rating']['rating'] = float(data.get('rating').get('value'))
            info['rating']['type'] = 'PG'
            info['rating']['votes'] = int(data.get('rating').get('count'))
        except: pass
        if len(info['rating']) == 0:
            info['rating'] = None
        elif not info['rating'].get('votes'):
            info['rating']['votes'] = 0

        desc = data.get('text', '').strip().replace('<br>', '\n').replace('<br/>', '\n')
        info['overview'] = html.unescape(re.sub('<.*?>', '', desc))
        
        info['fanarts'] = []
        query = 'https://www.playground.ru/gallery/{}/'.format(id)
        try:
            response = requests.get(query)
            if not response.ok:
                log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {}', query)
            else:
                screenshotsBlock = re.search('<div class="module clearfix screenshots-module">(.+?)(?=<\/div><\/div><\/div>)', response.text)
                if screenshotsBlock:
                    screenshots = re.findall('<div class="gallery-item thumb"><a data-fancybox="gallery" href="(.+?)".+?<img src="(.+?)" alt="', screenshotsBlock.group(0))
                    if screenshots:
                        for screenshot in screenshots:
                            info['fanarts'].append({'image': screenshot[0], 'preview': screenshot[1]})

        except Exception as e:
            log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {} - {}', query, e)

        if len(info['fanarts']) > 0:
            info['thumbs']['fanart'] = info['fanarts'][0]['image']
        else:
            info['fanarts'] = None

        if len(info['thumbs']) == 0: info['thumbs'] = None

        log(LOG_TAG, xbmc.LOGDEBUG, 'metadata for game "{}" scraped', id)
        return info



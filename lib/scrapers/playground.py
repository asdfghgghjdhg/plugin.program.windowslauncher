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
        
        query = 'https://www.playground.ru/gallery/{}/'.format(id)
        try:
            response = requests.get(query)
            if not response.ok:
                log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {}', query)
                return None
        except Exception as e:
            log(LOG_TAG, xbmc.LOGERROR, 'failed to get response from {} - {}', query, e)
            return None
        
        gameInfo = re.search('<div class="modal-content" style="background-image: url\(.+\)">[\s\S]*?(?=<script>)', response.text)
        if not gameInfo:
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from {}', query)
            return None

        title = re.findall('<div class="game-title">\s+<a href=".+">\s+(.+)\s+(<span class="game-title-alt">(.+)</span>)?\s+</a>', gameInfo.group(0))
        if title:
            info['title'] = title[0][0].strip()
            info['altTitle'] = title[0][2].strip()
        else:
            log(LOG_TAG, xbmc.LOGERROR, 'wrong response from {}', query)
            return None

        info['thumbs'] = dict()
        poster = re.findall('<div class="modal-content" style="background-image: url\((.+)\)">', gameInfo.group(0))
        if poster:
            info['thumbs']['poster'] = poster[0].strip()
        thumb = re.findall('<div class="game-poster">[\s\S]+<img.+src="(.+?)"', gameInfo.group(0))
        if thumb:
            info['thumbs']['thumb'] = thumb[0].strip()

        info['genres'] = []
        genres = re.findall('<a class="item" href="\/games\/.+?">(.+?)<\/a>', gameInfo.group(0))
        if genres:
            for genre in genres:
                info['genres'].append(genre.strip())
        if len(info['genres']) == 0: info['genres'] = None

        dates = re.findall('<div class="release-item">\s+?<span class="date">([\s\S]+?)<\/span>\s+<a class="platform-item (.+)" href="\/games\/.+">', gameInfo.group(0))
        if dates:
            for platform in dates:
                if platform[1].strip() == 'pc':
                    try:
                        info['year'] = int(platform[0].strip()[-4:])
                        info['platform'] = 'PC'
                    except:
                        pass

        developer = re.findall('<a title="все игры этого разработчика"\s+href="\/games\?company=.+">\s+<span>(.+?)<\/span>', gameInfo.group(0))
        if developer:
            info['developer'] = developer[0].strip()

        publisher = re.findall('<a title="все игры этого издателя"\s+href="\/games\?company=.+">\s+<span>(.+?)<\/span>', gameInfo.group(0))
        if publisher:
            info['publisher'] = publisher[0].strip()

        info['rating'] = dict()
        rating = re.findall('<span class="value">\s*(.+?)\s*<\/span>\s+Пользователи\s*<span>\s*(.+?)\s*<\/span>', gameInfo.group(0))
        if rating:
            try:
                info['rating']['rating'] = float(rating[0][0].strip()[0:-3])
                info['rating']['type'] = 'PG'
                info['rating']['votes'] = int(rating[0][1].strip().replace(' ', ''))
            except: pass
        if len(info['rating']) == 0:
            info['rating'] = None
        elif not info['rating'].get('votes'):
            info['rating']['votes'] = 0

        plot = re.findall('<div class="description-wrapper">([\s\S]+?)<\/div>', gameInfo.group(0))
        if plot:
            plot = re.sub('<.*?>', '', plot[0].strip().replace('<br>', '\n').replace('<br/>', '\n'))
            info['overview'] = html.unescape(plot)

        info['fanarts'] = []
        screenshotsBlock = re.search('<div class="module clearfix screenshots-module">(.+?)(?=<\/div><\/div><\/div>)', response.text)
        if screenshotsBlock:
            screenshots = re.findall('<div class="gallery-item thumb"><a data-fancybox="gallery" href="(.+?)".+?<img src="(.+?)" alt="', screenshotsBlock.group(0))
            if screenshots:
                for screenshot in screenshots:
                    info['fanarts'].append({'image': screenshot[0], 'preview': screenshot[1]})

        if len(info['fanarts']) > 0:
            info['thumbs']['fanart'] = info['fanarts'][0]['image']
        else:
            info['fanarts'] = None

        if len(info['thumbs']) == 0: info['thumbs'] = None

        log(LOG_TAG, xbmc.LOGDEBUG, 'metadata for game "{}" scraped', id)
        return info



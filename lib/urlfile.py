import os
import re

class UrlFile:
    def __init__(self, urlFile: str):
        self._urlPath = os.path.abspath(urlFile)
        self._data = dict()

        file = open(urlFile, mode = 'r')

        try:
            for n, line in enumerate(file, 1):
                line = line.rstrip('\n')

                if line.lower() == '[internetshortcut]':
                    break

            while line:
                line = file.readline()
                if line:
                    lineData = re.findall('(\S+)\s*=\s*(.*)', line)
                    if lineData:
                        self._data[lineData[0][0].lower()] = lineData[0][1]

        except:
            raise ValueError('Not valid Url File')
        finally:
            file.close()

        if len(self._data) == 0:
            raise ValueError('Not valid Url File')

        if not self._data.get('url'):
            raise ValueError('Not valid Url File')

        if self._data['url'].strip() == '':
            raise ValueError('Not valid Url File')

        return super().__init__()

    @property
    def path(self):
        return self._urlPath

    @property
    def file(self):
        return os.path.basename(self._urlPath)

    @property
    def urlData(self):
        return self._data



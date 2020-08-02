import sys
import time
import os
import re
import random
import copy
import json
import codecs
import pprint

#----------------------------------------------------------------------
# 语言的别名
#----------------------------------------------------------------------
langmap = {
    "arabic": "ar",
    "bulgarian": "bg",
    "catalan": "ca",
    "chinese": "zh-CN",
    "chinese simplified": "zh-CHS",
    "chinese traditional": "zh-CHT",
    "czech": "cs",
    "danish": "da",
    "dutch": "nl",
    "english": "en",
    "estonian": "et",
    "finnish": "fi",
    "french": "fr",
    "german": "de",
    "greek": "el",
    "haitian creole": "ht",
    "hebrew": "he",
    "hindi": "hi",
    "hmong daw": "mww",
    "hungarian": "hu",
    "indonesian": "id",
    "italian": "it",
    "japanese": "ja",
    "klingon": "tlh",
    "klingon (piqad)":"tlh-Qaak",
    "korean": "ko",
    "latvian": "lv",
    "lithuanian": "lt",
    "malay": "ms",
    "maltese": "mt",
    "norwegian": "no",
    "persian": "fa",
    "polish": "pl",
    "portuguese": "pt",
    "romanian": "ro",
    "russian": "ru",
    "slovak": "sk",
    "slovenian": "sl",
    "spanish": "es",
    "swedish": "sv",
    "thai": "th",
    "turkish": "tr",
    "ukrainian": "uk",
    "urdu": "ur",
    "vietnamese": "vi",
    "welsh": "cy"
}

# ----------------------------------------------------------------------
# BasicTranslator
# ----------------------------------------------------------------------
class BasicTranslator(object):

    def __init__(self, name, **argv):
        self._name = name
        self._config = {}
        self._options = argv
        self._session = None
        self._agent = None
        self._load_config(name)
        self._check_proxy()

    def __load_ini(self, ininame, codec=None):
        config = {}
        if not ininame:
            return None
        elif not os.path.exists(ininame):
            return None
        try:
            content = open(ininame, 'rb').read()
        except IOError:
            content = b''
        if content[:3] == b'\xef\xbb\xbf':
            text = content[3:].decode('utf-8')
        elif codec is not None:
            text = content.decode(codec, 'ignore')
        else:
            codec = sys.getdefaultencoding()
            text = None
            for name in [codec, 'gbk', 'utf-8']:
                try:
                    text = content.decode(name)
                    break
                except:
                    pass
            if text is None:
                text = content.decode('utf-8', 'ignore')
        if sys.version_info[0] < 3:
            import StringIO
            import ConfigParser
            sio = StringIO.StringIO(text)
            cp = ConfigParser.ConfigParser()
            cp.readfp(sio)
        else:
            import configparser
            cp = configparser.ConfigParser(interpolation=None)
            cp.read_string(text)
        for sect in cp.sections():
            for key, val in cp.items(sect):
                lowsect, lowkey = sect.lower(), key.lower()
                config.setdefault(lowsect, {})[lowkey] = val
        if 'default' not in config:
            config['default'] = {}
        return config

    def _load_config(self, name):
        self._config = {}
        ininame = os.path.expanduser('~/.config/translator/config.ini')
        # ininame = os.path.expanduser('config.ini')
        config = self.__load_ini(ininame)
        if not config:
            return False
        for section in ('default', name):
            items = config.get(section, {})
            for key in items:
                self._config[key] = items[key]
        return True

    def _check_proxy(self):
        proxy = os.environ.get('all_proxy', None)
        if not proxy:
            return False
        if not isinstance(proxy, str):
            return False
        if 'proxy' not in self._config:
            self._config['proxy'] = proxy.strip()
        return True

    def request(self, url, data=None, post=False, header=None):
        import requests
        if not self._session:
            self._session = requests.Session()
        argv = {}
        if header is not None:
            header = copy.deepcopy(header)
        else:
            header = {}
        if self._agent:
            header['User-Agent'] = self._agent
        argv['headers'] = header
        timeout = self._config.get('timeout', 7)
        proxy = self._config.get('proxy', None)
        if timeout:
            argv['timeout'] = float(timeout)
        if proxy:
            proxies = {'http': proxy, 'https': proxy}
            argv['proxies'] = proxies
        if not post:
            if data is not None:
                argv['params'] = data
        else:
            if data is not None:
                argv['data'] = data
        if not post:
            r = self._session.get(url, **argv)
        else:
            r = self._session.post(url, **argv)
        return r

    def http_get(self, url, data=None, header=None):
        return self.request(url, data, False, header)

    def http_post(self, url, data=None, header=None):
        return self.request(url, data, True, header)

    def url_unquote(self, text, plus=True):
        if sys.version_info[0] < 3:
            import urllib
            if plus:
                return urllib.unquote_plus(text)
            return urllib.unquote(text)
        import urllib.parse
        if plus:
            return urllib.parse.unquote_plus(text)
        return urllib.parse.unquote(text)

    def url_quote(self, text, plus=True):
        if sys.version_info[0] < 3:
            import urllib
            if isinstance(text, unicode):  # noqa: F821
                text = text.encode('utf-8', 'ignore')
            if plus:
                return urllib.quote_plus(text)
            return urlparse.quote(text)  # noqa: F821
        import urllib.parse
        if plus:
            return urllib.parse.quote_plus(text)
        return urllib.parse.quote(text)

    def create_translation(self, sl=None, tl=None, text=None):
        res = {}
        res['engine'] = self._name
        res['sl'] = sl  # 来源语言
        res['tl'] = tl  # 目标语言
        res['text'] = text  # 需要翻译的文本
        res['phonetic'] = None  # 音标
        res['definition'] = None  # 简单释义
        res['explain'] = None  # 分行解释
        return res

    # 翻译结果：需要填充如下字段
    def translate(self, sl, tl, text):
        return self.create_translation(sl, tl, text)

    # 是否是英文
    def check_english(self, text):
        for ch in text:
            if ord(ch) >= 128:
                return False
        return True

    # 猜测语言
    def guess_language(self, sl, tl, text):
        if ((not sl) or sl == 'auto') and ((not tl) or tl == 'auto'):
            if self.check_english(text):
                sl, tl = ('en-US', 'zh-CN')
            else:
                sl, tl = ('zh-CN', 'en-US')
        if sl.lower() in langmap:
            sl = langmap[sl.lower()]
        if tl.lower() in langmap:
            tl = langmap[tl.lower()]
        return sl, tl

    def md5sum(self, text):
        import hashlib
        m = hashlib.md5()
        if sys.version_info[0] < 3:
            if isinstance(text, unicode):  # noqa: F821
                text = text.encode('utf-8')
        else:
            if isinstance(text, str):
                text = text.encode('utf-8')
        m.update(text)
        return m.hexdigest()


#----------------------------------------------------------------------
# Baidu Translator
#----------------------------------------------------------------------
class BaiduTranslator (BasicTranslator):

    def __init__ (self, **argv):
        super(BaiduTranslator, self).__init__('baidu', **argv)
        if 'apikey' not in self._config:
            sys.stderr.write('error: missing apikey in [baidu] section\n')
            sys.exit()
        if 'secret' not in self._config:
            sys.stderr.write('error: missing secret in [baidu] section\n')
            sys.exit()
        self.apikey = self._config['apikey']
        self.secret = self._config['secret']
        langmap = {
            'zh-cn': 'zh',
            'zh-chs': 'zh',
            'zh-cht': 'cht',
            'en-us': 'en',
            'en-gb': 'en',
            'ja': 'jp',
        }
        self.langmap = langmap

    def convert_lang (self, lang):
        t = lang.lower()
        if t in self.langmap:
            return self.langmap[t]
        return lang

    def translate (self, sl, tl, text):
        sl, tl = self.guess_language(sl, tl, text)
        req = {}
        req['q'] = text
        req['from'] = self.convert_lang(sl)
        req['to'] = self.convert_lang(tl)
        req['appid'] = self.apikey
        req['salt'] = str(int(time.time() * 1000) + random.randint(0, 10))
        req['sign'] = self.sign(text, req['salt'])
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        r = self.http_post(url, req)
        resp = r.json()
        res = {}
        res['text'] = text
        res['sl'] = sl
        res['tl'] = tl
        res['info'] = resp
        res['translation'] = self.render(resp)
        res['html'] = None
        res['xterm'] = None
        return res

    def sign (self, text, salt):
        t = self.apikey + text + salt + self.secret
        return self.md5sum(t)

    def render (self, resp):
        output = ''
        result = resp['trans_result']
        for item in result:
            output += '' + item['src'] + '\n'
            output += ' * ' + item['dst'] + '\n'
        return output


#----------------------------------------------------------------------
# testing suit
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        bt = BasicTranslator('test')
        r = bt.request("http://www.baidu.com")
        print(r.text)
        return 0


    def test2():
        gt = GoogleTranslator()
        # r = gt.translate('auto', 'auto', 'Hello, World !!')
        # r = gt.translate('auto', 'auto', '你吃饭了没有?')
        # r = gt.translate('auto', 'auto', '长')
        r = gt.translate('auto', 'auto', 'long')
        # r = gt.translate('auto', 'auto', 'kiss')
        # r = gt.translate('auto', 'auto', '亲吻')
        import pprint
        print(r['translation'])
        # pprint.pprint(r['info'])
        return 0


    def test3():
        t = YoudaoTranslator()
        r = t.translate('auto', 'auto', 'kiss')
        import pprint
        pprint.pprint(r)
        print(r['translation'])
        return 0


    def test5():
        t = BaiduTranslator()
        r = t.translate('en-US', 'zh-CN', '吃饭了没有?')
        import pprint
        pprint.pprint(r)
        print(r['translation'])
        return 0
    # test1()
    # test2()
    # test3()
    test5()
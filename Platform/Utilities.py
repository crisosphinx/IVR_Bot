import os
import json
import Documents
import Settings
import requests
from random import randint
from bs4 import BeautifulSoup as Bs


class SplitDir(object):
    def __init__(self, _dir=str()) -> None:
        self.dir = _dir
        self.os = os.name

    def __call__(self) -> str:
        _dir = str()
        if self.os == "nt":
            _dir = "/".join(self.dir.split("\\")[:-1])
        elif self.os == "posix":
            _dir = "/".join(self.dir.split("/")[:-1])

        return _dir


class LinkRead(object):
    def __init__(self) -> None:
        self.location = "{0}/link_repository.json".format(
            SplitDir(Documents.__file__)()
        )

    def __call__(self) -> dict:
        return self.run()

    def run(self) -> dict:
        with open(self.location, 'r') as f:
            return json.load(f)


class LinkWrite(object):
    def __init__(self, _location: str, _name: str, _example: str) -> None:
        self.location = "{0}/link_repository.json".format(
            SplitDir(Documents.__file__)()
        )
        self.json = LinkRead()()
        self.json[_location].setdefault(_name, _example)

    def __call__(self) -> None:
        with open(self.location, 'r+') as f:
            json.dump(self.json, f)


class LinkPop(object):
    def __init__(self, _location: str, _name: str) -> None:
        self.location = "{0}/link_repository.json".format(
            SplitDir(Documents.__file__)()
        )
        self.json = LinkRead()()
        self.json[_location].pop(_name)

    def __call__(self) -> None:
        with open(self.location, 'r+') as f:
            json.dump(self.json, f)


class SettingsRead(object):
    def __init__(self) -> None:
        self.location = "{0}/settings.json".format(
            SplitDir(Settings.__file__)()
        )

    def __call__(self) -> dict:
        return self.run()

    def run(self) -> dict:
        with open(self.location, 'r') as f:
            return json.load(f)


class SrcDir(object):
    def __init__(self):
        self.location = "{0}/srcdir.json".format(
            SplitDir(Documents.__file__)()
        )

    def __call__(self) -> dict:
        with open(self.location, 'r') as f:
            return json.load(f)


class ExamplesRead(object):
    def __init__(self):
        self.location = "{0}/examples.json".format(
            SplitDir(Documents.__file__)()
        )

    def __call__(self) -> dict:
        with open(self.location, 'r') as f:
            return json.load(f)


class ExamplesWrite(object):
    def __init__(self, _name: str, _example: str) -> None:
        self.location = "{0}/examples.json".format(
            SplitDir(Documents.__file__)()
        )
        self.json = ExamplesRead()()
        if _name in self.json.keys():
            self.json[_name].append(_example)
        else:
            self.json.setdefault(_name, []).append(_example)

    def __call__(self) -> None:
        with open(self.location, 'r+') as f:
            json.dump(self.json, f)


class Token(object):
    def __init__(self) -> None:
        """
        Attains the token location and returns the path back.
        """
        self.possible_loc = {
            "nt": ['C:\\Users\\jeff3\\Desktop\\Tokens.json', "J:\\Tokens.json"],
            "posix": ['/usr/bin/Tokens.json']
        }

    def __call__(self) -> str:
        """
        When class is called...
        :return:
        """
        return self.get()

    def get(self) -> str:
        """
        Get the JSON Token location for running the bot.
        :return:
        """
        _attained_path = str()
        for _path in self.possible_loc[os.name]:
            if os.path.isfile(_path):
                _attained_path = _path

        if len(_attained_path) > 0:
            return _attained_path
        else:
            return str()


class DefinitionUnity(object):
    def __init__(self, _query=str()) -> None:
        self.search_query = _query
        self.year = None
        self.soup = None
        self.h2 = "h3"

    def __call__(self, embed: bool) -> list or str or bool:
        if embed:
            try:
                return self.get_description()
            except IndexError:
                return False
        else:
            _get = self.get_description()
            _term = "```"
            _term += "\n{0}\n\n".format(_get[0])
            for _each in _get[1:]:
                _term += "{0}\n".format(_each)
            _term += "```"
            return _term

    def look_for_term(self, name: str):
        _searcher = SrcDir()()
        _tried = None
        found = False
        for year in list(_searcher.keys()):
            if not found:
                for term in _searcher[year]:
                    _term = term.lower()
                    if "." in _term:
                        if name.lower() == _term.split(".")[1].lower():
                            _tried = term
                            found = True
                            self.year = year
                    else:
                        if name.lower() == _term.lower():
                            _tried = term
                            found = True
                            self.year = year

                if _tried is None:
                    for term in _searcher[year]:
                        if name.lower() in term.lower():
                            _tried = term
                            found = True
                            self.year = year
            else:
                break

        return _tried

    def search(self) -> tuple:
        _a = self.look_for_term(self.search_query)
        if _a is not None:
            _link = "{0}{1}.html".format(LinkRead()()["{0}API".format(self.year)], _a)
            _page = requests.get(_link)
            self.soup = Bs(_page.content, "html.parser")
            return _a, self.soup, _link
        else:
            return None, None, None

    def get_description(self) -> list or bool:
        """

        :return:
        """
        _title, _webpage, _link = self.search()

        if _title is not None:
            _term = list()
            _d = list()
            _description = list()
            _temp = dict()
            _check = bool()
            _properties_hit = bool()
            j = 0
            _divs = _webpage.find_all("div", class_="subsection")
            while j < len(_divs):
                for _h2 in _divs[j].find_all(self.h2):
                    if "Description" in _h2:
                        _childs = _h2.parent.findChildren()
                        _childs = _h2.parent.find_all("p")
                        _next_childs = _divs[j+1].find_all("p")
                        _term.append("{0}\n{1}".format(_childs[0].string, _next_childs[0].getText()))
                j += 1

            for _a in _webpage.find_all("div", class_="subsection"):
                for _b in _a.find_all(self.h2):
                    if not _check:
                        i = 0
                        if _b.string != "Inherited Members" and _b.string != "Description":
                            _bstring = _b.string
                            if _b.string == "Properties" and _properties_hit:
                                _bstring = "Inherited Members"
                            _items = list()
                            _trs = _b.parent.findChildren()[1].find_all("tr")
                            for _tr in _trs:
                                _desc = _tr.parent.find_all("td")
                                while i < len(_desc):
                                    _items.append("{0} - {1}".format(_desc[i].string, _desc[i+1].string))
                                    i += 2
                            _temp.setdefault(_bstring, _items)
                        if _b.string == "Operators":
                            _check = True
                        if _b.string == "Properties":
                            _properties_hit = True

            _description.append(_title)
            _description.append(_link)
            _description.append("{0}\n".format(_term[0]))
            for _tmp in _temp:
                if "►" not in _tmp:
                    _description.append("\n‣ {0}\n{1}\n".format(_tmp, "-" * 10))
                    for _info in _temp[_tmp]:
                        _description.append("🗹\t{0}".format(_info).replace("\n", " "))

            return _description
        else:
            return False


class DefineWord(object):
    def __init__(self) -> None:
        self.soup = None
        self.define = LinkRead()()["Websites"]["Define"]
        self.word = str()
        self.link = str()
        self.defdict = {
            "noun": [],
            "verb": [],
            "adjective": [],
            "adverb": []
        }

    def __call__(self, _word: str) -> tuple:
        self.word = _word
        self.info()
        return self.word, self.link, self.defdict

    def search(self) -> tuple:
        if self.word is not None:
            _link = "{0}{1}".format(self.define, self.word)
            _page = requests.get(_link)
            self.soup = Bs(_page.content, "html.parser")
            return self.word, self.soup, _link
        else:
            return None, None, None

    def info(self):
        self.word, self.soup, self.link = self.search()
        for _each in self.soup.find_all("span", class_="e1q3nk1v1"):
            if _each.string is not None and len(_each.string.split(" ")) > 3:
                _identifier = _each.parent.parent.parent.parent.parent.find("span", class_="luna-pos")
                if _identifier is not None and _identifier.string is not None:
                    _identifier = _identifier.string.replace(",", "")
                    self.defdict.setdefault(_identifier, []).append(_each.string)


class GetRandomExample(object):
    def __init__(self) -> None:
        self.exread = ExamplesRead()()

    def __call__(self, _word: str) -> str:
        return self.select(_word)

    def select(self, _word: str) -> str:
        if _word in self.exread.keys():
            _max = len(list(self.exread[_word]))
            _get_random = randint(0, _max) - 1
            if _max > 0:
                return self.exread[_word][_get_random]
            else:
                return ""


if __name__ == '__main__':
    _x = DefinitionUnity("camera")(False)
    print(_x, len(_x))
    # DefineWord()("purple")

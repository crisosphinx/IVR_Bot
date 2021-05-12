from __future__ import annotations

import os
import sys
import cattr
import attr
from typing import Optional, List, Any
import json
import requests
from Platform import Utilities
from threading import Thread
from queue import Queue
import Documents

AMT = int()
GOT = list()


@attr.dataclass
class DocumentRoot(object):
    link: Optional[Any]
    title: str
    children: Optional[List[DocumentRoot]]


class JsonAttain(object):
    def __call__(self):
        return Utilities.LinkRead()()


class ExtractData(object):
    def __init__(self, _file=str(), _doc=str()):
        self.file = _file
        self.doc = _doc
        self.json = dict()
        self.removal = [
            "children", "link", "null",
            "title", "toc", None, "Attributes",
            "Assemblies", "Classes", "Enumerations",
            "Interfaces"
        ]
        self.main_topics = list()

    def __call__(self) -> dict:
        _new_obj = dict()
        self.json_gettr()
        data: DocumentRoot = cattr.GenConverter().structure(self.json, DocumentRoot)
        self.main_topics = [x.title for x in data.children]

        self.process(_new_obj)

        return _new_obj

    def json_gettr(self) -> None:
        with open(self.file, 'r') as f:
            self.json = json.load(f)

    def titles(self, obj: DocumentRoot):
        new_obj = {
            obj.title: {}
        }
        if obj.children:
            for child in obj.children:
                new_obj[obj.title][child.title] = self.titles(child)[child.title]
        return new_obj

    def process(self, _new_obj: dict) -> None:
        for topic in self.main_topics:
            _new_obj.setdefault(topic, dict())

        _temp_var = str()
        for each in self.dict_generator(indict=self.json):
            _test_main = list(set(each).intersection(self.main_topics))
            if len(_test_main) > 0:
                _temp_var = _test_main[0]
            _count = each.count("children") - 1
            _diff = list(set(each).difference(self.removal))
            if _diff:
                # print(_count, _diff[0])
                _html = "{0}{1}.html".format(JsonAttain()()[self.doc], _diff[0])
                _new_obj[_temp_var].setdefault(_diff[0], _html)
                # request = requests.get("{0}{1}.html".format(_html, _diff[0]))
                # if request.status_code == 200:
                #     print(_diff[0])
                #     _new_obj[_temp_var].append(_diff[0])

    def dict_generator(self, indict, pre=None):
        pre = pre[:] if pre else []
        if isinstance(indict, dict):
            for key, value in indict.items():
                if isinstance(value, dict):
                    for d in self.dict_generator(value, pre + [key]):
                        yield d
                elif isinstance(value, list) or isinstance(value, tuple):
                    for v in value:
                        for d in self.dict_generator(v, pre + [key]):
                            yield d
                else:
                    yield pre + [key, value]
        else:
            yield pre + [indict]


def work(queue):
    """
    The function take task from input_q and print or return with some code changes (if you want)
    """
    global COUNT
    global GOT
    while True:
        item = queue.get()
        if item == "STOP":
            break

        request = requests.get(item[1])
        if request.status_code == 200:
            GOT.append(item[0])
        COUNT += 1
        sys.stdout.write("\r[{0}%]".format(round(COUNT/AMT*100, 2)))


def write(name: str):
    srcdir = "{0}\\srcdir.json".format(
        "\\".join(Documents.__file__.split("\\")[:-1])
    )
    if os.path.isfile(srcdir):
        with open(srcdir, "r+") as file:
            data = json.load(file)
            data.update({name: GOT})
            file.seek(0)
            json.dump(data, file)

    else:
        with open(srcdir, "w") as f:
            json.dump({name: GOT}, f)


def main(_file=str()):
    global AMT
    input_q = Queue()
    results = ExtractData(_file=_file, _doc=_file.split(".")[0] + "API")()
    _total = list()
    for _eachheader in results:
        for task in results[_eachheader]:
            _total.append(task)
    AMT = len(_total)
    threads_number = 100
    workers = [Thread(target=work, args=(input_q,), ) for i in range(threads_number)]

    # start workers here
    for w in workers:
        w.start()

    # start delivering tasks to workers
    for _eachheader in results:
        for task in results[_eachheader]:
            # print("{0} has been put into a job...".format(task))
            # print(results[_eachheader][task])
            input_q.put((task, results[_eachheader][task],))

    for i in range(threads_number):
        input_q.put("STOP")

    # join all workers to main thread here:
    for w in workers:
        w.join()

    write(_file.split(".")[0])

    print("\nFinished\n\n")


if __name__ == '__main__':
    _docs = JsonAttain()()
    for each in _docs:
        COUNT = 0
        if "API" in each:
            main(_file="{0}.json".format(each.replace("API", "")))  # "2019_4.json")

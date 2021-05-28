#!/usr/bin/env python3

from __future__ import print_function
import pickle
import os.path
from datetime import datetime
from Documents.formatter import *
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from Platform import Utilities
from threading import Thread
from multiprocessing import Process

DEBUG = Utilities.SettingsRead()()['DEBUG']


class AttainGoogleDoc(object):
    def __init__(self, document_id=str()) -> None:
        """
        Get a relative document.
        """
        self.docuid = document_id
        self.scopes = ['https://www.googleapis.com/auth/documents.readonly']

    def __call__(self) -> list:
        """
        Returns the google document in a list of information.
        :return:
        """
        return self.googledoc()

    def googledoc(self) -> list:
        """
        Attains the google document and creates a pickled token.
        :return:
        """
        creds = None
        rules = list()

        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                json_path = Utilities.Token()()
                flow = InstalledAppFlow.from_client_secrets_file(
                    json_path, self.scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('docs', 'v1', credentials=creds)

        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=self.docuid).execute()

        for each in document.get("body")["content"]:
            if "paragraph" in each.keys():
                _text = each["paragraph"]["elements"][0]["textRun"]["content"]
                if _text != "\n":
                    rules.append(_text.replace("\n", ""))

        return rules


class AttainGoogleClass(object):
    def __init__(self, _classname: str) -> None:
        self.scopes = [
            'https://www.googleapis.com/auth/classroom.courses.readonly',
            'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
            'https://www.googleapis.com/auth/classroom.topics.readonly',
            "https://www.googleapis.com/auth/classroom.rosters"
        ]
        self.classname = _classname
        self.courses = None
        self.service = None
        self.class_groupings = dict()
        self.topic_groupings = dict()
        self.class_rosters = list()
        self.course_info()

        self.student_collective = dict()

    def __call__(self):
        return self.get_class_work()

    def course_info(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                json_path = Utilities.Token()()
                flow = InstalledAppFlow.from_client_secrets_file(
                    json_path, self.scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        # Attain our service
        self.service = build('classroom', 'v1', credentials=creds)

        # Call the Classroom API
        results = self.service.courses().list(pageSize=10).execute()
        self.courses = results.get('courses', [])

        self.class_rosters = [" - {0}".format(x['name']) for x in self.courses]

    def query_info(self):
        course = None
        for each_class in self.courses:
            if self.classname == each_class['name']:
                course = each_class
                break

        course_id = course['id']
        classes = self.service.courses().courseWork().list(courseId=course_id).execute()
        for each_work in classes['courseWork']:
            _due_date = "{0}-{1}-{2}".format(
                each_work['dueDate']['year'],
                each_work['dueDate']['month'],
                each_work['dueDate']['day']
            )
            self.class_groupings.setdefault(each_work['title'], []).append(each_work['topicId'])
            self.class_groupings.setdefault(each_work['title'], []).append(_due_date)
            self.class_groupings.setdefault(each_work['title'], []).append(each_work['alternateLink'])
        topics = self.service.courses().topics().list(courseId=course_id).execute()
        for each_topic in topics['topic']:
            self.topic_groupings.setdefault(each_topic['topicId'], each_topic['name'])

        return [self.class_groupings, self.topic_groupings]

    def get_class_work(self):
        a = self.query_info()
        _wrk_for_week = dict()
        for each in a[0]:
            _datetime = str(datetime.now()).split(" ")[0][2:]
            _date = datetime.strptime(_datetime, "%y-%m-%d")
            _due_date = datetime.strptime(a[0][each][1][2:], "%y-%m-%d")
            _days = int(str(_due_date - _date).split(" ")[0])
            if -1 < _days < 8:
                _temp_work = [each, a[0][each][1], a[0][each][2]]
                _wrk_for_week.setdefault(a[0][each][0], []).append(_temp_work)
        if len(list(_wrk_for_week.keys())) == 0:
            _wrk_for_week.setdefault('Complete', ['Complete'])

        _work_due = dict()
        b = dict()
        # Get the topicIds
        if list(_wrk_for_week.keys())[0] != 'Complete':
            for top_id in list(a[1].keys()):
                if top_id in _wrk_for_week.keys():
                    for each_assignment in _wrk_for_week[top_id]:
                        b.setdefault(each_assignment[0], []).append(each_assignment[1])
                        b.setdefault(each_assignment[0], []).append(each_assignment[2])
                        _work_due.setdefault(a[1][top_id], b)
        else:
            _work_due = _wrk_for_week
        return _work_due

    def process_token(self, course_id=str(), token=str()) -> None:
        if token:
            students = self.service.courses().students().list(courseId=course_id, pageToken=token).execute()
        else:
            students = self.service.courses().students().list(courseId=course_id).execute()
        if 'nextPageToken' in students:
            for each_student in students['students']:
                self.student_collective.setdefault(each_student['profile']['name']['fullName'], each_student)
            self.process_token(
                course_id=course_id,
                token=students['nextPageToken']
            )

    def grades(self, username: str, results: dict):
        course = None
        for each_class in self.courses:
            if self.classname == each_class['name']:
                course = each_class
                break

        course_id = course['id']
        classes = self.service.courses().courseWork().list(courseId=course_id).execute()
        self.process_token(course_id=course_id)

        _title = str()
        _max = str()
        _workid = str()

        for each_work in classes['courseWork']:
            if "maxPoints" in list(each_work.keys()):
                _max = each_work['maxPoints']
                _title = each_work['title']
                _workid = each_work['id']
                _descript = each_work['description']
                _link = each_work['alternateLink']

                if username in self.student_collective.keys():
                    each = self.student_collective[username]
                    _name = each['profile']['name']['fullName']
                    if _name not in results.keys():
                        results.setdefault(_name, [])
                    a = self.service.courses().courseWork().studentSubmissions().list(
                        courseId=course_id,
                        courseWorkId=_workid,
                        userId=each['userId']
                    ).execute()

                    for assignment in a['studentSubmissions']:
                        if "assignedGrade" in assignment:
                            if DEBUG:
                                print("{0}\n--------\n{1}\n{2}/{3}\n{4}\n{5}".format(
                                    _name,
                                    _title,
                                    assignment['assignedGrade'],
                                    _max,
                                    _descript,
                                    _link
                                ))
                            _info = {
                                _title: [
                                    "Assignment Description: {2}\n{0}/{1}".format(
                                        assignment['assignedGrade'],
                                        _max,
                                        _descript
                                    ),
                                    _link
                                ]
                            }
                            results[_name].append(_info)

    def roster(self) -> list:
        return [len(self.class_rosters), "\n".join(self.class_rosters)]


class AttainGoogleSheet(object):
    def __init__(self, document_id=str()) -> None:
        """
        Get a relative document.
        """
        self.docuid = document_id
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.sheet = self.googlesheet()

    def __call__(self):
        return self.getallvalues()

    def googlesheet(self):
        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                json_path = Utilities.Token()()
                flow = InstalledAppFlow.from_client_secrets_file(
                    json_path, self.scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds)
        # Call the Sheets API
        sheet = service.spreadsheets()

        return sheet

    def getallvalues(self) -> dict:
        result = self.sheet.values().get(
            spreadsheetId=self.docuid,
            range="Sheet1!A1:B",
        ).execute()
        rows = result.get("values", [])
        _dict = dict()

        for each in rows:
            _dict.setdefault(each[0], int(each[1]))
        return _dict

    def addvalues(self, revised_dict=None):
        if revised_dict is None:
            revised_dict = dict()

        add_values = list()
        for key in revised_dict:
            add_values.append([key, revised_dict[key]])

        result = self.sheet.values()
        result.update(
            spreadsheetId=self.docuid,
            range="Sheet1!A1:B",
            valueInputOption="USER_ENTERED",
            body={"values": add_values}
        ).execute()

    def updatevalue(self, name: str):
        processdict = self.getallvalues()
        if name in processdict.keys():
            processdict[name] += 1
        else:
            processdict.setdefault(name, 1)
        self.addvalues(revised_dict=processdict)


class ThreadClass(Thread):
    def __init__(self, _class=str(), _user=str()):
        self.results = dict()
        super(ThreadClass, self).__init__(
            daemon=True,
            target=AttainGoogleClass(_classname=_class).grades,
            args=(_user, self.results, )
        )

    def attain_class_grades(self) -> dict:
        self.start()
        self.join()
        return self.results


class ProcessClass(Process):
    def __init__(self, _class=str(), _user=str()):
        self.results = dict()
        super(ProcessClass, self).__init__(
            target=AttainGoogleClass(_classname=_class).grades,
            args=(_user, self.results, )
        )

    def attain_class_grades(self) -> dict:
        self.start()
        self.join()
        return self.results


def main():
    """Shows basic usage of the Classroom API.
    Prints the names of the first 10 courses the user has access to.
    """

    # _class = "R5 Universe: Introduction to Unity in 3D/VR"
    # _user = "Chelsie Harrison"
    # _assignments = ThreadClass(_class, _user).attain_class_grades()
    # return _assignments
    _sheet_docid = "1CgWrVv-iomNiuZOIJXKkaWIYzVyfc_itQ1Fv9O97_2U"
    _doc = AttainGoogleSheet(document_id=_sheet_docid)

    _words = Utilities.SrcDir()()
    _new_read = dict()
    for year in _words:
        for key in _words[year]:
            _new_read.setdefault(key, 0)

    for _example in Utilities.ExamplesRead()():
        _new_read.setdefault("'" + _example, 0)

    _links = Utilities.LinkRead()()
    _names = [x for x in _links if "API" not in x]
    for _name in _names:
        for _keyname in list(_links[_name].keys()):
            _new_read.setdefault(_keyname, 0)

    _new_read.setdefault("help", 0)
    _new_read.setdefault("ping", 0)
    _new_read.setdefault("download", 0)
    _new_read.setdefault("website", 0)
    _new_read.setdefault("about", 0)
    _new_read.setdefault("troubleshoot", 0)

    _doc.addvalues(_new_read)
    # _doc.updatevalue("Gizmos")


if __name__ == '__main__':
    print(main())

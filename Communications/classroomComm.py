#!/usr/bin/env python3

from __future__ import print_function
import pickle
from datetime import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from globalVars import *

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
    'https://www.googleapis.com/auth/classroom.topics.readonly',
]


class CourseInfo:
    def __init__(self):
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
                cred_path = 'I:\\credentials.json'
                if not os.path.isfile(cred_path):
                    cred_path = 'C:\\Users\\jeff3\\Desktop\\credentials.json'
                flow = InstalledAppFlow.from_client_secrets_file(
                    cred_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        # Attain our service
        self.service = build('classroom', 'v1', credentials=creds)

        # Call the Classroom API
        results = self.service.courses().list(pageSize=10).execute()
        self.courses = results.get('courses', [])

        #
        if DEBUG:
            if not self.courses:
                print('No courses found.')
            else:
                print('Courses:')
                for course in self.courses:
                    print(course['name'])

        self.class_rosters = [" - {0}".format(x['name']) for x in self.courses]
        self.class_groupings = dict()
        self.topic_groupings = dict()

    def query_info(self, class_name=str()):
        course = None
        for each_class in self.courses:
            if class_name == each_class['name']:
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

    def get_class_work(self, class_name=str()):
        a = self.query_info(class_name=class_name)

        _wrk_for_week = dict()
        for each in a[0]:
            _datetime = str(datetime.now()).split(" ")[0][2:]
            _date = datetime.strptime(_datetime, "%y-%m-%d")
            _due_date = datetime.strptime(a[0][each][1][2:], "%y-%m-%d")
            _days = int(str(_due_date - _date).split(" ")[0])
            if -1 < _days < 8:
                if DEBUG:
                    print("{0} is the topidId".format(a[0][each][0]))
                    print("{0} is the dueDate".format(a[0][each][1]))
                    print("{0} is the alternativeLink".format(a[0][each][2]))
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

    def roster(self):
        return [len(self.class_rosters), "\n".join(self.class_rosters)]


def main():
    """Shows basic usage of the Classroom API.
    Prints the names of the first 10 courses the user has access to.
    """

    assignments = CourseInfo().get_class_work("Universe: Introduction to Unity in VR")
    print(assignments)


if __name__ == '__main__':
    main()
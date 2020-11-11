#!/usr/bin/env python3

from __future__ import print_function
import pickle
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
        i = 0
        course = None
        for each_class in self.courses:
            if class_name == each_class['name']:
                course = each_class
                break
            i += 1

        course_id = course['id']
        classes = self.service.courses().courseWork().list(courseId=course_id).execute()
        for each_work in classes['courseWork']:
            self.class_groupings.setdefault(each_work['title'], each_work['topicId'])
        topics = self.service.courses().topics().list(courseId=course_id).execute()
        for each_topic in topics['topic']:
            self.topic_groupings.setdefault(each_topic['topicId'], each_topic['name'])

        return [self.class_groupings, self.topic_groupings]

    def recent_class(self, class_name=str()):
        a = self.query_info(class_name=class_name)
        for each in list(a[1].keys()):
            print(each)

    def print_info(self):
        return [len(self.class_rosters), "\n".join(self.class_rosters)]


def main():
    """Shows basic usage of the Classroom API.
    Prints the names of the first 10 courses the user has access to.
    """

    CourseInfo().query_info("VR App Development")


if __name__ == '__main__':
    main()

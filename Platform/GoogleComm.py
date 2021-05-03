#!/usr/bin/env python3

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from Platform import Utilities


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
    def __init__(self, document_id=str()) -> None:
        self.docuid = document_id
        self.scopes = [
            'https://www.googleapis.com/auth/classroom.courses.readonly',
            'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
            'https://www.googleapis.com/auth/classroom.topics.readonly',
        ]

    def __call__(self):
        return "something"

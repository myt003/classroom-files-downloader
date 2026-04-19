from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

import io
import os
import os.path
from os import path
import pprint


def sanitize_folder_name(name):
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for ch in invalid_chars:
        name = name.replace(ch, '-')
    return name.strip()


def main():

    service = get_classroom_service()
    courses = service.courses().list(pageSize=20).execute()
    for course in courses['courses']:
        print(course['name'])

    downd_files = list()

    for course in courses['courses']:

        course_name = sanitize_folder_name(course['name'])
        course_id   = course['id']
        print("\nDownloading files for course :", course_name)

        if not path.exists(course_name):
            os.mkdir('./' + course_name)
            os.mkdir('./' + course_name + "/cours")
            os.mkdir('./' + course_name + "/td")
        else:
            print("{} Already exists".format(course_name))

        # Fetch everything — announcements, assignments AND materials
        anoncs    = get_all_announcements(service, course_id)
        works     = get_all_coursework(service, course_id)
        materials = get_all_coursework_materials(service, course_id)

        downd_files += download_annonc_files(anoncs, course_name)
        downd_files += download_works_files(works, course_name)
        downd_files += download_material_files(materials, course_name)

    pprint.pprint(downd_files)


# ─── Paginated fetchers ────────────────────────────────────────────────────────

def get_all_announcements(service, course_id):
    results, page_token = [], None
    while True:
        resp = service.courses().announcements().list(
            courseId=course_id, pageToken=page_token).execute()
        results.extend(resp.get('announcements', []))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return results


def get_all_coursework(service, course_id):
    results, page_token = [], None
    while True:
        resp = service.courses().courseWork().list(
            courseId=course_id, pageToken=page_token).execute()
        results.extend(resp.get('courseWork', []))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return results


def get_all_coursework_materials(service, course_id):
    """Fetch teacher-posted materials (the 'Material' type in Classroom UI)."""
    results, page_token = [], None
    while True:
        try:
            resp = service.courses().courseWorkMaterials().list(
                courseId=course_id, pageToken=page_token).execute()
            results.extend(resp.get('courseWorkMaterial', []))
            page_token = resp.get('nextPageToken')
            if not page_token:
                break
        except HttpError as e:
            print(f"  Could not fetch materials for course: {e}")
            break
    return results


# ─── Auth helpers ──────────────────────────────────────────────────────────────

def get_classroom_service():
    SCOPES = [
        'https://www.googleapis.com/auth/classroom.courses.readonly',
        'https://www.googleapis.com/auth/classroom.announcements.readonly',
        'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',  # ← NEW
        'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly',
    ]

    creds = None
    if os.path.exists('classroom-token.json'):
        creds = Credentials.from_authorized_user_file('classroom-token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('classroom-token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('classroom', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print('An error occurred: %s' % error)


def download_file(file_id, file_name, course_name, subfolder):
    SCOPES = ['https://www.googleapis.com/auth/drive']

    creds = None
    if os.path.exists('drive-token.json'):
        creds = Credentials.from_authorized_user_file('drive-token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('drive-token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

        fh.seek(0)
        dest_path = os.path.join('./', course_name, subfolder, file_name)
        with open(dest_path, 'wb') as f:
            f.write(fh.read())

    except HttpError as error:
        print(f'An error occurred: {error}')


# ─── Download helpers ──────────────────────────────────────────────────────────

def _process_materials(materials_list, course_name, subfolder, label):
    """Generic helper: iterate a list of items with .get('materials'), download driveFiles."""
    downloaded = []
    present_files = getListOfFiles(os.path.join('./', course_name))

    for item in materials_list:
        for val in item.get('materials', []):
            try:
                file_id   = val['driveFile']['driveFile']['id']
                file_name = val['driveFile']['driveFile']['title']

                if file_name[0:10] == "[Template]":
                    alt = val['driveFile']['driveFile']['alternateLink']
                    file_id = alt[alt.find('=') + 1:]

                extension = os.path.splitext(file_name)[1].lstrip('.').lower()

                if valid(extension) and file_name not in present_files:
                    print(f"DOWNLOADING {file_name} -> {subfolder}/")
                    download_file(file_id, file_name, course_name, subfolder)
                    downloaded.append(f"{label} : {course_name}/{subfolder} : {file_name}")
                elif file_name in present_files:
                    print(file_name, "already exists")
                elif not valid(extension):
                    print('Unsupported file type:', extension)
            except KeyError:
                continue  # Not a driveFile (YouTube, link, form…)

    return downloaded


def download_annonc_files(announcements, course_name):
    """Announcements → cours/"""
    return _process_materials(announcements, course_name, 'cours', 'Annonce')


def download_works_files(works, course_name):
    """Assignments (courseWork) → td/"""
    return _process_materials(works, course_name, 'td', 'Devoir')


def download_material_files(materials, course_name):
    """Teacher materials (courseWorkMaterials) → cours/"""
    return _process_materials(materials, course_name, 'cours', 'Material')


# ─── Utilities ─────────────────────────────────────────────────────────────────

def valid(ext):
    return ext in [
        'pdf', 'docx', 'pptx', 'png', 'jpg', 'jpeg', 'html', 'css', 'js',
        'java', 'class', 'txt', 'r', 'm', 'sql', 'doc', 'mp3', 'rar', 'zip',
        'py', 'c'
    ]


def getListOfFiles(dirName):
    """Return flat list of filenames (no path) under dirName — works on Windows & Linux."""
    allFiles = []
    for entry in os.listdir(dirName):
        fullPath = os.path.join(dirName, entry)
        if os.path.isdir(fullPath):
            allFiles += getListOfFiles(fullPath)
        else:
            allFiles.append(os.path.basename(fullPath))
    return allFiles


if __name__ == '__main__':
    main()
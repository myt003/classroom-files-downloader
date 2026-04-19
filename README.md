A script that automates downloading Google Classroom files and organizes them each in their appropriate folder.

Prerequisities:

Python

Pip

How to setup the necessary files for the script?

1- First we need to create a project in Google Cloud Platform : https://developers.google.com/workspace/guides/create-project

2- Next we need to enable Google Classroom API and Google Drive API in our project : https://developers.google.com/workspace/guides/enable-apis

3- Now we need to configure the OAuth consent screen so that we can be able to create credentials that we will later download and allows our app to access our data.

    This can be achieved by following this guide : https://developers.google.com/workspace/guides/configure-oauth-consent.

    There are 2 important steps in this part :

    1-Add our email address to test users, just add the email address (addresses) you're gonna use to access the app.

    2-Add the required scopes, the ones that our app will need to function properly ,

    For Google Classroom API we will need these scopes
    SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.announcements.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly'
    ]
    For Google Drive API we will need this one :
    SCOPES = ['https://www.googleapis.com/auth/drive']

4- After configuring the OAuth consent screen, we can now create credentials in our GCP project, we need to create OAuth Client ID for a desktop app :

https://developers.google.com/workspace/guides/create-credentials#desktop-app

If you still didn't configure the OAuth consent screen , you will get a warning and won't be able to create credentials.

5- Finally, after creating the credentials that our app needs to function, we can now download the json file that contains our credentials. The download button for that file should be easily accessible. After downloading that file we need to rename it to credentials.json and place it next to the python script ClassroomFilesDownloader.py.

ALMOST DONE!!!!!!!

Now we need to execute a command in our terminal : pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

This is mentioned here in this guide : https://developers.google.com/drive/api/quickstart/python

\*\* Now we are ready to execute our script but before that we need to tell our script the number of courses to download by editing a variable value in the script:

    - open the ClassroomFilesDownloader.py in any text editor you want

    - CTRL +F  to look for the word "pageSize"

    - change the value of that variable to how many courses you want to download, it works by the newest to oldest order.

 Changelog
v2.0.0 — Contributions by @myt003

2. Fixed FileNotFoundError on Windows for courses with / in their name
Course names like SOA24/25 caused os.mkdir() to fail on Windows because / is interpreted as a path separator.
→ Added sanitize_folder_name() which replaces all Windows-invalid characters (/ \ : * ? " < > |) with -.
3. Fixed files not being saved in cours/ and td/ subfolders
The original script created cours/ and td/ subdirectories but always saved files to the course root folder.
→ download_file() now accepts a subfolder parameter and saves to the correct path.
4. Fixed missing files due to silent KeyError skipping
The try/except KeyError block was wrapping the entire for val in materials loop. If one material failed (e.g. a YouTube link or Google Form), the entire assignment's remaining files were silently skipped.
→ Moved try/except inside the loop so each material is handled independently.
5. Fixed missing files due to no pagination
The Classroom API returns a limited number of results per page (default ~20). Courses with more than 20 announcements or assignments had the rest silently ignored.
→ Added get_all_announcements() and get_all_coursework() which loop over nextPageToken until all items are fetched.
6. Fixed broken duplicate-file detection on Windows
getListOfFiles() used ch.rfind('/') to extract filenames, but Windows uses \ as the path separator, so rfind('/') returned -1 and the full path was returned instead of just the filename. This broke the "already exists" check.
→ Replaced with os.path.basename() which works correctly on both Windows and Linux.
7. Fixed ' sql' typo in valid() function
A leading space in ' sql' meant .sql files never matched and were always skipped.
→ Fixed to 'sql' and added .lower() so extensions like .PDF are handled correctly.
✨ New Features
8. Added support for courseWorkMaterials (teacher-posted materials)
The original script only fetched announcements and courseWork (assignments). Teacher-posted materials — visible in the Classroom UI as standalone items with a document icon — use a separate API endpoint (courseWorkMaterials) and were never downloaded.
→ Added get_all_coursework_materials() and download_material_files(). These files are saved to cours/.
→ Added the required scope: classroom.courseworkmaterials.readonly.

⚠️ Because a new OAuth scope was added, you must delete classroom-token.json and re-authenticate on the next run.

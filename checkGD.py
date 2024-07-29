import json
import os
import io
import datetime
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class CheckGoogleDrive:
    def __init__(self, service_account_file, parent_folder_id, hash_map_file):
        self.service_account_file = service_account_file
        self.parent_folder_id = parent_folder_id
        self.hash_map_file = hash_map_file
        self.service = None
        self.hash_map = {}

    def authenticate_and_create_service(self):
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=['https://www.googleapis.com/auth/drive.readonly'])
        self.service = build('drive', 'v3', credentials=credentials)

    def list_folders_in_folder(self, parent_folder_id):
        query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        try:
            results = self.service.files().list(q=query, pageSize=1000, fields="nextPageToken, files(id, name, modifiedTime)").execute()
            items = results.get('files', [])

            while 'nextPageToken' in results:
                page_token = results['nextPageToken']
                results = self.service.files().list(q=query, pageSize=1000, pageToken=page_token, fields="nextPageToken, files(id, name, modifiedTime)").execute()
                items.extend(results.get('files', []))

            return items
        except Exception as e:
            print(f"An error occurred while listing folders: {e}")
            return []

    def list_files_in_folder(self, folder_id):
        query = f"'{folder_id}' in parents and trashed=false"
        try:
            results = self.service.files().list(q=query, pageSize=1000, fields="nextPageToken, files(id, name, mimeType, thumbnailLink, webViewLink, modifiedTime)").execute()
            items = results.get('files', [])

            while 'nextPageToken' in results:
                page_token = results['nextPageToken']
                results = self.service.files().list(q=query, pageSize=1000, pageToken=page_token, fields="nextPageToken, files(id, name, mimeType, thumbnailLink, webViewLink, modifiedTime)").execute()
                items.extend(results.get('files', []))

            return items
        except Exception as e:
            print(f"An error occurred while listing files: {e}")
            return []

    def read_file_content(self, file_id):
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            fh.seek(0)
            return fh.read().decode('utf-8')
        except Exception as e:
            print(f"An error occurred while reading file content: {e}")
            return None

    def load_hash_map(self):
        if os.path.exists(self.hash_map_file):
            with open(self.hash_map_file, 'r') as f:
                self.hash_map = json.load(f)
        else:
            self.hash_map = {}

    def save_hash_map(self):
        with open(self.hash_map_file, 'w') as f:
            json.dump(self.hash_map, f, indent=4)

    def check_system_time(self):
        current_time = datetime.datetime.now(pytz.utc)
        print(f"Current system time (UTC): {current_time}")

    def find_thumbnail_link(self, files):
        for file in files:
            if file['name'].startswith('thumbnail'):
                return file.get('thumbnailLink', None)
        return None

    def process_drive(self):
        self.check_system_time()
        self.authenticate_and_create_service()
        self.load_hash_map()

        subfolders = self.list_folders_in_folder(self.parent_folder_id)

        for folder in subfolders:
            if folder['name'] == 'Writing Samples':
                print(f"Skipping folder: {folder['name']}")
                continue

            folder_id = folder['id']
            folder_name = folder['name']
            folder_modified_time = folder['modifiedTime']

            if folder_id in self.hash_map and self.hash_map[folder_id]['modifiedTime'] == folder_modified_time:
                print(f"Skipping unmodified folder: {folder_name}")
                continue

            print(f"Processing folder: {folder_name} (ID: {folder_id})")

            self.hash_map[folder_id] = {
                'name': folder_name,
                'modifiedTime': folder_modified_time,
                'files': {}
            }

            files = self.list_files_in_folder(folder_id)
            thumbnail_link = self.find_thumbnail_link(files)

            for file in files:
                file_id = file['id']
                file_name = file['name']
                file_mime_type = file['mimeType']
                file_modified_time = file['modifiedTime']
                file_web_view_link = file.get('webViewLink', None)  # Get the Google Drive link to view the file

                file_entry = {
                    'name': file_name,
                    'mimeType': file_mime_type,
                    'modifiedTime': file_modified_time,
                    'thumbnailLink': thumbnail_link,
                    'webViewLink': file_web_view_link  # Save the Google Drive link to the file
                }

                if file_name == 'summary.txt':
                    print(f"Found summary.txt in folder: {folder_name}")
                    content = self.read_file_content(file_id)
                    if content:
                        print(f"Contents of {file_name} in folder {folder_name}:\n{content}\n")
                        file_entry['content'] = content
                    else:
                        print(f"Failed to read contents of {file_name} in folder {folder_name}")
                elif file_mime_type == 'application/pdf':
                    print(f"Found PDF in folder: {folder_name}")
                    print(f"PDF ID: {file_id}, PDF Name: {file_name}")
                    if thumbnail_link:
                        print(f"Preview Image: {thumbnail_link}")
                    else:
                        print("No preview image available for this PDF.")
                    if file_web_view_link:
                        print(f"PDF Google Drive Link: {file_web_view_link}")
                    else:
                        print("No Google Drive link available for this PDF.")

                if file_id not in self.hash_map.get(folder_id, {}).get('files', {}):
                    self.hash_map[folder_id]['files'][file_id] = file_entry

        self.save_hash_map()

# Example usage
if __name__ == '__main__':
    service_account_file = 'service_key.json'
    parent_folder_id = '1dE7sfbteMX_GxZdUNZbS6Yz-kj5GxGu4'
    hash_map_file = 'hash_map.json'

    drive_checker = CheckGoogleDrive(service_account_file, parent_folder_id, hash_map_file)
    drive_checker.process_drive()

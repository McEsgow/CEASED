import os
import tempfile
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, BatchHttpRequest, MediaIoBaseDownload

from google.auth.exceptions import RefreshError

class GoogleDrive:
    def __init__(self,
        creds_path:str="auth/credentials.json",
        token_path:str="auth/token.json"
    ) -> None:
        self.SCOPES = ["https://www.googleapis.com/auth/drive"]
        self.creds_path = creds_path
        self.token_path = token_path
        self.creds = None
        self.auth()

        os.mkdir("auth") if not os.path.exists("auth") else None

    def auth(self):
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        try:
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.creds_path, self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)

            with open(self.token_path, "w") as token:
                token.write(self.creds.to_json())
            
        except RefreshError:
            os.remove(self.token_path)
            self.auth()

    def upload_file(self, file_data: bytes, name:str, parent_folder_id: str, mimetype:str='application/octet-stream'):
        try:
            # Use an in-memory bytes buffer instead of a temporary file
            file_buffer = io.BytesIO(file_data)
            service = build('drive', 'v3', credentials=self.creds)
            
            file_metadata = {
                'name': name,
            }

            if parent_folder_id:
                file_metadata["parents"] = [parent_folder_id]

            media = MediaIoBaseUpload(file_buffer, mimetype=mimetype, resumable=True)

            # Perform the upload
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

        # print(f'File uploaded: {name}')

        return file.get("id")

    def download_file(self, file_id) -> bytes:
        try:
            # create drive api client
            service = build("drive", "v3", credentials=self.creds)


            # pylint: disable=maybe-no-member
            request = service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # print(f"Download {int(status.progress() * 100)}.")

        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

        return file.getvalue()

    def search_file(self, query:str, fields:list=["id", "name"]) -> list[dict]:
        """Searches drive for files

        Args:
            query (str): See https://developers.google.com/drive/api/guides/ref-search-terms

        Returns:
            list[dict]: list of files
        """
        try:
            # create drive api client
            service = build("drive", "v3", credentials=self.creds)
            fields = "nextPageToken, files(" + ",".join(field for field in fields) + ")"
            files = []
            page_token = None
            while True:
                # pylint: disable=maybe-no-member
                response = (
                    service.files()
                    .list(
                        q=query,
                        spaces="drive",
                        fields=fields,
                        pageToken=page_token,
                    )
                    .execute()
                )
                files.extend(response.get("files", []))
                page_token = response.get("nextPageToken", None)
                if page_token is None:
                    break

        except HttpError as error:
            print(f"An error occurred: {error}")
            files = None

        return files

    def create_folder(self, name:str, parent_folder_id:str=None):
        try:
            service = build("drive", "v3", credentials=self.creds)
            file_metadata = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
            }

            if parent_folder_id:
                file_metadata["parents"] = [parent_folder_id]

            file = service.files().create(body=file_metadata, fields="id").execute()


            return file.get("id")

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
        
    def delete_file(self, file_id:str):
        try:
            service = build("drive", "v3", credentials=self.creds)
            service.files().delete(fileId=file_id).execute()
        except HttpError as error:
            print(f"An error occurred: {error}")
            
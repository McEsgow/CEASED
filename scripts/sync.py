import os
import time
import ujson as json
import secrets

from base64 import urlsafe_b64encode
from concurrent.futures import ThreadPoolExecutor, as_completed

from key_manager import KeyManager
from encrypt import rsa, aes, hash_md5, hash_sha256
from google_drive import GoogleDrive

KEY_DELIMITER = 'RljUoVUFjfAFkfSEg61sWpcdnipjJe5vFwiVNTF75Nc'


class Drive:
    def __init__(
        self,
        config:dict,
        local_path:str,
        remote_folder_id:str,
        google_drive:GoogleDrive=None,
        key_manager:KeyManager=None
    ) -> None:
        self.config = config
        self.local_path = local_path
        self.gd = google_drive or GoogleDrive()
        self.km = key_manager or KeyManager(self.config['key_folder'])
        self.remote = self.Remote(self, remote_folder_id)
        self.local = self.Local(self, self.local_path)

        self.username = self.config['username']

        self.remote.map_structure()

        self.remote.create_folder('archiveinfo')
        self.remote.create_folder('archiveinfo/users')
        self.remote.create_folder('files')

        if not self.remote.is_valid_path('archiveinfo/id.txt'):
            self.id = secrets.token_urlsafe(24)
            self.remote.create_file('archiveinfo/id.txt', self.id.encode())
            self.km.set_key(f'archives/{self.id}', aes.generate_key())
        else:
            self.id = self.remote.get_file_data('archiveinfo/id.txt').decode()


        self.remote.create_folder(f'archiveinfo/users/{self.username}')
        self.remote.create_file(
            f'archiveinfo/users/{self.username}/public.asc',
            self.km.get_key('user/public')
        )


        self.local.create_folder('.archiveinfo')
        

        self.chat = self.Chat(self)

        try:
            self.aes_key = self.km.get_key(f'archives/{self.id}')
            self.salt = hash_sha256(self.id.encode() + self.aes_key)
        except FileNotFoundError:
            self.aes_key = None
            self.salt = None

    class Remote():
        def __init__(self, parent:'Drive', root_folder_id:str=None) -> None:
            self.parent = parent
            self.gd = parent.gd
            self.root_folder_id = root_folder_id

        def map_structure(self):
            def _map_structure(parent_id):
                local_structure = {}
                files = self.gd.search_file(f'parents in "{parent_id}" and trashed=false', ['id', 'name', 'mimeType'])
                
                folder_futures = []  

                with ThreadPoolExecutor() as executor:
                    for i, file in enumerate(files):
                        name = file['name']
                        file_id = file['id']
                        mime_type = file['mimeType']

                        local_structure[name] = {
                            "id": file_id,
                        }


                        if mime_type == 'application/vnd.google-apps.folder':
                            future = executor.submit(_map_structure, file_id)
                            folder_futures.append((name, future))

                    fs = json.dumps(local_structure, indent=2)
                    for name, future in folder_futures:
                        local_structure[name]['children'] = future.result()


                return local_structure
            
            self.remote_hierarchy = _map_structure(self.root_folder_id)

        def get_dir(self, path:str|list[str]) -> dict:
            if isinstance(path, str):
                path = path.split('/')
            path_len = len(path)
            level:dict = self.remote_hierarchy
            for i, sub_dir in enumerate(path):
                level = level.get(sub_dir, {})
                if not level:
                    return None
                if i >= path_len-1:
                    return level
                level = level.get('children')
            
        def is_valid_path(self, path:str|list[str]):
            return True if self.get_dir(path) else False
        
        def get_path_id(self, path:str|list[str]):
            return self.get_dir(path).get('id')
        
        def _get_parent_folder_info(self, remote_path: str|list[str]):
            remote_path = remote_path.split('/')

            if len(remote_path) > 1:
                if not (self.is_valid_path(remote_path[:-1]) and not self.is_valid_path(remote_path)):
                    return None, None, None
                
                parent_folder_path = remote_path[:-1]
                item_name = remote_path[-1]
                parent_folder_id = self.get_path_id(parent_folder_path)
            else:
                if self.is_valid_path(remote_path[0]):
                    return None, None, None
                
                item_name = remote_path[0]
                parent_folder_id = self.root_folder_id
            
            return item_name, parent_folder_id, remote_path

        def _update_hierarchy(self, remote_path_parts, new_item_name, created_item_id, is_folder=True):
            current_level = self.remote_hierarchy
            for folder in remote_path_parts[:-1]:
                current_level = current_level[folder].get('children', {})

            current_level[new_item_name] = {
                "id": created_item_id,
                "children": {} if is_folder else None
            }

        def create_folder(self, remote_path: str):
            if self.is_valid_path(remote_path):
                return
            
            new_folder_name, parent_folder_id, remote_path_parts = self._get_parent_folder_info(remote_path)

            if not new_folder_name or not parent_folder_id:
                return

            created_folder_id = self.gd.create_folder(new_folder_name, parent_folder_id)
            self._update_hierarchy(remote_path_parts, new_folder_name, created_folder_id, is_folder=True)
            # self._update_last_changed()

        def create_file(self, remote_path: str, file_data: bytes, mimetype: str = 'application/octet-stream', should_encrypt:bool=False):
            if self.is_valid_path(remote_path):
                # print(f'Error creating file ({remote_path}): File allready exists')
                return
            new_file_name, parent_folder_id, remote_path_parts = self._get_parent_folder_info(remote_path)

            if not new_file_name or not parent_folder_id:
                # print(f'Error creating file ({remote_path}): Invalid path')
                return

            if should_encrypt:
                file_data = aes.encrypt(file_data, self.parent.aes_key)

            created_file_id = self.gd.upload_file(file_data, new_file_name, parent_folder_id, mimetype)
            self._update_hierarchy(remote_path_parts, new_file_name, created_file_id, is_folder=False)
        
        def get_file_data(self, remote_path: str, is_encrypted:bool=False):
            if not self.is_valid_path(remote_path):
                raise ValueError(f"File {remote_path} does not exist")
            
            file_id = self.get_path_id(remote_path)
            file_data = self.gd.download_file(file_id)
            if is_encrypted:
                file_data = aes.decrypt(file_data, self.parent.aes_key)
            return file_data

        def delete_file(self, remote_path: str):
            if not self.is_valid_path(remote_path):
                return
            
            file_id = self.get_path_id(remote_path)
            self.gd.delete_file(file_id)
            self.get_dir(remote_path.split('/')[:-1])['children'].pop(remote_path.split('/')[-1])
            

    class Local():
        def __init__(self, parent:'Drive', local_path:str) -> None:
            self.local_path = local_path

        @property
        def all_files(self):
            """List all files, folders, and sub directories in a directory"""
            all_files = []

            def traverse_directory(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        full_path = os.path.join(root, file).removeprefix(self.local_path).replace('\\', '/').removeprefix('/')
                        all_files.append(full_path)

            # Start gathering files from the root path
            traverse_directory(self.local_path)
            return all_files

        def get_dir(self, path:str):
            return os.listdir(os.path.join(self.local_path, path))
        
        def is_path_valid(self, path:str):
            return os.path.exists(os.path.join(self.local_path, path))

        def create_folder(self, path:str):
            os.makedirs(os.path.join(self.local_path, path), exist_ok=True)
        
        def write_file(self, path:str, file_data:bytes):
            os.makedirs(os.path.join(self.local_path, os.path.dirname(path)), exist_ok=True)
            with open(os.path.join(self.local_path, path), 'wb') as f:
                f.write(file_data)
        
        def get_file_data(self, path:str):
            with open(os.path.join(self.local_path, path), 'rb') as f:
                return f.read()

        def delete_file(self, path:str):
            os.remove(os.path.join(self.local_path, path))

    class Chat():
        def __init__(self, parent:'Drive') -> None:
            self.p = parent

            if not self.p.local.is_path_valid('.archiveinfo/chat.json'):
                self.p.local.write_file('.archiveinfo/chat.json', json.dumps({}).encode())
            # self.refresh()

        def send_message(self, recipient:str, message:str):
            if not self.p.remote.is_valid_path(f'archiveinfo/users/{recipient}'):
                raise ValueError(f"User {recipient} does not exist")

            self.p.remote.create_folder(f'archiveinfo/users/{recipient}/messages')
            self.p.remote.create_folder(f'archiveinfo/users/{recipient}/messages/{self.p.username}')

            public_key = self.p.remote.get_file_data(f'archiveinfo/users/{recipient}/public.asc')

            message_id = secrets.token_urlsafe(24)
            message_data = {
                "timestamp": time.time(),
                "content": message,
                "sender": self.p.username
            }

            encrypted_data = rsa.encrypt(json.dumps(message_data).encode(), public_key)

            self.p.remote.create_file(f'archiveinfo/users/{recipient}/messages/{self.p.username}/{message_id}.acs', encrypted_data)
            messages = self.messages
            if not recipient in messages.keys():
                messages[recipient] = {}
            messages[recipient][message_id] = message_data

            self.p.local.write_file('.archiveinfo/chat.json', json.dumps(messages).encode())

        def refresh(self, force_download:bool=False):
            self.p.remote.map_structure()
            messages = self.messages


            for user in self.p.users:
                message_dir = self.p.remote.get_dir(f'archiveinfo/users/{self.p.username}/messages/{user}')
                if not message_dir:
                    continue

                if not user in messages.keys():
                    messages[user] = {}

                for message_filename in message_dir['children']:
                    message_id = message_filename.removesuffix('.acs')
                    if force_download or (message_id not in messages[user].keys()):
                        encrypted_data = self.p.remote.get_file_data(
                            f'archiveinfo/users/{self.p.username}/messages/{user}/{message_filename}'
                        )
                        message_data:dict[str, str|int] = json.loads(
                            rsa.decrypt(
                                encrypted_data,
                                self.p.km.get_key('user/private')
                            ).decode()
                        )
                        
                        if message_data['content'].startswith(KEY_DELIMITER):
                            self.p.km.set_key(f'archives/{self.p.id}', message_data['content'].removeprefix(KEY_DELIMITER).encode())
                            message_data['content'] = KEY_DELIMITER + '[REDACTED]'

                            system_message_obj = {
                                "timestamp": time.time(),
                                "content": "Archive key received.",
                                "sender": 'System'
                            }

                            messages[user][secrets.token_urlsafe(24)] = system_message_obj
                        
                        message_obj = {
                            "timestamp": message_data['timestamp'],
                            "content": message_data['content'],
                            "sender": user
                        }
                        messages[user][message_id] = message_obj


            
            self.p.local.write_file('.archiveinfo/chat.json', json.dumps(messages).encode())
            
            return messages
        
        @property
        def messages(self):
            return json.loads(self.p.local.get_file_data('.archiveinfo/chat.json'))
    
        def get_messages(self, user:str) -> dict[str, dict[str, str]]:
            messages:dict[str, dict[str, str]] = self.messages.get(user, {})
            updated_messages = {}
            for message_id, message in messages.items():

                if message['content'].startswith(KEY_DELIMITER):
                    if not message['content'].removeprefix(KEY_DELIMITER) == '[REDACTED]':
                        self.p.km.set_key(f'archives/{self.p.id}', message['content'].removeprefix(KEY_DELIMITER).encode())
                    
                    message['content'] = 'Drive Encryption Key: [REDACTED]'
                
                    if message['sender'] != self.p.username:
                        updated_messages[secrets.token_urlsafe(24)] = {
                            "timestamp": message['timestamp']+0.1,
                            "content": "Archive key received.",
                            "sender": 'System'
                        }

                updated_messages[message_id] = message

            return updated_messages


    @property
    def users(self):
        return self.remote.get_dir('archiveinfo/users')['children']

    def request_archive_key(self, user:str):
        self.chat.send_message(user, "Requesting archive key.")

    def send_archive_key(self, user:str):
        self.chat.send_message(user, KEY_DELIMITER+self.km.get_key(f'archives/{self.id}').decode())

    def hash_files(self) -> dict[str]:
        all_files = self.local.all_files
        data_hashes = {}
        for file in all_files:
            if not file.startswith('.'):
                self.local.get_file_data(file)
                data_hashes[file] = urlsafe_b64encode(hash_md5(self.local.get_file_data(file))).decode()

        return data_hashes

    def get_remote_file_hashes(self) -> dict:
        try:
            return json.loads(self.remote.get_file_data('archiveinfo/file_hashes.json', is_encrypted=True).decode())
        except ValueError:
            return {}

    def update_remote_file_hashes(self, data_hashes:dict):
        self.remote.delete_file('archiveinfo/file_hashes.json')
        self.remote.create_file('archiveinfo/file_hashes.json', json.dumps(data_hashes).encode(), should_encrypt=True)

    def _hash_filename(self, filename:str) -> str:
        return urlsafe_b64encode(hash_sha256(filename.encode()+self.salt)).decode()

    def pull(self):
        self.remote.map_structure()

        local_data_hashes = self.hash_files()
        remote_file_hashes = self.get_remote_file_hashes()

        for filename, data_hash in remote_file_hashes.items():
            if local_data_hashes.get(filename) != data_hash:
                data = self.remote.get_file_data(f'files/{self._hash_filename(filename)}', is_encrypted=True)
                self.local.write_file(filename, data)
                print(f"File pulled: {filename}")


        for filename in local_data_hashes.keys():
            if filename not in remote_file_hashes.keys():
                self.local.delete_file(filename)
                print(f"File deleted: {filename}")
    
    def push(self):
        self.remote.map_structure()

        local_data_hashes = self.hash_files()
        remote_file_hashes = self.get_remote_file_hashes()


        def sync_single_file(name:str, data_hash:str):
            if remote_file_hashes.get(name) != data_hash:
                data = self.local.get_file_data(name)
                hashed_name = self._hash_filename(name)
                self.remote.delete_file(f'files/{hashed_name}')
                self.remote.create_file(f'files/{hashed_name}', data, should_encrypt=True)
        
        with ThreadPoolExecutor() as executor:
            futures = {}
            for name, data_hash in local_data_hashes.items():
                future = executor.submit(sync_single_file, name, data_hash)
                futures[future] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()
                print(f"File pushed: {name}")
            except Exception as e:
                print(f"Error pushing file `{name}`: {e}")


        for name in remote_file_hashes:
            if not (name in local_data_hashes.keys()):
                hashed_name = self._hash_filename(name)
                self.remote.delete_file(f'files/{hashed_name}')
                print(f"Remote file deleted: {name}")

        self.update_remote_file_hashes(local_data_hashes)

    
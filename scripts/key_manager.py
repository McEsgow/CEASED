import os

class KeyManager:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def get_key(self, name):
        with open(self.folder_path + name + ".asc", "rb") as file:
            key = file.read()
        return key
        
    
    def set_key(self, name:str, key:bytes) -> None:
        os.makedirs(os.path.join(self.folder_path, os.path.dirname(name)), exist_ok=True)
        with open(self.folder_path + name + ".asc", "wb") as file:
            file.write(key)

    def delete_key(self, name):
        os.remove(self.folder_path + name + ".asc")

    @property
    def keys(self):
        _key_names = []
        for file_name in os.listdir(self.folder_path):
            if file_name.endswith(".asc"):
                _key_names.append(file_name.removesuffix('.asc'))
        return _key_names
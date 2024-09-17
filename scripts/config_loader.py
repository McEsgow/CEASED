import yaml

def load_config(path:str) -> dict:
    with open(path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def save_config(config:dict, path:str='config.yaml'):
    with open(path, 'w') as file:
        yaml.dump(config, file)

DEFAULT_CONFIG = load_config('config.yaml')
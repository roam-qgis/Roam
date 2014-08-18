import roam.yaml as yaml

settings = {}

loaded_path = ''

def load(path):
    with open(path, 'r') as f:
        global settings
        settings = yaml.load(f)
        if settings is None:
            settings = {}
        global loaded_path
        loaded_path = path

def save(path=None):
    """
    Save the settings to disk. The last path is used if no path is given.
    :param path:
    :return:
    """
    if not path:
        path = loaded_path

    with open(path, 'w') as f:
        yaml.dump(data=settings, stream=f, default_flow_style=False)

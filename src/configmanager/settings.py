import roam.yaml as yaml
settings = {}

def load(path):
    with open(path, 'r') as f:
        global settings
        settings = yaml.load(f)

def save(path):
    with open(path, 'w') as f:
        yaml.dump(data=settings, stream=f, default_flow_style=False)

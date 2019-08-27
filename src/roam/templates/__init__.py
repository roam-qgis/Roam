import os
from string import Template
from qgis.PyQt.QtCore import QUrl

from jinja2 import Environment, FileSystemLoader
path = os.path.join(os.path.dirname(__file__))

env = Environment(loader=FileSystemLoader(path))

def render_tample(name, **data):
    template = env.get_template('{}.html'.format(name))
    return template.render(**data)


def get_template(name):
    """
    Return a string Template for the given html file
    :param name: The name of the template to return
    :return: a string Template
    """
    html = os.path.join(os.path.dirname(__file__), "{}.html".format(name))
    with open(html) as f:
        return Template(f.read())


base = os.path.dirname(os.path.abspath(__file__))
baseurl = QUrl.fromLocalFile(base + '/')

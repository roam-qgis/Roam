import os
from string import Template
from PyQt4.QtCore import QUrl


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

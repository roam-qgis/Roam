import os
from types import NoneType
from string import Template

from PyQt4.QtCore import QUrl, QByteArray, QDate, QDateTime, QTime
from PyQt4.QtGui import (QDialog, QWidget, QGridLayout, QPixmap,
                         QImageReader, QDesktopServices)
from PyQt4.QtWebKit import QWebView, QWebPage

from roam import utils

import templates

images = {}
supportedformats = []

def image_handler(key, value, **kwargs):
    imageblock = '''
                    <a href="{}" class="thumbnail">
                      <img width="100%" height="100%" src="{}"\>
                    </a>'''

    imagetype = kwargs.get('imagetype', 'base64' )
    keyid = "image_{key}_{count}".format(key=key, count=len(images) + 1)
    images[keyid] = (value, imagetype)
    if imagetype == 'base64':
        src = 'data:image/png;base64,${}'.format(value.toBase64())
    else:
        src = value
    return imageblock.format(keyid, src)


def default_handler(key, value, **kwargs):
    return value


def string_handler(key, value, **kwargs):
    def parse_links():
        strings = value.split(',')
        pairs = [tuple(parts.split('|')) for parts in strings]
        handlers = []
        for pair in pairs:
            url = pair[0]
            if not any(url.startswith(proto) for proto in ['http:', 'file:']):
                continue
            try:
                name = pair[1]
            except IndexError:
                name = url
            handlers.append('<a href="{}">{}</a>'.format(url, name))
        if handlers:
            return ','.join(handlers)

    def try_image(value):
        _, extension = os.path.splitext(value)
        if extension[1:].lower() in supportedformats:
            if not os.path.exists(value):
                value = os.path.join(kwargs.get('imagepath', ''), value)
            return image_handler(key, value, imagetype='file')

        newvalue = value.encode("utf-8")
        base64 = QByteArray.fromBase64(newvalue)
        image = QPixmap()
        loaded = image.loadFromData(base64)
        if loaded:
            return image_handler(key, base64, imagetype='base64')

    global supportedformats
    if not supportedformats:
        supportedformats = [f.data() for f in QImageReader.supportedImageFormats()]

    return parse_links() or try_image(value) or value


def date_handler(key, value, **kwargs):
    return value.toString()


def none_handler(key, value, **kwargs):
    return ''


def clear_image_cache():
    images = {}

def updateTemplate(data, template, **kwargs):
    data = dict(data)
    for key, value in data.iteritems():
        handler = blocks.get(type(value), default_handler)
        block = handler(key, value, **kwargs)
        data[key] = block
    return template.safe_substitute(**data)


blocks = {QByteArray: image_handler,
          QDate: date_handler,
          QDateTime: date_handler,
          QTime: date_handler,
          str: string_handler,
          unicode: string_handler,
          NoneType: none_handler}


def showHTMLReport(title, html, data={}, parent=None):
    dialog = HtmlViewerDialog(title)
    dialog.showHTML(html, data)
    dialog.exec_()


class HtmlViewerDialog(QDialog):
    def __init__(self, title, parent=None):
        super(HtmlViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.htmlviewer = HtmlViewerWidget(self)
        self.layout().addWidget(self.htmlviewer)

    def showHTML(self, html, data):
        self.htmlviewer.showHTML(html, data)


class HtmlViewerWidget(QWidget):
    def __init__(self, parent):
        super(HtmlViewerWidget, self).__init__(parent)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.view = QWebView()
        self.view.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.layout().addWidget(self.view)

    def showHTML(self, html, data):
        if os.path.isfile(html):
            html = open(html).read()

        html = html.replace(r'\n', '<br>')
        templte = Template(html)
        html = updateTemplate(data, templte)
        self.view.setHtml(html, templates.baseurl)

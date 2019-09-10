import os

from PyQt5.QtCore import QPointF, Qt, QByteArray
from PyQt5.QtGui import QPainter, QTextDocument, QImage

import roam.api


def stamp_from_config(image, config):
    stamp = config.get('stamp', None)
    form = config.get('formwidget', None)
    feature = None
    if not stamp:
        return image

    if form:
        feature = form.to_feature()
    image = stamp_image(image, stamp['value'], stamp['position'], feature)
    return image


def stamp_image(image, expression_str, position, feature):
    painter = QPainter(image)
    data = roam.api.utils.replace_expression_placeholders(expression_str, feature)
    if not data:
        return image

    data = data.replace(r"\n", "<br>")
    style = """
    body {
        color: yellow;
    }
    """
    doc = QTextDocument()
    doc.setDefaultStyleSheet(style)
    data = "<body>{}</body>".format(data)
    doc.setHtml(data)
    point = QPointF(20, 20)

    # Wrap the text so we don't go crazy
    if doc.size().width() > 300:
        doc.setTextWidth(300)
    if position == "top-left":
        point = QPointF(20, 20)
    elif position == "top-right":
        x = image.width() - 20 - doc.size().width()
        point = QPointF(x, 20)
    elif position == "bottom-left":
        point = QPointF(20, image.height() - 20 - doc.size().height())
    elif position == "bottom-right":
        x = image.width() - 20 - doc.size().width()
        y = image.height() - 20 - doc.size().height()
        point = QPointF(x, y)
    painter.translate(point)
    doc.drawContents(painter)
    return image


def resize_image(image, size):
    """
    Resize the given image to the given size.  Doesn't resize if smaller.
    :param image: a QImage to resize.
    :param size: The QSize of the result image. Will not resize if image is smaller.
    :return: The new sized image.
    """
    if size and not size.isEmpty() and image.width() > size.width() and image.height() > size.height():
        return image.scaled(size, Qt.KeepAspectRatio)
    else:
        return image


def save_image(image, path, name):
    if isinstance(image, QByteArray):
        _image = QImage()
        _image.loadFromData(image)
        image = _image

    if not os.path.exists(path):
        os.mkdir(path)

    saved = image.save(os.path.join(path, name), "JPG")
    return saved, name
from htmlviewer import showHTMLReport

def classFactory(iface):
    from qmap import QMap
    return QMap(iface)


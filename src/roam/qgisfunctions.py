from qgis.core import QgsExpression, QGis, QgsGeometry
from roam.api import GPS, utils

capturegeometry = None

def qgsfunction(args, group, **kwargs):
    """
    Decorator function used to define a user expression function.

    Custom functions should take (values, feature, parent) as args,
    they can also shortcut naming feature and parent args by using *args
    if they are not needed in the function.

    Functions should return a value compatible with QVariant

    Eval errors can be raised using parent.setEvalErrorString()

    Functions must be unregistered when no longer needed using
    QgsExpression.unregisterFunction

    Example:
      @qgsfunction(2, 'test'):
      def add(values, feature, parent):
        pass

      Will create and register a function in QgsExpression called 'add' in the
      'test' group that takes two arguments.

      or not using feature and parent:

      @qgsfunction(2, 'test'):
      def add(values, *args):
        pass
    """
    helptemplate = ''
    class QgsExpressionFunction(QgsExpression.Function):
        def __init__(self, name, args, group, helptext=''):
            QgsExpression.Function.__init__(self, name, args, group, helptext)

        def func(self, values, feature, parent):
            pass

    def wrapper(func):
        name = kwargs.get('name', func.__name__)
        help = func.__doc__ or ''
        help = help.strip()
        if args == 0 and not name[0] == '$':
            name = '${0}'.format(name)
        func.__name__ = name
        f = QgsExpressionFunction(name, args, group, help)
        f.func = func
        register = kwargs.get('register', True)
        if register:
            QgsExpression.registerFunction(f)
        return f
    return wrapper


@qgsfunction(1, "Roam")
def roam_geomvertex(values, feature, parent):
    if capturegeometry:
        nodeindex = values[0]
        if capturegeometry.type() == QGis.Line:
            line = capturegeometry.asPolyline()
            try:
                node = line[nodeindex]
            except IndexError:
                return None
            node = QgsGeometry.fromPoint(node)
            return node
    return None

@qgsfunction(0, 'Roam')
def roamgeometry(values, feature, parent):
    return capturegeometry

@qgsfunction(0, "Roam")
def gps_z(values, feature, parent):
    return gps(values, feature, parent)

@qgsfunction(1, "Roam")
def gps(values, feature, parent):
    """
    QGIS expression function to return information about the GPS postion.
    """
    if GPS.isConnected:
        return GPS.gpsinfo(values[0])
    else:
        return None

@qgsfunction(2, "Roam")
def max_value(values, feature, parent):
    """
    Return the max value from a layer for the given column

    Usage:
    max_value('Trees', 'pk')
    """
    layer = values[0]
    try:
        layer = utils.layer_by_name(layer)
    except IndexError:
        parent.setEvalErrorString("Can't find layer {}".format(layer))
        return

    field = values[1]
    index = layer.fieldNameIndex(field)
    if index == -1:
        return None
    return layer.maximumValue(index)

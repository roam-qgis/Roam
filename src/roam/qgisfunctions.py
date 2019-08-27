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
    """
    <h3>function roam_geomvertex</h3>
    <div class="description">Returns a specific vertex from the current object being edited in Roam.</div>
    <h4>Syntax</h4>
    <div class="syntax">
    <code><span class="functionname">roam_geomvertex</span>(<span class="argument">integer</span>)</code>
    <h4>Arguments</h4>
    <div class="arguments">
    <table>
    <tr><td class="argument">integer</td><td>An integer representing the number of the vertex of interest (starting at 0).</td></tr>
    </table>
    </div>
    <h4>Examples</h4>
    <div class="examples">
    <ul>
    <li><code>roam_geomvertex( 3 )</code> &rarr; <code>Returns the 4th vertex of the current geometry object.</code></li>
    </ul>
    </div>
    """
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
        elif capturegeometry.type() == QGis.Polygon:
            try:
                node = capturegeometry.vertexAt(nodeindex)
            except IndexError:
                return None
            node = QgsGeometry.fromPoint(node)
            return node
    return None


@qgsfunction(0, 'Roam')
def roamgeometry(values, feature, parent):
    """
    <h3>function roamgeometry</h3>
    <div class="description">Returns the geometry of the current object being edited in Roam.</div>
    <h4>Syntax</h4>
    <div class="syntax">
    <code><span class="functionname">$roamgeometry</span></code>
    <h4>Examples</h4>
    <div class="examples">
    <ul>
    <li><code>geomToWKT( $roamgeometry )</code> &rarr; <code>POINT(6 50)</code></li>
    </ul>
    </div>
    """
    return capturegeometry


@qgsfunction(0, "Roam")
def gps_z(values, feature, parent):
    """
    <h3>function gps_z</h3>
    <div class="description">Returns the altitude reading from the GPS for the current point.</div>
    <h4>Syntax</h4>
    <div class="syntax">
    <code><span class="functionname">$gps_z</span></code>
    <h4>Examples</h4>
    <div class="examples">
    <ul>
    <li><code>$gps_z</code> &rarr; <code>Altitude of current point</code></li>
    </ul>
    </div>
    """
    if GPS.isConnected:
        return GPS.gpsinfo('z')
    else:
        return None

@qgsfunction(1, "Roam")
def gps(values, feature, parent):
    """
    <h3>function gps</h3>
    <div class="description">Returns various attributes from the attached GPS.</div>
    <h4>Syntax</h4>
    <div class="syntax">
    <code><span class="functionname">gps</span>(<span class="argument">string</span>)</code>
    <h4>Arguments</h4>
    <div class="arguments">
    <table>
    <tr><td class="argument">string</td><td>A string representing an attribute passed by the gps.</td></tr>
    </table>
    </div>
    <h4>Examples</h4>
    <div class="examples">
    <ul>
    <li><code>gps('x')</code> &rarr; <code>Current longitude coordinate</code></li>
    <li><code>gps('y')</code> &rarr; <code>Current latitude coordinate</code></li>
    <li><code>gps('z')</code> &rarr; <code>Current altitude</code></li>
    <li><code>gps('quality')</code> &rarr; <code>GPS fix quality<br />(0 = invalid, 1 = GPS fix, 2 = DGPS, 3 = PPS, 4 = RTK, 5 = Float RTK)</code></li>
    <li><code>gps('pdop')</code> &rarr; <code>PDOP (dilution of precision)</code></li>
    <li><code>gps('hdop')</code> &rarr; <code>Horizontal dilution of precision (HDOP)</code></li>
    <li><code>gps('vdop')</code> &rarr; <code>Vertical dilution of precision (VDOP)</code></li>
    <li><code>gps('fixType')</code> &rarr; <code>GPS fix type<br />(1 = no fix, 2 = 2D fix, 3 = 3D fix)</code></li>
    <li><code>gps('satellitesUsed')</code> &rarr; <code>Number of satellites being tracked</code></li>
    <li><code>gps('speed')</code> &rarr; <code>Speed over ground in kmph</code></li>
    <li><code>gps('direction')</code> &rarr; <code>Track angle in degrees True</code></li>
    </ul>
    </div>
    """
    if GPS.isConnected:
        return GPS.gpsinfo(values[0])
    else:
        return None


@qgsfunction(2, "Roam")
def max_value(values, feature, parent):
    """
    <h3>function max_value</h3>
    <div class="description">Returns the maximum value from a layer for a given column.</div>
    <h4>Syntax</h4>
    <div class="syntax">
    <code><span class="functionname">max_value</span>(<span class="argument">string</span>, <span class="argument">string</span>)</code>
    <h4>Arguments</h4>
    <div class="arguments">
    <table>
    <tr><td class="argument">string</td><td>A string representing a layer in the current workspace.</td></tr>
    <tr><td class="argument">string</td><td>A string representing a field within this layer.</td></tr>
    </table>
    </div>
    <h4>Examples</h4>
    <div class="examples">
    <ul>
    <li><code>max_value('Trees', 'pk')</code> &rarr; <code>Maximum primary key ('pk') value in layer 'Trees'.</code></li>
    </ul>
    </div>
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

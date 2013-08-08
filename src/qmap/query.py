import sys
import os
import itertools
from qgis.utils import iface
from qgis.core import QgsExpression, QgsFeatureRequest, QgsMapLayerRegistry
    
class Where(object):
    """
        Object to filter result set by a where expression or function
    """
    def __init__(self, layer, filterfunc):
        """
            filterfunc : A QgsExpression string, or Python callable.
        """
        self.filterfunc = filterfunc
        self.layer = layer
        
    def __call__(self, features):
        """
            Each feature is evaluated against filterfunc and if true will 
            be returned from this function.

            Features are returned using a generator to avoid memory issues.             
        """
        func = self.filterfunc
        if not hasattr(self.filterfunc, '__call__'):
            exp = QgsExpression(self.filterfunc)
            fields = self.layer.pendingFields()
            exp.prepare(fields)
            func = exp.evaluate
        # Return a generator of features that match the given where check.
        for f in features:
            if func(f):
                yield f

def query(*args, **kwargs):
    """
        Create a new query based on the given layer.
        
        A genertor is returned which will return a dict for each record.

        Example:

        >>> q = query(layer).where('ABC = 1').top(20)
        >>> for f in q():
        ...    print f

        >>> q = (query(layer).where('ABC = 1')
                             .select("ABC", 
                                    geom = lambda f: f.geometry(),
                                    buffer = lambda f: f.geometry().buffer(20))
                             .top(20)
                )
        >>> for f in q():
        ...    print f
    """
    if isinstance(args[0], basestring):
        return Query.from_layer_name(args[0], *args, **kwargs)
    else:
        return Query(*args, **kwargs)

class Query(object):
    """
        Query object used to build and execute a query against a vector layer
        
        layer: A vector layer
    """
    
    @classmethod
    def from_layer_name(cls, name, *args, **kwargs):
        args = list(args)
        # Dig into the registry to find the layer of the same name
        args[0] = QgsMapLayerRegistry.instance().mapLayersByName(name)[0]
        return cls(*args, **kwargs)
    
    MapView = iface.mapCanvas().extent
    def __init__(self, layer, DEBUG=False):
        self.layer = layer
        self.wheres = []
        self.rect = None
        self.index = None
        self.limit = None
        self.selectstatment = None
        self.DEBUG = DEBUG
    
    def _project(self, feature, *cols, **namedcols):
        """
            Project the given feature into a dict of colname : value. 
            
            If cols and namedcols are not given all attributes of the feature are
            returned in a dictionary.  Two extra columns are added, qgs_feature and 
            qgs_geometry which contain the feature and geometry instance
            respectively.
        """
        result = {}
        def _getValue(col):
            if hasattr(col, '__call__'):
                value = col(feature)
            else:
                value = feature[col]
            return value
            
        if not cols and not namedcols is None:
            fields = [field.name() for field in feature.fields()]
            result = dict(zip(fields, feature.attributes()))
            result['qgs_feature'] = feature
            result['qgs_geometry'] = feature.geometry()
        else:
            for col in cols:
                name = str(col)
                if hasattr(col, '__name__'):
                    # If the col has __name__ we will use that
                    name = col.__name__
                result[name] = _getValue(col)
                
            for name, col in namedcols.iteritems():
                result[name] = _getValue(col)
        
        return result

        
    def where(self, filterexp):
        """
            Add a filter condition to the current query.

            filterexp : A QgsExpresion, or Python callable

            Filters are added to a list and evaluated in the given order

            .where('ABC = 1').where('ADC = 2')

            will eval 'ABC = 1' first and then pass the result into the next filter
            'ADC = 2'. Only features that pass both filters will be returned in
            the result. 
        """
        self.wheres.append(Where(self.layer, filterexp))
        return self
        
    def restict_to(self, rect):
        """
            Restrict the query to featues within a given QgsRectangle
        """
        self.rect = rect
        return self
        
    def top(self, limit):
        """
            Only return the given number of features.
        """
        self.limit = limit
        return self
    
    def with_index(self, index):
        """
            Note: Not used yet
        """
        self.index = index
        return self
        
    def select(self, *cols, **namedcols):
        """
            Add a custom output mapping for final result.  
            If no select is added all attributes of the feature are
            returned in a dictionary.  Two extra columns are qgs_feature and 
            qgs_geometry are added which contain the feature and geometry instance
            respectively.

            If *cols or **namedcols contains Python callables they will be called
            when the results are returned.
        """
        self.selectstatment = (cols, namedcols)
        return self
        
    def __call__(self):
        if self.rect:
            rq = QgsFeatureRequest()
            rq.setFilterRect(self.rect)
            features = self.layer.getFeatures(rq)
        else:
            features = self.layer.getFeatures()
        
        for where in self.wheres:
            if self.DEBUG: "Has filter"
            features = where(features)

        if self.limit:
            if self.DEBUG: print "Has Limit"
            features = itertools.islice(features, 0, self.limit)
        
        if self.selectstatment:
            cols = self.selectstatment[0]
            namedcols = self.selectstatment[1]
            features = (self._project(f, *cols, **namedcols) for f in features)
        else:
            features = (self._project(f) for f in features)
        
        return features

if __name__ == "__main__":
    pass    

    
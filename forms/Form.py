class Form(object):
    """
    Represents a data collection form.  Contains links to the python module for the form.
    """

    def __init__(self, moduleName):
        self.modulename = moduleName
        
    @property
    def moduleName(self):
        return self.modulename

    @property
    def tool(self):
        return self.mapTool


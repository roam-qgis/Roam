class Form:
    """
    Represents a data collection form.  Contains links to the python module for the form.
    """

    def __init__(self, moduleName):
        self.moduleName = moduleName
        
    @property
    def moduleName(self):
        return self.modulename

    @property
    def icon(self):
        return ""

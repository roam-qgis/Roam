
__all__ = ['BaseLoader', 'SafeLoader', 'Loader']

<<<<<<< HEAD
from admin.yaml.reader import *
from admin.yaml.scanner import *
from admin.yaml.parser import *
from admin.yaml.composer import *
from admin.yaml.constructor import *
from admin.yaml.resolver import *
=======
from reader import *
from scanner import *
from parser import *
from composer import *
from constructor import *
from resolver import *
>>>>>>> dms

class BaseLoader(Reader, Scanner, Parser, Composer, BaseConstructor, BaseResolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        BaseConstructor.__init__(self)
        BaseResolver.__init__(self)

class SafeLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

class Loader(Reader, Scanner, Parser, Composer, Constructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        Constructor.__init__(self)
        Resolver.__init__(self)


class EditorWidgetException(Exception):
    pass


class RejectedException(Exception):
    WARNING = 1
    ERROR = 2

    def __init__(self, message, level=WARNING):
        super(RejectedException, self).__init__(message)
        self.message = message
        self.level = level

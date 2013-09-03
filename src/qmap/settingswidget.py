from uifiles import settings_widget, settings_base

class SettingsWidget(settings_widget, settings_base):
    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
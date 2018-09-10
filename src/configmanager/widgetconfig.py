class WidgetConfig:
    DEFAULT_SIMPLE = "simple"
    DEFAULT_LAYER_VALUE = "layer-value"

    def __init__(self, config):
        self.config = config

    @property
    def default_type(self):
        default = self.config.setdefault('default', '')
        defaulttype = self.config.get("default-type", "simple")
        if type(default) is dict or defaulttype == WidgetConfig.DEFAULT_LAYER_VALUE:
            return WidgetConfig.DEFAULT_LAYER_VALUE
        else:
            return WidgetConfig.DEFAULT_SIMPLE

    @default_type.setter
    def default_type(self, value):
        self.config['default-type'] = value

    @classmethod
    def from_config(cls, config):
        return WidgetConfig(config)

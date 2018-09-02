from PyQt4.QtCore import QDateTime, Qt


class BaseService(object):
    def __init__(self):
        import roam.utils
        self.logger = roam.utils.logger


class DataService(BaseService):
    def __init__(self, config):
        super(DataService, self).__init__()
        self.config = config

    def update_date_to_latest(self):
        self.config.set("data_save_date", QDateTime.currentDateTimeUtc().toString(Qt.ISODate))
        self.logger.info("Updated data save data to {}".format(self.config.get("data_save_data")))
        self.save()

    def save(self):
        self.config.save()

    def read(self):
        return {
            "data_save_date": self.config.get("data_save_date", None)
        }

    @property
    def last_save_date(self):
        return QDateTime.fromString(self.read()["data_save_date"], Qt.ISODate).toString()

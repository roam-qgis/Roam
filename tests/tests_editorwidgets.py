__author__ = 'nathan.woodrow'

import unittest
import qgis

from PyQt4.QtGui import QWidget, QApplication
from src.qmap.editorwidgets.core.editorwidget import EditorWidget

class EditorWidgetBaseTests(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.mywidget = QWidget()
        self.editor = EditorWidget(None, 0, self.mywidget)

    def tearDown(self):
        QApplication.exit(0)

    def test_should_return_given_widget(self):
        self.assertEqual(self.mywidget, self.editor.widget)

    def test_should_set_custom_property(self):
        config = {}
        self.editor.config = config
        widget = self.mywidget.property("EWV2Wrapper")
        print self.mywidget.property("EWV2Wrapper")
        print widget is self.editor


if __name__ == '__main__':
    unittest.main()

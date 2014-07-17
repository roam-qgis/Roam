from PyQt4.QtGui import QIcon, QPushButton, QTabWidget

from roam.api import FeatureForm
from roam.api.utils import layer_by_name, feature_by_key

import roam.project

class InspectionForm(FeatureForm):
    def __init__(self, *args, **kwargs):
        super(InspectionForm, self).__init__(*args, **kwargs)
        self.inspectionforms = []
        self.joinkey = 'insp_loc_id'
        self.mapkeycolumn = 'mapkey'
        self.inspectionformname = 'inspection_data'
        self.countcolum = 'number'

    def uisetup(self):
        """
        Called when the UI is fully constructed.  You should connect any signals here.
        """
        if self.formconfig['type'] == 'auto':
            self.AddInspectionButton = QPushButton()
            self.inspectiontabs = QTabWidget()
            self.layout().addRow(self.AddInspectionButton)
            self.layout().addRow(self.inspectiontabs)

        self.AddInspectionButton.pressed.connect(self.create_new_inspection)

    def load(self, feature, layers, values):
        """
        Called before the form is loaded. This method can be used to do pre checks and halt the loading of the form
        if needed.

        Calling self.cnacelload("Your message") will stop the opening of the form and show the message to the user.

            >>> self.cancelload("Sorry you can't load this form now")

        You may alter the values given in the values dict. It will be passed to the form after this method returns.
        """

        project = self.form.project
        self.inspectionform = project.form_by_name(self.inspectionformname)
        inspectionlayer = self.inspectionform.QGISLayer

        self.AddInspectionButton.setText("Add {}".format(self.inspectionform.label))
        self.AddInspectionButton.setIcon(QIcon(self.inspectionform.icon))
        if not self.is_capturing:
            inspections = self.find_inspections(self.feature)
            self.load_inspections(inspections, mapkeycolumn=self.mapkeycolumn)

    def find_inspections(self, feature):
        """
        Override to return the inspections for this form forms feature.
        :param feature:
        :return:
        """
        return []

    def load_inspections(self, inspections, mapkeycolumn):
        """
        Load the given inspections into the form
        :param inspections:
        :param mapkeycolumn:
        :return:
        """
        inspectionlayer = self.inspectionform.QGISLayer
        for inspection in inspections:
            mapkey = inspection['mapkey']
            inspectionfeature = feature_by_key(inspectionlayer, mapkey)
            self._add_inspectionform(inspectionfeature, editing=True, label=self.inspectionform.label)

    def create_new_inspection(self):
        """
        Create a new inspection feature and add it to the form
        :return:
        """
        feature = self.inspectionform.new_feature()
        # Give the new feature the key from the parent
        feature[self.joinkey] = self.bindingvalues[self.joinkey]
        self._add_inspectionform(feature, editing=False, label=self.inspectionform.label)

    def _add_inspectionform(self, feature, editing=False, label=''):
        """
        Add a new inspection form for the given feature.
        :param feature: The feature to bind to the form
        :param editing: True to set the form into edit mode.
                        False edit mode will add a new feature on save.
        """
        count = len(self.inspectionforms) + 1
        # Increase the inspection count for this feature
        feature[self.countcolum] = count

        # Create a new inspection form widget
        featureform = self.inspectionform.create_featureform(feature, editmode=editing)
        featureform.helprequest.connect(self.helprequest.emit)

        # Extract the values from the feature
        values = self.inspectionform.values_from_feature(feature)
        # Bind the values to the feature form
        featureform.bindvalues(values)

        # Add the tab and set the icon
        icon = QIcon(self.inspectionform.icon)
        self._add_tab(featureform, "{label} {count}".format(label=label, count=count), icon)

        # If the current count is over the max number of inspections then set the
        # button to disabled so we can't add anymore
        if count >= self.formconfig.get('maxinspections', 2):
            self.AddInspectionButton.setText("Max Inspections")
            self.AddInspectionButton.setEnabled(False)

    def _add_tab(self, widget, name, icon):
        """
        Adds a tab to the tab widget with the given widget, name, and icon.
        :param widget: The widget to add to the tab
        :param name: The name of the tab
        :param icon: The icon of the tab
        """
        index = self.inspectiontabs.addTab(widget, name)
        self.inspectionforms.append(widget)
        self.inspectiontabs.setCurrentIndex(index)
        self.inspectiontabs.setTabIcon(index, icon)

    def save(self):
        """
        Override of the save logic for the feature form

        We override the save logic because we are not saving to the property layer but to the
        InspectionLocation table
        """
        # Save all sub forms
        for subform in self.inspectionforms:
            subform.save()


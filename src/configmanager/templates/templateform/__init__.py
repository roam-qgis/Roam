"""
Template custom logic module.
"""
from roam.api import FeatureForm


class TemplateFeatureForm(FeatureForm):
    def __init__(self, *args, **kwargs):
        super(TemplateFeatureForm, self).__init__(*args, **kwargs)

    def uisetup(self):
        """
        Called when the UI is fully constructed.  You should connect any signals here.
        """
        pass

    def load(self, feature, layers, values):
        """
        Called before the form is loaded. This method can be used to do pre checks and halt the loading of the form
        if needed.

        Calling self.cnacelload("Your message") will stop the opening of the form and show the message to the user.

            >>> self.cancelload("Sorry you can't load this form now")

        You may alter the values given in the values dict. It will be passed to the form after this method returns.
        """
        pass

    def featuresaved(self, feature, values):
        """
        Called when the feature is saved in QGIS.

        The values that are taken from the form as passed in too.
        :param feature:
        :param values:
        :return:
        """
        pass

    def deletefeature(self):
        """
        Return False if you do not wish to override the delete logic.
        Raise a DeleteFeatureException if you need to raise a error else
        roam will assume everything was fine.
        :return: False if you don't need to handle custom delete logic
        """
        return False

    def featuredeleted(self, feature):
        """
        Called once the feature has been delete from the layer.
        :param feature:
        """
        pass

    def loaded(self):
        """
        Called after the form is loaded into the UI.
        """
        pass

    def accept(self):
        """
        Called before the form is accepted.  Override this and return False to cancel the accepting of the form.
        :return:
        """
        return True

def init_form(form):
    form.registerform(TemplateFeatureForm)
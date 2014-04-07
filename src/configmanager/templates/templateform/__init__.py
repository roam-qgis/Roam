"""
Template custom logic module.
"""
from roam.api import FeatureForm


class TemplateFeatureForm(FeatureForm):
    def __init__(self, *args, **kwargs):
        super(FeatureForm, self).__init__(*args, **kwargs)


def init_form(form):
    # Remove the following return in order to override the feature form logic.
    return
    form.registerform(TemplateFeatureForm)
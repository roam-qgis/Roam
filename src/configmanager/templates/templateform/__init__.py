"""
Template custom logic module.
"""
from roam.featureform import FeatureForm


class TemplateFeatureForm(FeatureForm):
    def __init__(self, *args):
        super(FeatureForm, self).__init__(*args)


def init_form(form):
    pass
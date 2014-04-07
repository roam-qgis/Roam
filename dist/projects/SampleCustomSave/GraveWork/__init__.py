"""
Template custom logic module.
"""
from roam.api import FeatureForm
from myform import MyForm

class TemplateFeatureForm(FeatureForm):
    def __init__(self, *args, **kwargs):
        super(FeatureForm, self).__init__(*args, **kwargs)


def init_form(form):
    # Remove the following return in order to override the feature form logic.
    form.registerform(MyForm)

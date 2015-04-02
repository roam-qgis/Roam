from form import Form


def init_form(form):
    # Register the class Form with the current form.
    # Form can be used to override/add logic to the form in Roam
    form.registerform(Form)
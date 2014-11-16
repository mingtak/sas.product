from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

from ..sasconfiglet import ISASConfiglet
from plone.z3cform import layout
from z3c.form import form

class SASControlPanelForm(RegistryEditForm):
    form.extends(RegistryEditForm)
    schema = ISASConfiglet

SASControlPanelView = layout.wrap_form(SASControlPanelForm, ControlPanelFormWrapper)
SASControlPanelView.label = u"SAS product datafeed setting"

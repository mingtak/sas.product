from five import grok

from z3c.form import group, field
from zope import schema
from zope.interface import invariant, Invalid
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from plone.dexterity.content import Container
from plone.directives import dexterity, form
from plone.app.textfield import RichText
from plone.namedfile.field import NamedImage, NamedFile
from plone.namedfile.field import NamedBlobImage, NamedBlobFile
from plone.namedfile.interfaces import IImageScaleTraversable

from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder


from sas.product import MessageFactory as _


class ISASConfiglet(form.Schema, IImageScaleTraversable):
    """
    Share a sale(shareasale.com) configlet control panel interface
    """

    affiliateId = schema.TextLine(
        title=_(u"Affiliate ID"),
        description=_(u"Affiliate ID, using in shareasale.com api"),
        required=False,
    )

    token = schema.TextLine(
        title=_(u"Token"),
        description=_(u"Token string, using in shareasale.com api"),
        required=False,
    )

    apiSecret = schema.TextLine(
        title=_(u"API Secret"),
        description=_(u"API Secret, using in shareasale.com api"),
        required=False,
    )

    emailList = schema.Text(
        title=_(u"Receiver Email List"),
        description=_(u"Receiver email list, per line one record"),
        required=False,
    )

    dataFeedFileList  = schema.Text(
        title=_(u"Datafeed File List"),
        description=_(u"Datafeed file list, per line one record"),
        required=False,
    )


class SASConfiglet(Container):
    grok.implements(ISASConfiglet)


class SampleView(grok.View):
    """ sample view class """

    grok.context(ISASConfiglet)
    grok.require('zope2.View')
    # grok.name('view')

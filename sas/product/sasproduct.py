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
from afiliate.product.productdata import IProductData
from plone.indexer import indexer
from sas.product import MessageFactory as _


# Interface class; used to define content-type schema.

class ISASProduct(form.Schema, IImageScaleTraversable, IProductData):
    """
    Share a sale product content type
    """
    productImage = NamedBlobImage(
        title=_(u"Product image"),
        required=False,
    )


@indexer(ISASProduct)
def imageSize_indexer(obj):
    imageSize = obj.productImage.getSize()
    return imageSize
grok.global_adapter(imageSize_indexer, name='imageSize')

@indexer(ISASProduct)
def aspectRatio_indexer(obj):
    aspect = obj.productImage.getImageSize()
    aspectRatio = float(aspect[0])/float(aspect[1])
    return aspectRatio
grok.global_adapter(aspectRatio_indexer, name='aspectRatio')


class SASProduct(Container):
    grok.implements(ISASProduct)


class SampleView(grok.View):
    """ sample view class """

    grok.context(ISASProduct)
    grok.require('zope2.View')
    grok.name('view')

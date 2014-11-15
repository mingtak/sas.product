# -*- coding: utf-8 -*-
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
from collective import dexteritytextindexer
from sas.product import MessageFactory as _


# Interface class; used to define content-type schema.

class ISASProduct(form.Schema, IImageScaleTraversable, IProductData):
    """
    Share a sale product content type

    field name : mapping to IProductData field
    ------------------------------------------
    productID : manufacturerId
    name : productName
    merchantID : ---
    merchant : advertiser
    link : buyUrl
    thumbnail : ---
    bigImage : imageUrl
    price : salePrice
    retailPrice : price
    category : advertiserCategory (結合 category, subCategory)
    subCategory : advertiserCategory (結合 category, subCategory)
    description : ---
    custom1 : ---
    custom2 : ---
    custom3 : ---
    custom4 : ---
    custom5 : ---
    lastUpdated : lastUpdated
    status : inStock
    manufacturer : manufacturer
    partnumber : ---
    merchantCategory : thirdPartyCategory (結合 merchantCategory, merchantSubcategory, merchantGroup, merchantSubgroup)
    merchantSubcategory : thirdPartyCategory (結合 merchantCategory, merchantSubcategory, merchantGroup, merchantSubgroup)
    shortDescription : content type behavior's Description
    ISBN : isbn
    UPC : upc
    SKU : sku
    crossSell : ---
    merchantGroup : thirdPartyCategory (結合 merchantCategory, merchantSubcategory, merchantGroup, merchantSubgroup)
    merchantSubgroup : thirdPartyCategory (結合 merchantCategory, merchantSubcategory, merchantGroup, merchantSubgroup)
    compatibleWith : ---
    compareTo : ---
    quantityDiscount : ---
    bestSeller : ---
    addToCartURL : ---
    reviewsRSSURL : ---
    option1 : ---
    option2 : ---
    option3 : ---
    option4 : ---
    option5 : ---
    mobileURL : ---
    mobileImage : ---
    mobileThumbnail : ---
    """
    merchantID = schema.TextLine(
        title=_(u"Merchant ID"),
        description=_(u"Merchant ID number"),
        required=False,
    )

    productImage = NamedBlobImage(
        title=_(u"Product image"),
        required=False,
    )

    partnumber = schema.TextLine(
        title=_(u"Part Number"),
        description=_(u"Manufacture's part number"),
        required=False,
    )

    # Name Conflict， mapping to Shareasale.com datafeed's 'description' field
    dexteritytextindexer.searchable('longDescription')
    longDescription = RichText(
        title=_(u"Description"),
        description=_(u"Description (HTML Rich Text)"),
        required=False,
    )

    crossSell = schema.TextLine(
        title=_(u"Cross Sell"),
        description=_(u"Comma separated list of SKU values that cross sell with the product."),
        required=False,
    )

    compatibleWith = schema.TextLine(
        title=_(u"Compatible With"),
        description=_(u"Comma separated list of compatible items in format of Manufacturer~PartNumber."),
        required=False,
    )

    compareTo = schema.TextLine(
        title=_(u"Compare To"),
        description=_(u"Comma separated list of items this product can replace in format of Manufacturer~PartNumber."),
        required=False,
    )

    quantityDiscount = schema.TextLine(
        title=_(u"Quantity Discount"),
        description=_(u"Comma separated list in the format of minQuantity~maxQuantity~itemCost. Blank Max Quantity represents a top tier."),
        required=False,
    )

    bestSeller = schema.Bool(
        title=_(u"Best Seller"),
        description=_(u"A 1 indicates a best selling product. Null values or zero are non-bestsellers."),
        required=False,
    )


@indexer(ISASProduct)
def bestSeller_indexer(obj):
    return obj.bestSeller
grok.global_adapter(bestSeller_indexer, name='bestSeller')

@indexer(ISASProduct)
def quantityDiscount_indexer(obj):
    return obj.quantityDiscount
grok.global_adapter(quantityDiscount_indexer, name='quantityDiscount')

@indexer(ISASProduct)
def merchantID_indexer(obj):
    return obj.merchantID
grok.global_adapter(merchantID_indexer, name='merchantID')

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

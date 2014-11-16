# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
import logging
from plone import api
import urllib2
from zope.component import getUtility, queryUtility
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.utils import safe_unicode
from os import popen, system
from bs4 import BeautifulSoup
from datetime import datetime
from naiveBayesClassifier import tokenizer
from naiveBayesClassifier.trainer import Trainer
from naiveBayesClassifier.classifier import Classifier
from priceasking.policy.config import TRAINING_SET as trainingSet
from priceasking.policy.config import MAIL_FROM as mailFrom
from priceasking.policy.config import MAIL_TO as mailTo
from priceasking.policy.config import SYN_SETS as synSets
from plone.namedfile import NamedBlobImage
#以下4個import，做關聯用
from zope.app.intid.interfaces import IIntIds
from z3c.relationfield import RelationValue
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
#以上4個import，做關聯用

from priceasking.policy.tfidf import run as tfIdf

logger = logging.getLogger("cj.product.productimport")


def sendErrorReport(record):
    api.portal.send_email(
        recipient=mailTo,
        sender=mailFrom,
        subject="Cj product 匯入錯誤，請處理, %s" % str(record),
        body="Cj product 匯入錯誤，請處理, %s" % str(record),
    )
    return


def transString(string):
    return string.replace(u"\u201c",'"').replace(u"\u2019","'").replace(u"\xb0","").replace(u"\xa0","")


def updateObject(item, product):
    item.salePrice=float(str(getattr(product.find("saleprice"), "string", "0.0")))
    item.price=float(str(getattr(product.find("price"), "string", "0.0")))
    item.retailPrice=float(str(getattr(product.find("retailprice"), "string", "0.0")))
    item.keywords=safe_unicode(str(transString(getattr(product.find("keywords"), "string", ""))))
    item.description=safe_unicode(transString(getattr(product.find("description"), "string", "")))
    item.buyUrl=safe_unicode(str(getattr(product.find("buyurl"), "string", "")))
    item.promotionalText=safe_unicode(str(getattr(product.find("promotionaltext"), "string", "")))
    item.reindexObject()
    return


def createObject(portal, title, subjectList, intIds,
                 advertiserObject, lastUpdated, descriptionString, imageUrl,
                 productImage, advertiser, product,):
    object = api.content.create(
        container=portal['product'],
        type='cj.product.cjproduct',
        title=safe_unicode(str(transString(title))),
        subject=subjectList,
        advertiser=[RelationValue(intIds.getId(advertiserObject))],
        programName=safe_unicode(str(getattr(product.find("programname"), "string", advertiser))),
        programUrl=safe_unicode(str(getattr(product.find("programurl"), "string", ""))),
        catalogName=safe_unicode(str(getattr(product.find("catalogName"), "string", ""))),
        lastUpdated=lastUpdated,
        productName=safe_unicode(str(transString(getattr(product.find("name"), "string", "")))),
        keywords=safe_unicode(str(transString(getattr(product.find("keywords"), "string", "")))),
        description=descriptionString,
        sku=safe_unicode(str(getattr(product.find("sku"), "string", ""))),
        manufacturer=safe_unicode(str(getattr(product.find("manufacturer"), "string", ""))),
        manufacturerId=safe_unicode(str(getattr(product.find("manufacturerid"), "string", ""))),
        upc=safe_unicode(str(getattr(product.find("upc"), "string", ""))),
        isbn=safe_unicode(str(getattr(product.find("isbn"), "string", ""))),
        currency=safe_unicode(str(getattr(product.find("currency"), "string", "USD"))),
        salePrice=float(str(getattr(product.find("saleprice"), "string", "0.0"))),
        price=float(str(getattr(product.find("price"), "string", "0.0"))),
        retailPrice=float(str(getattr(product.find("retailprice"), "string", "0.0"))),
        fromPrice=safe_unicode(str(getattr(product.find("fromprice"), "string", ""))),
        buyUrl=safe_unicode(str(getattr(product.find("buyurl"), "string", ""))),
        impressionUrl=safe_unicode(str(getattr(product.find("impressionurl"), "string", ""))),
        imageUrl=imageUrl,
        advertiserCategory=safe_unicode(str(getattr(product.find("advertisercategory"), "string", ""))),
        thirdPartyId=safe_unicode(str(getattr(product.find("thirdpartyid"), "string", ""))),
        thirdPartyCategory=safe_unicode(str(getattr(product.find("thirdpartycategory"), "string", ""))),
        publicationAuthor=safe_unicode(str(getattr(product.find("publicationauthor"), "string", ""))),
        artist=safe_unicode(str(getattr(product.find("artist"), "string", ""))),
        publicationTitle=safe_unicode(str(getattr(product.find("publicationtitle"), "string", ""))),
        publisher=safe_unicode(str(getattr(product.find("publisher"), "string", ""))),
        label=safe_unicode(str(getattr(product.find("label"), "string", ""))),
        format=safe_unicode(str(getattr(product.find("format"), "string", ""))),
        special=safe_unicode(str(getattr(product.find("special"), "string", ""))),
        gift=safe_unicode(str(getattr(product.find("gift"), "string", ""))),
        promotionalText=safe_unicode(str(getattr(product.find("promotionaltext"), "string", ""))),
        offLine=safe_unicode(str(getattr(product.find("offline"), "string", ""))),
        onLine=safe_unicode(str(getattr(product.find("online"), "string", ""))),
        inStock=safe_unicode(str(getattr(product.find("instock"), "string", ""))),
        condition=safe_unicode(str(getattr(product.find("condition"), "string", ""))),
        warranty=safe_unicode(str(getattr(product.find("warranty"), "string", ""))),
        standardShippingCost=float(str(getattr(product.find("standardshippingcost"), "string", "0.0"))),
        productImage = productImage,
        )
    for synWord in synSets[object.Subject()[0]]:
        if synWord in object.advertiserCategory.lower() or synWord in object.Title().lower():
            api.content.transition(obj=object, transition='publish')
            break
    if api.content.get_state(obj=object) == "private" and len(object.Subject()) > 1:
        if hasattr(synSets, object.Subject()[1].lower()):
            tempList = list(object.Subject())
            tempList.reverse(); tempList.pop(); tempList.reverse()
            object.setSubject(tuple(tempList))
            api.content.transition(obj=object, transition='publish')
    object.exclude_from_nav = True
    object.reindexObject()
    return


class PorductImport(BrowserView):
    prefixString = "cj.product.cjconfiglet.ICjConfiglet"
    splitString = ":::"
    tmpDir = "/tmp"

    trainer = Trainer(tokenizer)
    for record in trainingSet:
        trainer.train(record['text'], record['category'])
    classifier = Classifier(trainer.data, tokenizer)

    def __call__(self):
        request = self.request
        portal = api.portal.get()
        catalog = api.portal.get_tool(name='portal_catalog')
        intIds = getUtility(IIntIds)
        registry = getUtility(IRegistry)
        connectId = registry.get("%s.%s" % (self.prefixString, "cjDataFeedConnectId"))
        connectPassword = registry.get("%s.%s" % (self.prefixString, "cjDataFeedConnectPassword"))
        dataFeedSetting = registry.get("%s.%s" % (self.prefixString, "cjDataFeedSetting"))

        # get one record for each operator
        record = dataFeedSetting.split("\r\n")[int(request["record"])]
        advertiser, urlString = record.split(self.splitString)

        advertiserObject = catalog({"portal_type":"mingtak.advertiser.advertiser", "id":advertiser.lower()})[0].getObject()
        gzFileName = urlString.split("/")[-1]
        dataFileName = gzFileName.split(".gz")[0]
        wgetString = "http://%s:%s@%s" % (connectId, connectPassword, urlString)

        # wget, write to /tmp , read, del temp file, useing try-except.
        try:
            system("wget %s -O %s/%s" % (wgetString, self.tmpDir, gzFileName))
            system("gzip -d %s/%s" % (self.tmpDir, gzFileName))
            with open("%s/%s" % (self.tmpDir, dataFileName)) as fileName:
                doc = fileName.read()
            # delete temp file
            system("rm %s/%s" % (self.tmpDir, dataFileName))
        except:
            logger.error('ERROR!!!, %s' % advertiser)
            return

        soup = BeautifulSoup(doc, "xml")

        # in this loop, every product have same advertiser
        count, errorCount = 0, 0
        for product in soup.find_all("product"):
            title = getattr(product.find("name"), "string", None)
            sku = getattr(product.find("sku"), "string", None)
            if title is None or sku is None:
                continue
            brain = catalog({"portal_type":"cj.product.cjproduct",
                             "programName":safe_unicode(str(getattr(product.find("programname"), "string", advertiser))),
                             "title":title,
                             "sku":sku})

            if len(brain) > 0:
                updateObject(item=brain[0].getObject(), product=product)
                continue
            #Import 1000 record at one time， to avoid out of memory
#            count += 1
#            if count > 200:
#                return
            try:
                year, month, day = str(getattr(product.find("lastupdated"), "string", "")).split()[0].split("-")[0:3]
                hour, minute = str(getattr(product.find("lastupdated"), "string", "")).split()[1].split(":")[0:2]
#                descriptionString = safe_unicode(str(getattr(product.find("description"), "string", "")))
                descriptionString = safe_unicode(transString(getattr(product.find("description"), "string", "")))
                keywordString = safe_unicode(transString(getattr(product.find("keywords"), "string", "")))
                advertiserCategory = safe_unicode(transString(getattr(product.find("advertisercategory"), "string", "")))
                productClassification = self.classifier.classify('%s %s %s %s %s %s' %
                                       (advertiserCategory, keywordString, descriptionString,
                                        advertiserCategory, keywordString, advertiserCategory))
                subjectList, bayesPair = [], []
                if productClassification[0][1] > 0:
                    subjectList.append(productClassification[0][0])
                else:
                    subjectList.append("other")


                """
                for subject in productClassification:
                    # bayes value
                    if subject[1] > 0:
                        if bayesPair == []:
                            bayesPair = subject
                        elif subject[1] > bayesPair[1]:
                            bayesPair = subject
                if bayesPair == []:
                    subjectList = ["other"]
                else:
                    subjectList.append(bayesPair[0])
                """


                logger.info(productClassification)

                #get product image
                imageUrl = safe_unicode(str(getattr(product.find("imageurl"), "string", "")))
                imageFileName = safe_unicode(imageUrl.split('/')[-1])
                system("wget %s -O %s/%s" % (imageUrl, self.tmpDir, imageFileName))
                with open('%s/%s' % (self.tmpDir, imageFileName)) as tmpImage:
                    productImage = tmpImage.read()
                # delete temp file
                system("rm %s/%s" % (self.tmpDir, imageFileName))

                # tf idf
                tf_idf_result = tfIdf('%s %s %s %s %s %s' %
                                       (advertiserCategory, keywordString, descriptionString, 
                                        advertiserCategory, keywordString, advertiserCategory))

                for result in tf_idf_result[0:7]:
                    if len(result[0]) > 5:
                        subjectList.append(result[0])
            except:
                errorCount += 1
                if errorCount > 50:
                    sendErrorReport(record)
                    return
                logger.error('錯誤 1')
                continue
            try:
                lastUpdated = datetime(int(year), int(month), int(day), int(hour), int(minute))
                object = createObject(portal=portal, title=title, subjectList=subjectList, intIds=intIds,
                                      advertiserObject=advertiserObject, lastUpdated=lastUpdated,
                                      descriptionString=descriptionString, imageUrl=imageUrl,
                                      productImage=NamedBlobImage(data=productImage, filename=imageFileName),
                                      advertiser=advertiser, product=product,)
            except:
                errorCount += 1
                if errorCount > 100:
                    sendErrorReport(record)
                    return
                logger.error('error position 1')
                continue
            #目前尚未處理startDate, endDate (對應catalog index的 start, end),原因：找不到sample
            #以及，advertiser的反向關連尚未確認正確性，如不正確，要使用notify處理(見getnewrelation...)！
            logger.info("||| %s ||| %s ||| %s" %
                (count,
                 product.find("name").string,
                 product.find("buyurl").string,))
            count += 1
            if count > 100:
                return

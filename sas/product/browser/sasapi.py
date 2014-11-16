# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
import logging
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.utils import safe_unicode
from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.text import MIMEText
import urllib2
import hashlib


logger = logging.getLogger("sas.product.sasapi")


class SASAPI(BrowserView):

    registryString = "sas.product.sasconfiglet.ISASConfiglet"

    def getPage(self, url, headers):
        req = urllib2.Request(url=url, headers=headers)
        response = urllib2.urlopen(req)
        return response.read()

    def actionMerchantDataFeeds(self, xmlData):
        xmlSoup = BeautifulSoup(xmlData, 'xml')
        merchantList = xmlSoup.findAll("datafeedlistreportrecord")
        resultList = []
        for merchant in merchantList:
            try:
                lastupdated = merchant.find("lastupdated").string
                month, day, year = lastupdated.split("/")
                if (datetime.now() - datetime(int(year),int(month),int(day))).days < 7:
                    merchantId = merchant.find("merchantid").string
                    merchantName = merchant.find("merchant").string
                    status = merchant.find("applystatus").string
                    resultList.append([merchantId, merchantName, status, lastupdated])
                else:
                    continue
            except:
                continue
        return resultList


    def __call__(self):
        request = self.request
        affiliateId = api.portal.get_registry_record('%s.%s' % (self.registryString, 'affiliateId'))
        token = api.portal.get_registry_record('%s.%s' % (self.registryString, 'token'))
        apiSecret = api.portal.get_registry_record('%s.%s' % (self.registryString, 'apiSecret'))
        merchantId = getattr(request, 'merchantId', '')
        action = getattr(request, 'action', '')
        emailList = api.portal.get_registry_record('%s.%s' % (self.registryString, 'emailList'))
        utcDateString = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

        stringToHash = '%s:%s:%s:%s' % (token, utcDateString, action, apiSecret)
        sha256String = hashlib.sha256(stringToHash).hexdigest().upper()
        url = "https://shareasale.com/x.cfm?"
        headers = {'x-ShareASale-Date':utcDateString,
                   'x-ShareASale-Authentication':sha256String}


        if action == "merchantDataFeeds":
            url += "action=%s&affiliateId=%s&token=%s&XMLFormat=1" % (action, affiliateId, token)
            xmlData = self.getPage(url, headers)
            resultList = self.actionMerchantDataFeeds(xmlData)

            # create rich text
            htmlString = "<!Doctype html><html><body>"
            for result in resultList:
                htmlString += '<a href="https://jokey.shareasale.com/a-downloadproducts-bulk.cfm?merchantID=%s">%s (%s), %s</a><br>' \
                              % (result[0], result[1], result[0], result[3])
            htmlString += "</body></html>"
            mimeBody = MIMEText(htmlString, 'html', 'utf-8')

            emailList = emailList.replace('\n', ',')
            api.portal.send_email(recipient=emailList,
                                  sender='service@mingtak.com.tw',
                                  subject='ShareASale API report, date: %s' % str(datetime.now()),
                                  body='%s' % mimeBody.as_string())
        else:
            logger.warning("Warning value for 'action'.")
            return

        return

from nltk.corpus import reuters
from math import log 
from nltk import WordNetLemmatizer
wnl=WordNetLemmatizer()
from config import _Punctuation, _STOPWORD

import logging
logger = logging.getLogger("TF-IDF")

_DN = float(len(reuters.fileids()))
_RTS = {k:[wnl.lemmatize(w.lower()) for w in reuters.words(k)] for k in reuters.fileids()}

def idf(w):
    w = wnl.lemmatize(w.lower())
    return log( _DN / (1+sum([float(w in _RTS[k]) for k in _RTS.keys()])) , 2)

def tf(w,f):
    return sum([float(w == x) for x in f])/len(f)

def tf_idf(w,f):
    tfValue, idfValue = tf(w,f), idf(w)
    return tfValue*idfValue

def run(f):
    for i in _Punctuation.split():
        f = f.replace(i, " ")
    wordList = [wnl.lemmatize(word.lower()) for word in f.split()]
    _wordList = list(wordList)
    for word in wordList:
        if word in _STOPWORD:
            _wordList.remove(word)
    wordList = _wordList
    wordSet = list(set(wordList))

    word_tfidf = [(word, tf_idf(word,wordList)) for word in wordSet]
#    for word, t in sorted(word_tfidf, key = lambda x : x[1], reverse=True):
#        logger.info ("%s \t\t %f" % (word, t))
    word_tfidf = sorted(word_tfidf, key = lambda x : x[1], reverse=True)
    return word_tfidf

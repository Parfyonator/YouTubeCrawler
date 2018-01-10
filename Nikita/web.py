
# coding: utf-8

# #Start

# In[1]:

import sys
sys.path


# #Start!

# In[1]:

from collections import OrderedDict
import urllib.request
import re
# import nltk
# import time
# from pandas import*
# import numpy as np
# from nltk.stem.wordnet import WordNetLemmatizer
# wnl = WordNetLemmatizer()

from Nikita.ops import*
import pickle

def pyto(x,fname):
    with open(fname,'wb') as f:
        pickle.dump(x,f)

def pyato(x,fname):
    with open(fname,'ab') as f:
        pickle.dump(x,f)
        
def pyfrom(fname):
    with open(fname,'rb') as f:
        b=pickle.load(f)


#Read web-page to string
def gethtml(s):
    return str(urllib.request.urlopen(s).read())

def gethtml(s):
    req = urllib.request.Request(
    s, 
    data=None, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }
    
)
    resource = urllib.request.urlopen(req)
    content =  resource.read().decode(resource.headers.get_content_charset())
    return content

def gethtmld(s):
    req = urllib.request.Request(
    s, 
    data=None, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }
    
)
    resource = urllib.request.urlopen(req)
    content =  resource.read().decode(resource.headers.get_content_charset())
    return content

def gethtml(s):
    req = urllib.request.Request(
    s, 
    data=None, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }
    
)
    resource = urllib.request.urlopen(req)
    return str(resource.read())
    content =  resource.read().decode(resource.headers.get_content_charset())
    return content

import codecs

def utf(s):
    return codecs.escape_decode(s)[0].decode('UTF-8')

from bs4 import BeautifulSoup as bs

def parse(x): return bs(x, "lxml")

def fromlink(s):
    return parse(gethtml(s))

def cla(p,s,one=0):
    if not one: return p(class_=s)
    else: return p.find(class_=s)

def gettrue(p,s):
    return p.find(**{s:True})[s]

def hack():
    return globals()

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def broget(s):
    browser = webdriver.Chrome(r'X:\Nik\Programs\Anaconda3\Scripts\chromedriver.exe')
    browser.get(s)
    return browser
def lang(s): return detect(s)

def vids(p,k=5):
    l=p.find_all(class_="yt-lockup-title")
    return [x.find(href=True)['href'] for x in l[:k]]

def tits(p): 
    l=p(class_="yt-lockup-title")
    return [gettrue(x,'title') for x in l]

def tags(p):
    l=p.find_all("meta", property="og:video:tag")
    return [x["content"] for x in l]

def vote(v):
    p=parse(gethtml(v))
    l=p.find('span', class_="like-button-renderer")
    l=l('span',class_="yt-uix-button-content")
    l=[sgood(x.string) for x in l]
    #print (l)
    p,n=int(l[0]), int(l[5])
    return p/(p+n)

def avote(p):
    l=[vote(ch+x) for x in vids(p)]
    return sum(l)/len(l)

def subs(p):
    x=p.find(class_="yt-subscription-button-subscriber-count-branded-horizontal").string
    return int(sgood(x))

def about(ch):
    x=parse(gethtml(ch[:-6]+'about'))
    return cla(x,'about-description branded-page-box-padding',1).find('pre').string

def getdesc(p):
    return cla(p,'about-description branded-page-box-padding',1).find('pre').string

from langdetect import detect
def lang(s): return detect(s)
def getlang(p):
    try:
        lang=detect(utf(getdesc(p)))
    except: lang='none'
    return lang

testchan='https://www.youtube.com/user/crashcourse'

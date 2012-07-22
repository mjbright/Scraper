#!/usr/bin/python


import urllib2
import socket

import smtplib

#from BeautifulSoup import BeautifulSoup
from bs4 import BeautifulSoup

import re

import requests,sys,os
import traceback

import difflib

import datetime
from datetime import date, timedelta

# Used for stripping HTML tags:
from HTMLParser import HTMLParser

# Used for converting unicode to ASCII (??):
import unicodedata

## Import Scraper config from this Python module
from Scraper_config import Scraper_config

################################################################################

itemno=0

DEBUG_MODE=False

SAVE_ERRORS=list()

################################################################################
# Entry filtering

select_entries=None

category=None

################################################################################
# Differencing period:


HOUR=1
HOUR2=2
HOUR4=4

DAY=10
DAY2=20

WEEK=100
WEEK2=200

MONTH=1000
MONTH2=2000

period=DAY
runids = dict({
    HOUR:   'hour',
    HOUR2:  '2hour',
    HOUR4:  '4hour',
    DAY:    'day',
    DAY2:   '2day',
    WEEK:   'week',
    WEEK2:  '2week',
    MONTH:  'month',
    MONTH2: '2month',
})


################################################################################
# E-mail config:

for key in {'SEND_TO', 'SENDER_EMAIL', 'SENDER_NAME', 'SMTP_HOST', 'SEND_MAIL_MIN_BYTES',
            'SEND_MAIL_INDIVIDUAL', 'SEND_MAIL_GLOBAL',
            'SEND_ERROR_MAIL_INDIVIDUAL', 'SEND_ERROR_MAIL_GLOBAL',
            'SEND_MAIL_SUMMARY'}:
    if (not key in Scraper_config):
        print "Entry for config item '" + key + "' is missing from Scraper_config"
        exit(255)

SEND_TO = Scraper_config['SEND_TO']
SENDER_EMAIL = Scraper_config['SENDER_EMAIL']
SENDER_NAME = Scraper_config['SENDER_NAME']
SMTP_HOST = Scraper_config['SMTP_HOST']
SEND_MAIL_MIN_BYTES = Scraper_config['SEND_MAIL_MIN_BYTES']
SEND_MAIL_INDIVIDUAL = Scraper_config['SEND_MAIL_INDIVIDUAL']
SEND_MAIL_GLOBAL = Scraper_config['SEND_MAIL_GLOBAL']
SEND_ERROR_MAIL_INDIVIDUAL = Scraper_config['SEND_ERROR_MAIL_INDIVIDUAL']
SEND_ERROR_MAIL_GLOBAL = Scraper_config['SEND_ERROR_MAIL_GLOBAL']
SEND_MAIL_SUMMARY = Scraper_config['SEND_MAIL_SUMMARY']

################################################################################
# Configure User-Agents:

UAs = dict({
  'ffox5': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'
})

################################################################################
# 

HOME=os.getenv("HOME")

CACHE=HOME + "/var/SCRAPER-CACHE/"

LATEST=CACHE + "LATEST"

#From <mail_notification@saas.com> Tue Jun 12 23:00:07 CEST 2012
#DATE=datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Z %G')

FMT_DATE='%G_%B_%d'
FMT_DATEHOUR='%G_%B_%d_%Hh'
FMT_DATETIME='%G_%B_%d_%Hh%Mm%S'

DATE=datetime.datetime.now().strftime(FMT_DATE)
DATEHOUR=datetime.datetime.now().strftime(FMT_DATEHOUR)
DATETIME=datetime.datetime.now().strftime(FMT_DATETIME)

if (not os.path.exists(CACHE)):
    os.makedirs(CACHE)

################################################################################
# debug(line):

debug_flag=True
debug_flag=False
debug_readUrlList=debug_flag

def debug(line):
    if (debug_flag):
        print "DEBUG: " + line

###############################################################################
# def getTimeString(tdelta, FMT):

def getTimeString(tdelta, FMT):
    return (date.today() + tdelta).strftime(FMT)

################################################################################
# def filterSortEntries(entries, select_entries, category, runid):

def filterSortEntries(entries, select_entries, category, runid):

    #TODO: sort by category / name

    #filtered_entries = list()
    #filtered_entries = []
    filtered_entries = dict()

    DEBUG_MODE_FILTER=True
    DEBUG_MODE_FILTER=False

    for key in entries.iterkeys():
        url=key
        entry=entries[key]
        name=entry['name']

        e_runid=None
        if (entry.get('runid')):
            e_runid=entry['runid'].lower()

        e_category=None
        if (entry.get('category')):
            e_category=entry['category']

        enabled=True
        if (entry.get('enabled')):
            e_enabled=entry['enabled'].lower()

            enabled=False
            if (e_enabled == 'true'):
                 enabled=True

        if (enabled == False):
            if DEBUG_MODE_FILTER:
                print "DISABLED: " + url
            continue

        if (select_entries and url.find(select_entries) == -1):
            if DEBUG_MODE_FILTER:
                print "SELECT_ENTRIES: " + select_entries + " not found " + url
            continue

        if category:
            if (e_category == None):
                if DEBUG_MODE_FILTER:
                    print "CATEGORY: " + category + ", no category in entry " + url
                continue
            if (e_category != category):
                if DEBUG_MODE_FILTER:
                    print "CATEGORY: " + category + " != " + e_category + " category in entry " + url
                continue

        if runid:
            if (e_runid == None):
                if DEBUG_MODE_FILTER:
                    print "RUNID: " + runid + ", no runid in entry " + url
                continue
            if (e_runid != runid.lower()):
                if DEBUG_MODE_FILTER:
                    print "RUNID: " + runid + " != " + e_runid + " runid in entry " + url
                continue

        filtered_entries[url]=entry

    num_entries=len(entries)
    num_filtered_entries=len(filtered_entries)
    if (num_entries != num_filtered_entries):
        print "filterEntries returned "+str(num_filtered_entries)+" from initial " + str(num_entries) + " entries"

    return filtered_entries


################################################################################
# def hexdump(src, length=8):

def hexdump(src, start=0, count=-1, length=16):
    result = []

    digits = 4 if isinstance(src, unicode) else 2

    if (count == -1):
        count=len(src)

    if (count > len(src)):
        count=len(src)

    for i in xrange(start, start+count, length):
       s = src[i:i+length]

       hexa = b' '.join(["%0*X" % (digits, ord(x))  for x in s])
       text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.'  for x in s])

       result.append( b"%04X   %-*s   %s" % (i, length*(digits + 1), hexa, text) )

    return b'\n'.join(result)


################################################################################
# def printBuffer(label, buffer, start, count):

def printBuffer(label, buffer, start, count):
    print label + "\n" + hexdump(buffer, start, count, 16)


################################################################################
# strip_tags(html):

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        #return ''.join(self.fed)
        return self.fed

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

################################################################################
# def mkdirp(directory):

def mkdirp(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)

################################################################################
# def main_sendmail( entry, to, body, select_entries, category, period, name):

def main_sendmail( entry, to, body, select_entries, category, period, name):

    global runid

    try:
        body_bytes = len(body)
    except:
        body=""
        body_bytes = 0

    if (body_bytes < SEND_MAIL_MIN_BYTES):
        print "**** Not sending mail as num bytes="+str(body_bytes)+"< min("+str(SEND_MAIL_MIN_BYTES)+") [" + name + "]"
        return
    else:
        print "**** Sending mail as num bytes="+str(body_bytes)+">= min("+str(SEND_MAIL_MIN_BYTES)+") [" + name + "]"

    if (entry != None):
        entry_info ="<br><h3>Entry info:</h3>\n"
        for key in entry.keys():
            entry_info = entry_info + "&nbsp;&nbsp;&nbsp;&nbsp;" + key + ": " + entry.get(key) + "<br>\n"
            
        body = entry_info + "<br>" + str(body_bytes) + " body bytes<br><br>" + body

        if ('mailto' in entry):
            to = [ entry['mailto'] ]

        if ('mailto+' in entry):
            to.append( entry['mailto+'] )

    if (runid == None):
        runid=runids.get(period)

    subject='[' + runid + ']: ' + name

    if (select_entries):
        subject = subject + '<' + select_entries + '> '

    if (category):
        subject = subject + '[' + category + ']'

    subject = subject + '[' + DATEHOUR + '] '

    headers=[ 'MIME-Version: 1.0\n', 'Content-type: text/html\n' ]
    
    sendmail( to, headers, body, subject)

################################################################################
# def sendmail(to, headers, body, subject="Scraper", sender=SENDER_EMAIL, sender_name=SENDER_NAME):

def sendmail(to, headers, body, subject="Scraper", sender=SENDER_EMAIL, sender_name=SENDER_NAME):

    message = "From: " + sender_name + " <"+sender+">\n" + "To: " + ' '.join(to) + "\nSubject: " + subject + "\n"
    for header in headers:
        message = message + header

    message = message + "\n\n" + body

    body_bytes = len(body)
    by = "[ with " + str(body_bytes) + " bytes]"

    try:
       smtpObj = smtplib.SMTP(SMTP_HOST)
       smtpObj.sendmail(sender, to, message)
       print "**** Sent email to <" + ' '.join(to) + "> " + by + " " + subject

    except smtplib.SMTPException:
       print "**** Error: unable to send email" + by + " " + subject

################################################################################
# def check_file_not_gzipped(file):

import gzip

def check_file_not_gzipped(file):

    byte1 = 0
    byte2 = 0

    with open(file, 'rb') as fp:
        byte1 = ord(fp.read(1))
        byte2 = ord(fp.read(1))

    if (byte1 == 0x1f) and (byte2 == 0x8b):
        print "File '" + file + "' is gzip-compressed, uncompressing ..."
        ifp = gzip.open(file, 'rb')
        content = ifp.read()
        ifp.close()

        writeFile(file, content)

################################################################################
# get_page(url, entry, DOWNLOAD_DIR):

def get_page(url, entry, DOWNLOAD_DIR):
    op_file = DOWNLOAD_DIR + "/" + createFileName(url,entry)

    ua = UAs.get('ffox5') # TODO: browser-configurable

    try:
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', ua)]
        req = opener.open(url, timeout=30)
        #req = urllib2.urlopen(url, headers={'User-Agent' : ua})

        CHUNK = 16 * 1024
        with open(op_file, 'wb') as fp:
          while True:
            chunk = req.read(CHUNK)
            if not chunk: break

            #### # Strip chars > 128 (replace with space):
            #### for i in range(0, len(chunk)):
                #### if (ord(chunk[i]) > 128):
                    #### chunk[i]=' '
            fp.write(chunk)

    except urllib2.HTTPError as e:
        print e.fp.read()

    except urllib2.URLError as e:
        if isinstance(e.reason, socket.timeout):
            #raise MyException("Connection timedout - error: %r" % e)
            print "Connection timedout - error: %r" % e
        else:
            # reraise the original error
            # raise
            #print e.fp.read()
            print "URL Error"

    except:
        print "ERROR: in get_page:" + traceback.format_exc()
        #raise

    try:
        check_file_not_gzipped(op_file)
    except:
        print "ERROR: in get_page - failed gzip checking - " + traceback.format_exc()

    #except urllib2.Error as e:
            #print "urllib2.Error: " + e.fp.read()


################################################################################
# get_pages(entries, DOWNLOAD_DIR):

def get_pages(entries, DOWNLOAD_DIR):

    mkdirp(DOWNLOAD_DIR)

    for key in entries.iterkeys():
        url=key
        entry=entries[key]
        name=entry['name']
        print "\nGET: " + name + " => <" + url + ">"

        try:
            get_page(url, entry, DOWNLOAD_DIR)
        except:
            print "\n**** UNCAUGHT EXCEPTION on get_page(): " + traceback.format_exc()

################################################################################
# getUrlId(url):

def getUrlId(url):
    classId = url.replace("http://", "")
    classId = classId.replace("https://", "")
    classId = classId.replace("/", "_")

    return classId

################################################################################
# parse_pages(entries, DIR):

def parse_pages(entries, DIR):
    for url in entries.iterkeys():
        entry=entries[url]
        name=entry['name']
        print name + " => <" + url + ">"

        return parse_page(url, entry, DIR)

################################################################################
# def get_subtree_from_html(file, html, tag, attribute_name, attribute_value):

def get_subtree_from_html(file, html, tag, attribute_name, attribute_value):
    value = None

    entry_key = tag + "_" + attribute_name

    search = "<" + tag + " " + attribute_name + "='" + attribute_value + "'>"

    #print "Getting content from root " + entry_key + "='" + attribute_value +"'"
    print "Getting content from root " + search + " tag"

    try:
        attrs=dict()
        attrs[attribute_name]=attribute_value

        print "main = html.find_all(" + tag + ",  attrs={" + attribute_name + " : " + attribute_value + "})"
        main = html.find_all(tag, attrs)
        if (len(main) > 1):
            print "WARN: matched on more than 1 " + search + " tag"

        if (len(main) == 0):
            raise Exception("Not", " found")

        #print repr(main)

        contents=main[0].contents # Return contents of first match only

        if DEBUG_MODE:
            file = file + "." + entry_key + ".selection"
            print "Writing selection file: " + file
            writeFile(file, str(contents))

        return contents

    except:
        print "ERROR: Failed to find root at " + search + " tag"
        print traceback.format_exc()
        raise

################################################################################
# def convert_unicode_to_string(x):

#from django.utils import encoding

def convert_unicode_to_string(x):
    """
    >>> convert_unicode_to_string(u'ni\xf1era')
    'niera'
    """
    return encoding.smart_str(x, encoding='ascii', errors='ignore')

################################################################################
# def cleanText(text):

def cleanText(text):

    by=0
    line=1
    linepos=0
    #return convert_unicode_to_string(text)
    return encode2Ascii(text)

    print "cleantext("+str(len(text))+" bytes)"

    for byte in text:
        by = by + 1
        if (ord(byte) > 0xa):
            line = line + 1
            linepos=0
            continue

        linepos = linepos + 1
        if (ord(byte) > 128):
            hexstr=strformat("0x%x", ord(byte))
            print "Found big number " + hexstr +" at by " + by + " at line"+line+"@"+linepos
            byte=' '

        text = text + byte

    return text

################################################################################
# parse_page(url, entry, DIR):

def parse_page(url, entry, DIR):
    print "--->parse_page(" + url + ")"
    file = DIR + "/" + createFileName(url,entry)

    if (not os.path.exists(file)):
        print "No such dir/file as '"+file+"'"
        return

    if (not os.path.isfile(file)):
        print "No such file as '"+file+"'"
        return

    print "--->parse_file(" + file + ")"

    text = ''
    f = open(file, "rb")
    text = f.read(10000000) # 10 MBy !
    text = encode2Ascii(text)
    f.close()

    try:
        soup = BeautifulSoup(text)
        #soup = BeautifulSoup(open(file))
    except:
        print "ERROR: Failed to parse html file: " + file
        return '<br> Failed to parse ' + file + '\n' + ''.join(open(file).readlines())

    try:
        print "Original encoding = " + str(soup.originalEncoding)
    except:
        print "Original encoding = <exception>"

    body = soup.body

    if (body == None):
        return ""

    ############################################################
    ## Try first root_div_class, root_div_id entries if present:

    for key in entry:
        if (key[0:5] == "root_"):
            attr_val=entry[key]

            parts=key.split("_")
            tag=parts[1]
            attr=parts[2]
            
            try:
                print "0. TRY "+tag+" "+attr+" "+attr_val
                return get_subtree_from_html(file, body, tag, attr, attr_val)
            except:
                if (attr == "class"):
                    attr="id"

                try:
                    print "0(id). TRY "+tag+" "+attr+" "+attr_val
                    return get_subtree_from_html(file, body, tag, attr, attr_val)
                except:
                    pass

    root_div_class = None
    if ('root_div_class' in entry):
        root_div_class = entry.get('root_div_class')
        try:
            print "1. NEVER HERE ... TRY div class " + root_div_class
            return get_subtree_from_html(file, body, 'div', 'class', root_div_class)
        except:
            if (not 'root_div_id' in entry):
                print "Trying as 'root_div_id'"
                entry['root_div_id'] = root_div_class

    root_div_id = None
    if ('root_div_id' in entry):
        root_div_id = entry.get('root_div_id')

        try:
            print "2. NEVER HERE ... TRY div id " + root_div_id
            return get_subtree_from_html(file, body, 'div', 'id', root_div_id)
        except:
            pass

    ############################################################
    ## Then try root_div_class, root_div_id as 'content':

    if (not root_div_class == 'content'):
        root_div_class = 'content'
        try:
            print "3. TRY div class " + root_div_class
            return get_subtree_from_html(file, body, 'div', 'class', root_div_class)
        except:
            pass

    if (not root_div_id == 'content'):
        root_div_id='content'
        try:
            print "4. TRY div id " + root_div_id
            return get_subtree_from_html(file, body, 'div', 'id', root_div_id)
        except:
            pass

    ############################################################
    ## Then try body
    if (body):
        print "Returning body.contents"
        return body.contents

    ############################################################
    ## If all else fails return nothing!
    print "Returning NO content"
    return "";

    #print main.prettify()
    #print repr(soup.prettify())

################################################################################
# createFileName(url, entry):

def createFileName(url, entry):

    if ('filename_base' in entry):
        return entry['filename_base']

    file = url
    file = file.replace("http://", "")
    file = file.replace("https://", "")
    file = file.replace("/", "_")
    file = file.replace("?", "_")
    file = file.replace("&", "_")

    #return file[0:100]
    return file

################################################################################
# readUrlList(filename):

def readUrlList(filename):
    debug_flag=debug_readUrlList

    file_lines = readFile(filename)

    # entries=(#Entries keyed by URL)
    entries=dict()

    url_match='^https?://'
    p_url = re.compile(url_match)

    empty_match='^\s*$'
    p_empty = re.compile(empty_match)

    comment_match='^\s*#'
    p_comment = re.compile(comment_match)

    end_match='^__END__$'
    p_end = re.compile(end_match)

    ######################################################################
    ## Read all lines, adding entries to dictionary:

    entry_no=1;
    line_no=0;
    entries_started=False;

    entry=dict()
    entry['url']=None
    entry['name']='entry'+str(entry_no+1)

    for file_line in file_lines:
        line_no = line_no+1
        debug("LINE"+str(line_no)+": "+file_line)

        ########################################
        ## Skip comment lines:
        if p_comment.match(file_line):
            continue

        ########################################
        ## Empty lines delimit entries:
        if (p_empty.match(file_line) or p_end.match(file_line)):
            url = entry['url']
            #print "END OF ENTRY"

            # Ignore if empty-line before 1st entry:
            if (p_empty.match(file_line) and (not entries_started)):
                debug("IGNORING empty-lines before 1st entry")
                continue

            if p_end.match(file_line):
                break

            if (url == None):
                continue
                #print "No url defined for entry"+str(entry_no)+" ending at line "+str(line_no)
                #exit(-1)

            if (url in entries):
                print "Entry already defined for url <"+url+"> in entry"+str(entry_no)+" ending at line "+str(line_no)
                exit(-1)

            debug("Adding entry#"+str(entry_no))
            entries[url]=entry

            entry_no = entry_no+1
            entry = dict()
            entry['url']=None
            entry['name']='entry'+str(entry_no)
            continue

        ########################################
        ## Detect title lines: (No spaces before line)
        if (file_line.find(" ") != 0): 
            entry['name']=file_line
            entries_started=True;
            continue

        file_line=file_line.lstrip()
        entries_started=True;

        ########################################
        ## Detect url lines:
        if (p_url.match(file_line)):
            entry['url']=file_line
            continue

        ########################################
        ## Treat other lines:
        elements = file_line.split(":")
        name = elements[0]
        value = ":".join(elements[1:])
        entry[name]=value

    return entries


################################################################################
# readFile(filename):

def readFile(filename):
    """Read a file"""

    #with open(filename, 'r') as file:
        #lines = file.read()

    #lines = [line.strip() for line in open(filename)]
    lines = [line.rstrip() for line in open(filename)]

    #file = open(filename)
    #lines = file.readlines()
    #file.close()

    #file.close()
    return lines
        
################################################################################
# writeFile(filename):

def writeFile(filename, text):
    """Write a file"""

    try:
        with open(filename, 'wb') as file:
            file.write(text)

    except:
        print "ERROR: in writeFile("+filename+"):" + traceback.format_exc()
        raise

################################################################################
# encode2Ascii(lines):

def encode2Ascii(lines):
    ret=""

    if (str(type(lines)) == "<type 'str'>"):
        #print "STR"
        return lines

    #return lines.encode('ascii','ignore')
    text = unicodedata.normalize('NFKD', lines).encode('ascii','ignore')
    return text

    ret = ''
    for i in range(0, len(text)):
        if (i % 2) == 0:
            ret = ret + text[i]

    return ret;

    for char in lines:
        try:
            unicodedata.normalize('NFKD', char).encode('ascii','ignore')
            byte=char
            #byte = unicodedata.normalize('NFKD', char).encode('ascii','ignore')
            #byte = char.encode("ascii")
        except:
            byte = "."
        ret = ret + byte

    return ret

################################################################################
# def isAscii(mystring):

def isAscii(mystring):
    try:
        mystring.decode('ascii')
    except UnicodeDecodeError:
        return "it was not a ascii-encoded unicode string"
    else:
        return "It may have been an ascii-encoded unicode string"

################################################################################
# def diff_pages(entries, NEW_DIR, OLD_DIR):

def diff_pages(entries, NEW_DIR, OLD_DIR):

    global period

    diff_pages = ""

    for url in entries.iterkeys():
        entry=entries[url]
        name=entry['name']
        print "\nDIFF: " + name + " => <" + url + ">"

        classId=getUrlId(url)

        email_attrs=dict()
        email_attrs['select_entries']=select_entries
        email_attrs['category']=category
        email_attrs['period']=period
        email_attrs['name']=name

        page = ""
        try:
            page = diff_page(classId, url, entry, NEW_DIR, OLD_DIR, email_attrs)
        except:
            error = "ERROR: on diff_page("+url+")" + traceback.format_exc()
            print error

            full_error= "<pre>" + traceback.format_exc() + "</pre>"
            full_error_header="<b> Errors for '<u>"+name+"</u>'</b><br>"

            SAVE_ERRORS.append(full_error_header+full_error)

            if DEBUG_MODE:
                main_sendmail( entry, [ SEND_TO ], full_error, select_entries, category, period, "ERROR: " + name)

        diff_pages = diff_pages + page

    return diff_pages

################################################################################
# def substitute_local_links(d, url):

def substitute_local_links(d, url):

   file_slash=d.find('href="/')

   if (file_slash < 0):
       file_slash=d.find("href='/")

       if (file_slash < 0):
           return d

   slash=url.find("/")

   protocol = url[:slash-1]
   addr = url[slash+2:]
   slash3 = addr.find("/")

   #print "PROTOCOL="+protocol
   #print "ADDR="+addr
   #print "slash="+str(slash)
   #print d

   orig = d

   rootUrl = protocol + "://" + addr[:slash3] + "/"
   #print "rootUrl="+rootUrl

   d = d.replace("href='/", "href='"+rootUrl)
   d = d.replace('href="/', 'href="'+rootUrl)
   
   #d = d.replace("href='/", "href='"+url)
   #d = d.replace('href="/', 'href="'+url)

   #if (orig != d):
      #print "orig("+orig+")=>"+d

   return d

################################################################################
# def showlist(entries):

def showlist(entries):

    print "\nEntries: " + str(len(entries)) + " entries (filtered)"

    for key in entries.iterkeys():
        url=key
        value=entries[key]
        name=value['name']
        print name + " => <" + url + ">"

    print "\nFinished list of " + str(len(entries)) + " entries (filtered)"

    print ""

################################################################################
# def diff_page(classId, url, entry, NEW_DIR, OLD_DIR, email_attrs):

def diff_page(classId, url, entry, NEW_DIR, OLD_DIR, email_attrs):
    global itemno

    new_lines = parse_page(url, entry, NEW_DIR)
    try:
        new_lines = str(new_lines) # to UTF-8
    except:
        print "ERROR: Failed to str(NEW page)"
        raise
        #return ""

    try:
        new_lines = ''.join(new_lines)
        new_lines = new_lines.decode("utf8")
    except:
        print "ERROR: Failed to decode NEW page to 'utf8'"
        raise
        #return ""

    if ((new_lines != "") and SEND_MAIL_INDIVIDUAL):
        #body = ''.join(lines.readlines())
        #body = new_lines
        body = encode2Ascii(new_lines)

        if (('action' in entry) and (entry['action']  == "email_selection")):
            print "email_selection"

            select_entries=email_attrs['select_entries']
            category=email_attrs['category']
            period=email_attrs['period']
            name=email_attrs['name']
            main_sendmail( entry, [ SEND_TO ], body, select_entries, category, period, "SELECT: " + name)
            return ""

    try:
        old_lines = parse_page(url, entry, OLD_DIR)
    except:
        print "ERROR: Failed to parse_page(OLD page)"
        raise

    try:
        old_lines = str(old_lines) # to UTF-8
    except:
        print "ERROR: Failed to str(OLD page)"
        old_lines = ""
        #raise
        #return ""

    try:
        old_lines = ''.join(old_lines)
        old_lines = old_lines.decode("utf8")
    except:
        print "ERROR: Failed to decode OLD page to 'utf8'"
        raise
        #return ""

    
    file = NEW_DIR + "/" + createFileName(url,entry) + ".new.prediff"
    writeFile(file, encode2Ascii(new_lines))
    file = NEW_DIR + "/" + createFileName(url,entry) + ".old.prediff"
    writeFile(file, encode2Ascii(old_lines))

    print "   diff("+str(len(old_lines))+" old bytes vs. "+str(len(new_lines))+" new bytes)"
    diff_text = difflib.unified_diff(old_lines.split("\n"), new_lines.split("\n"))
    #print "   ==> "+str(len(diff))+" bytes different"

    if DEBUG_MODE:
        try:
            #### file = NEW_DIR + "/" + createFileName(url,entry) + ".diff"
            print "Writing diff file: " + file
            debug_diff_text = diff_text[:] # Deepcopy !!
            debug_diff_text = ' '.join(list(debug_diff_text))
            print "debug_diff_text len="+str(len(debug_diff_text))
            debug_diff_text = encode2Ascii(debug_diff_text)
            print "debug_diff_text len="+str(len(debug_diff_text))
            writeFile(file, debug_diff_text)
        except:
            print "ERROR: failed to write diff file: " + traceback.format_exc()

    show_new_only=True
    show_new_only=False

    div_page_diffs = "<hr>\n<div class id='"+classId+"'>\n"
    ##if (itemno > 0):
        ##item=str(itemno)
        ##div_page_diffs = div_page_diffs + "<a href='#item_"+item+"'> Prev</a>\n"
    nextno=str(itemno+2)
    div_page_diffs = div_page_diffs + "<a href='#item_"+nextno+"'>Next</a>\n"

    itemno = itemno +1
    item=str(itemno)
    div_page_diffs = div_page_diffs + "<a name='item_"+item+"'> </a>\n"
    div_page_diffs = div_page_diffs + "<h1> "+classId+" </h1>\n"

    page_diffs = ""

    for d in diff_text:
        d = d.encode("utf8", "ignore")

        # Ignore initial '+++' line:
        if (d.find("+++") == 0): 
            continue

        # Ignore position '@@' lines:
        if (d.find("@@") == 0):
            continue

        # Ignore removed lines:
        if (d.find("-") == 0): 
            continue

        d = substitute_local_links(d, url)

        # Remove leading '+' from new/modified lines:
        if (d.find("+") == 0): 
            d = d.replace("+","",1).replace("u[\"","",1)
            if (show_new_only):
                page_diffs = page_diffs + d + "\n";
                #print d
                continue
            #print d.replace("+","",1)
            #print d

        if ( not show_new_only):
            # Print new/modified/"old context" lines:
            page_diffs = page_diffs + d + "\n";
            #print d

    print "   ==> "+str(len(page_diffs))+" NEW bytes different"

    if (page_diffs == ""):
        return ""

    if DEBUG_MODE:
        try:
            file = NEW_DIR + "/" + createFileName(url,entry) + ".diff.NEW"
            print "Writing diff file: " + file
            debug_page_diffs = page_diffs[:] # Deepcopy !!
            debug_page_diffs = ' '.join(list(debug_page_diffs))
            print "debug_page_diffs len="+str(len(debug_page_diffs))
            debug_page_diffs = encode2Ascii(debug_page_diffs)
            print "debug_page_diffs len="+str(len(debug_page_diffs))
            writeFile(file, debug_page_diffs)
        except:
            print "ERROR: failed to write diff file: " + traceback.format_exc()
    page_diffs = div_page_diffs + page_diffs + "</div><<br/> <!-- "+classId+"-->\n\n"

    if ((page_diffs != "") and SEND_MAIL_INDIVIDUAL):
        #body = ''.join(lines.readlines())
        body = page_diffs

        select_entries=email_attrs['select_entries']
        category=email_attrs['category']
        period=email_attrs['period']
        name=email_attrs['name']
        main_sendmail( entry, [ SEND_TO ], body, select_entries, category, period, name)

    return page_diffs

################################################################################
# CMD-LINE ARGS:

args=sys.argv

print 80 * '_'
print "Programe started at: " + DATETIME + " as:"
print ' '.join(args)


ifile='LIST.txt'

operations=[ 'list' ]

ofile='GLOBAL_OP.html'

# Used for DIFF_page
DIR0=None
DIR1=None

runid=None

a=0
while a < (len(args)-1):
    a=a+1
    opt=args[a]

    if opt == "-e":
        a=a+1
        select_entries=args[a]
        continue

    if opt == "-c":
        a=a+1
        category=args[a]
        continue

    if opt == "-id":
        a=a+1
        runid=args[a]
        continue

    if opt == "-allid":
        a=a+1
        runid=None
        continue

    if opt == "-o":
        a=a+1
        ofile=args[a]
        continue

    if opt == "-l":
        a=a+1
        ifile=args[a]
        continue

    if opt == "-debug":
        DEBUG_MODE=True
        continue

    if opt == "-local":
        operations.append('parse_local')
        continue

    if opt == "-get":
        operations.append('get_pages')
        continue

    if opt == "-diff":
        operations.append('diff_page')
        continue

    if opt == "-DIFF":
        operations.append('DIFF_page')
        a=a+1
        DIR0=args[a]
        a=a+1
        DIR1=args[a]
        continue

    ########################################
    ## Period options:

    if opt == "-hour":
        period=HOUR
        runid=runids[period]
        continue

    if opt == "-hour2":
        period=HOUR2
        runid=runids[period]
        continue

    if opt == "-hour4":
        period=HOUR4
        runid=runids[period]
        continue

    if opt == "-day":
        period=DAY
        runid=runids[period]
        continue

    if opt == "-day2":
        period=DAY2
        runid=runids[period]
        continue

    if opt == "-week":
        period=WEEK
        runid=runids[period]
        continue

    if opt == "-week2":
        period=WEEK2
        runid=runids[period]
        continue

    if opt == "-month":
        period=MONTH
        runid=runids[period]
        continue

    if opt == "-month2":
        period=MONTH2
        runid=runids[period]
        continue

    ########################################
    ## Mail options:

    if opt == "-maili":
        SEND_MAIL_INDIVIDUAL=True
        continue

    if opt == "-nomaili":
        SEND_MAIL_INDIVIDUAL=False
        continue

    if opt == "-mailg":
        SEND_MAIL_GLOBAL=True
        continue

    if opt == "-nomailg":
        SEND_MAIL_GLOBAL=False
        continue

    print "Unknown option '"+opt+"'"
    exit(255)

################################################################################
# MAIN:

new_dir="UNKNOWN"
old_dir="UNKNOWN"

if period == HOUR:
    new_dir     = CACHE + DATEHOUR
    old_dir = CACHE + getTimeString(timedelta(hours=-1), FMT_DATEHOUR)
 
if period == HOUR2:
    new_dir     = CACHE + DATEHOUR
    old_dir = CACHE + getTimeString(timedelta(hours=-2), FMT_DATEHOUR)

if period == HOUR4:
    new_dir     = CACHE + DATEHOUR
    old_dir = CACHE + getTimeString(timedelta(hours=-4), FMT_DATEHOUR)

if period == DAY:
    new_dir     = CACHE + DATE
    old_dir = CACHE + getTimeString(timedelta(days=-1), FMT_DATE)

if period == DAY2:
    new_dir     = CACHE + DATE
    old_dir = CACHE + getTimeString(timedelta(days=-2), FMT_DATE)

if period == WEEK:
    new_dir     = CACHE + DATE
    old_dir = CACHE + getTimeString(timedelta(days=-7), FMT_DATE)

if period == WEEK2:
    new_dir     = CACHE + DATE
    old_dir = CACHE + getTimeString(timedelta(days=-14), FMT_DATE)

if period == MONTH:
    new_dir     = CACHE + DATE
    old_dir = CACHE + getTimeString(timedelta(days=-30), FMT_DATE)

if period == MONTH2:
    new_dir     = CACHE + DATE
    old_dir = CACHE + getTimeString(timedelta(days=-60), FMT_DATE)

entries = readUrlList(ifile)

entries = filterSortEntries(entries, select_entries, category, runid)

for oper in operations:

    if (oper == "list"):
        showlist(entries)

    if (oper == "get_pages"):
        if (not os.path.exists(new_dir)):
            print "os.makedirs("+new_dir+")"
            os.makedirs(new_dir)

        get_pages(entries, new_dir)

    if (oper == "parse_local"):
        parse_pages(entries, "PAGES")

    if (oper == "diff_page") or (oper == "DIFF_page"):
        dir1=new_dir
        dir0=old_dir
        if (oper == "DIFF_page"):
            dir1=DIR1
            dir0=DIR0

        diff_pages_op = diff_pages(entries, dir1, dir0)

        if (len(SAVE_ERRORS) > 0):
           SEND_MAIL_SUMMARY=True

        if (SEND_MAIL_GLOBAL):
            with open(ofile, 'w') as f:
                f.writelines(diff_pages_op)

            lines = open(ofile, 'r')
            #lines = strip_tags(lines)

            body=''
            if SEND_MAIL_SUMMARY and (len(SAVE_ERRORS) > 0):
                body = '<H1> Errors: </H1>' + ' '.join(SAVE_ERRORS) + '<br>'

            body = body + ''.join(lines.readlines())
            main_sendmail( None, [ SEND_TO ], body, select_entries, category, period, "GLOBAL")

        elif SEND_MAIL_SUMMARY and (len(SAVE_ERRORS) > 0):
            body = '<H1> Errors: </H1>' + ' '.join(SAVE_ERRORS) + '<br>'

            main_sendmail( None, [ SEND_TO ], body, select_entries, category, period, "SUMMARY")


exit(0)



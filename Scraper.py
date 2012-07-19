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

# Used for stripping HTML tags:
from HTMLParser import HTMLParser

# Used for converting unicode to ASCII (??):
import unicodedata

################################################################################

itemno=0

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
periods = dict({
    HOUR: 'HOUR',
    HOUR2:  '2HOUR',
    HOUR4:  '4HOUR',
    DAY: 'DAY',
    DAY2:  '2DAY',
    WEEK: 'WEEK',
    WEEK2:  '2WEEK',
    MONTH: 'MONTH',
    MONTH2:  '2MONTH',
})


################################################################################
# E-mail config:

SEND_TO = 'scraper@mjbright.net'

SENDER = 'scraper_cron@mjbright.net'
SENDER_NAME = 'Scraper'

SMTP_HOST='smtp.free.fr'

SEND_MAIL_MIN_BYTES=10

SEND_MAIL_INDIVIDUAL=True
SEND_MAIL_GLOBAL=False

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

#DATE=datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Z %G')
DATE=datetime.datetime.now().strftime('%G_%B_%d')
DATETIME=datetime.datetime.now().strftime('%G_%B_%d_%Hh%Mm%S')
#From <mail_notification@saas.com> Tue Jun 12 23:00:07 CEST 2012

if (not os.path.exists(CACHE)):
    os.makedirs(CACHE)

NOW=  CACHE + DATETIME

################################################################################
# debug(line):

debug_flag=True
debug_flag=False
debug_readUrlList=debug_flag

def debug(line):
    if (debug_flag):
        print "DEBUG: "+line

################################################################################
# def filterSortEntries(entries, select_entries, category):

def filterSortEntries(entries, select_entries, category):

    #TODO: sort by category / name

    #filtered_entries = list()
    #filtered_entries = []
    filtered_entries = dict()

    for key in entries.iterkeys():
        url=key
        entry=entries[key]
        name=entry['name']

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
            continue

        if (select_entries and url.find(select_entries) == -1):
            continue

        if category:
            if (e_category == None):
                continue
            if (e_category != category):
                continue

        filtered_entries[url]=entry

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

    try:
        body_bytes = len(body)
    except:
        body=""
        body_bytes = 0

    if (body_bytes < SEND_MAIL_MIN_BYTES):
        print "**** Not sending mail as num bytes="+str(body_bytes)+"< min("+str(SEND_MAIL_MIN_BYTES)+") [" + name + "]"
        
        return

    if (entry != None):
        entry_info ="<br><h3>Entry info:</h3>\n"
        for key in entry.keys():
            entry_info = entry_info + "&nbsp;&nbsp;&nbsp;&nbsp;" + key + ": " + entry.get(key) + "<br>\n"
            
        body = entry_info + "<br><br>" + body

    subject=name[:20]+'[' + periods.get(period) + ']: '

    if (select_entries):
        subject = subject + '<' + select_entries + '> '

    if (category):
        subject = subject + '[' + category + ']'

    subject = subject + '[' + DATETIME + '] ' + name

    headers=[ 'MIME-Version: 1.0\n', 'Content-type: text/html\n' ]
    
    sendmail( to, headers, body, subject)

################################################################################
# def sendmail(to, headers, body, subject="Scraper", sender=SENDER, sender_name=SENDER_NAME):

def sendmail(to, headers, body, subject="Scraper", sender=SENDER, sender_name=SENDER_NAME):

    message = "From: " + sender_name + " <"+sender+">\n" + "To: " + to[0] + "\nSubject: " + subject + "\n"
    for header in headers:
        message = message + header

    message = message + "\n\n" + body

    body_bytes = len(body)
    by = "[ with " + str(body_bytes) + " bytes]"

    try:
       smtpObj = smtplib.SMTP(SMTP_HOST)
       smtpObj.sendmail(sender, to, message)
       print "**** Successfully sent email" + by + " " + subject

    except SMTPException:
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
# get_page(url, DOWNLOAD_DIR):

def get_page(url, DOWNLOAD_DIR):
    op_file = DOWNLOAD_DIR + "/" + createFileName(url)

    #with open(op_file, 'w') as f:
    #f.write(urllib2.urlopen(url))

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
        print "ERROR: in get_page:", sys.exc_info()[0]
        #raise

    try:
        check_file_not_gzipped(op_file)
    except:
        print "ERROR: in get_page - failed gzip checking - ", sys.exc_info()[0]

    #except urllib2.Error as e:
            #print "urllib2.Error: " + e.fp.read()


################################################################################
# get_pages(entries, DOWNLOAD_DIR):

def get_pages(entries, DOWNLOAD_DIR):

    mkdirp(DOWNLOAD_DIR)

    for key in entries.iterkeys():
        url=key
        value=entries[key]
        name=value['name']
        print "\nGET: " + name + " => <" + url + ">"

        try:
            get_page(url, DOWNLOAD_DIR)
        except:
            print "\n**** UNCAUGHT EXCEPTION on get_page(): " + sys.exc_info()[0] + "\n"

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
# parse_page(url, entry, DIR):

def parse_page(url, entry, DIR):
    print "--->parse_page(" + url + ")"
    file = DIR + "/" + createFileName(url)

    if (not os.path.exists(file)):
        print "No such dir/file as '"+file+"'"
        return

    if (not os.path.isfile(file)):
        print "No such file as '"+file+"'"
        return

    print "--->parse_file(" + file + ")"

    try:
        soup = BeautifulSoup(open(file))
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

    root_div_class = None
    if ('root_div_class' in entry):
        root_div_class = entry.get('root_div_class')
        print "Getting content from root_div_class='" + root_div_class + "'"

        try:
            main = body.find_all("div", attrs={'class' : root_div_class})
            contents=main[0].contents # Return contents of first match only

            writeFile(file + ".div_class.selection", str(contents))
            return contents
        except:
            print "ERROR: Failed to find div_class <" + root_div_class + ">"
            if (not 'root_div_id' in entry):
                print "Trying as 'root_div_id'"
                entry['root_div_id'] = root_div_class
            #raise

    root_div_id = None
    if ('root_div_id' in entry):
        root_div_id = entry.get('root_div_id')
        print "Getting content from root_div_id='" + root_div_id + "'"

        try:
            main = body.find_all("div", attrs={'id' : root_div_id})
            contents=main[0].contents # Return contents of first match only

            writeFile(file + ".div_id.selection", str(contents))
            return contents
        except:
            print "ERROR: Failed to find div_id <" + root_div_id + ">"
            #raise

    ############################################################
    ## Then try root_div_class, root_div_id as 'content':

    if ((not root_div_class == 'content') and body.find_all("div", attrs={'class' : 'content'})):
        print "Trying content from root_div_class='content'"
        root_div_class='content'
        try:
            main = body.find_all("div", attrs={'class' : root_div_class})
            contents=main[0].contents # Return contents of first match only

            writeFile(file + ".div_class.selection", str(contents))
            return contents
        except:
            print "ERROR: Failed to find div_class <" + root_div_class + ">"
            #raise


    if ((not root_div_id == 'content') and body.find_all("div", attrs={'id' : 'content'})):
        print "Trying content from root_div_id='content'"
        root_div_id='content'
        try:
            main = body.find_all("div", attrs={'id' : root_div_id})
            contents=main[0].contents # Return contents of first match only

            writeFile(file + ".div_id.selection", str(contents))
            return contents
        except:
            print "ERROR: Failed to find div_id <" + root_div_id + ">"
            #raise

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
# createFileName(url):

def createFileName(url):
    file = url
    file = file.replace("http://", "")
    file = file.replace("https://", "")
    file = file.replace("/", "_")
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
        with open(filename, 'w') as file:
            file.write(text)

    except:
        print "ERROR: in writeFile("+filename+"):", sys.exc_info()[0]
        raise

################################################################################
# encode2Ascii(lines):

def encode2Ascii(lines):
    ret=""

    if (str(type(lines)) == "<type 'str'>"):
        print "STR"
        return lines

    return lines.encode('ascii','ignore')
    return unicodedata.normalize('NFKD', lines).encode('ascii','ignore')

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

        page = ""
        try:
            page = diff_page(classId, url, entry, NEW_DIR, OLD_DIR)
        except:
            #error = "ERROR: on diff_page("+url+")" + str(sys.exc_info()[0])
            error = "ERROR: on diff_page("+url+")" + traceback.format_exc()
            #print "ERROR: on diff_page("+url+")", sys.exc_info()[0]
            print error

            full_error= "<pre>" + traceback.format_exc() + "</pre>"

            main_sendmail( entry, [ SEND_TO ], full_error, select_entries, category, period, "ERROR: " + name)

        if ((page != "") and SEND_MAIL_INDIVIDUAL):
            #body = ''.join(lines.readlines())
            body = page

            main_sendmail( entry, [ SEND_TO ], body, select_entries, category, period, name)

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

    print "\nEntries: " + str(len(entries)) + " entries"

    for key in entries.iterkeys():
        url=key
        value=entries[key]
        name=value['name']
        print name + " => <" + url + ">"

    print ""

################################################################################
# def diff_page(classId, url, entry, NEW_DIR, OLD_DIR):

def diff_page(classId, url, entry, NEW_DIR, OLD_DIR):
    global itemno

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

    print "   diff("+str(len(old_lines))+" old bytes vs. "+str(len(new_lines))+" new bytes)"
    diff = difflib.unified_diff(old_lines.split("\n"), new_lines.split("\n"))
    #print "   ==> "+str(len(diff))+" bytes different"

    show_new_only=True
    show_new_only=False

    div_page_diffs = "<hr>\n<div class id='"+classId+"'>\n"
    if (itemno > 0):
        item=str(itemno)
        div_page_diffs = div_page_diffs + "<a href='#item_"+item+"'> Prev</a>\n"
    nextno=str(itemno+2)
    div_page_diffs = div_page_diffs + "<a href='#item_"+nextno+"'>Next</a>\n"

    itemno = itemno +1
    item=str(itemno)
    div_page_diffs = div_page_diffs + "<a name='item_"+item+"'> </a>\n"
    div_page_diffs = div_page_diffs + "<h1> "+classId+" </h1>\n"

    page_diffs = ""

    for d in diff:
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

    page_diffs = div_page_diffs + page_diffs + "</div><<br/> <!-- "+classId+"-->\n\n"

    return page_diffs

################################################################################
# CMD-LINE ARGS:

args=sys.argv

ifile='LIST.txt'

operations=[ 'list' ]

ofile='GLOBAL_OP.html'

# Used for DIFF_page
DIR0=None
DIR1=None

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

    if opt == "-o":
        a=a+1
        ofile=args[a]
        continue

    if opt == "-l":
        a=a+1
        ifile=args[a]
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
        continue

    if opt == "-hour2":
        period=HOUR2
        continue

    if opt == "-hour4":
        period=HOUR4
        continue

    if opt == "-day":
        period=DAY
        continue

    if opt == "-day2":
        period=DAY2
        continue

    if opt == "-week":
        period=WEEK
        continue

    if opt == "-week2":
        period=WEEK2
        continue

    if opt == "-month":
        period=MONTH
        continue

    if opt == "-month2":
        period=MONTH2
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

dirlink="UNKNOWN"
dirlink_old="UNKNOWN"

if period == HOUR:
    NOW        =  CACHE + DATETIME
    dirlink    = CACHE + "HOUR"
    dirlink_old= CACHE + "HOUR_1"

if period == HOUR2:
    NOW        =  CACHE + DATETIME
    dirlink    = CACHE + "HOUR"
    dirlink_old= CACHE + "HOUR_2"

if period == HOUR4:
    NOW        =  CACHE + DATETIME
    dirlink    = CACHE + "HOUR"
    dirlink_old= CACHE + "HOUR_4"

if period == DAY:
    NOW        =  CACHE + DATE
    dirlink    = CACHE + "TODAY"
    dirlink_old= CACHE + "TODAY_1"

if period == DAY2:
    NOW        =  CACHE + DATE
    dirlink    = CACHE + "TODAY"
    dirlink_old= CACHE + "TODAY_2"

if period == WEEK:
    NOW        =  CACHE + DATE
    dirlink    = CACHE + "WEEK"
    dirlink_old= CACHE + "WEEK_1"

if period == WEEK2:
    NOW        =  CACHE + DATE
    dirlink    = CACHE + "WEEK"
    dirlink_old= CACHE + "WEEK_2"

if period == MONTH:
    NOW        =  CACHE + DATE
    dirlink    = CACHE + "MONTH"
    dirlink_old= CACHE + "MONTH_1"

if period == MONTH2:
    NOW        =  CACHE + DATE
    dirlink    = CACHE + "MONTH"
    dirlink_old= CACHE + "MONTH_2"

entries = readUrlList(ifile)

num_entries=len(entries)
entries = filterSortEntries(entries, select_entries, category)
num_entries_2=len(entries)

#print "num_entries="+str(num_entries)
#print "num_entries_2="+str(num_entries_2)

for oper in operations:

    if (oper == "list"):
        showlist(entries)

    if (oper == "get_pages"):
        if (not os.path.exists(NOW)):
            print "os.makedirs("+NOW+")"
            os.makedirs(NOW)

        if (os.path.islink(dirlink_old)):
            print "os.remove("+dirlink_old+")"
            os.remove(dirlink_old)

        if (os.path.islink(dirlink)):
            #os.rmdir(dirlink)
            print "os.rename("+dirlink+", "+dirlink_old+")"
            os.rename(dirlink, dirlink_old)

        print "os.symlink("+NOW+", "+dirlink+")"
        os.symlink(NOW, dirlink)
    
        get_pages(entries, dirlink)

    if (oper == "parse_local"):
        parse_pages(entries, "PAGES")

    if (oper == "diff_page") or (oper == "DIFF_page"):
        dir1=dirlink
        dir0=dirlink_old
        if (oper == "DIFF_page"):
            dir1=DIR1
            dir0=DIR0

        diff_pages_op = diff_pages(entries, dir1, dir0)

        if (SEND_MAIL_GLOBAL):
            with open(ofile, 'w') as f:
                f.writelines(diff_pages_op)

            lines = open(ofile, 'r')
            #lines = strip_tags(lines)

            body = ''.join(lines.readlines())
            main_sendmail( None, [ SEND_TO ], body, select_entries, category, period, "GLOBAL")

exit(0)



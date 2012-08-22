#!/usr/bin/python

import re
import requests,sys,os
import traceback

from datetime import date, timedelta

# Used for converting unicode to ASCII (??):
import unicodedata

## Import Scraper config from this Python module
from Scraper_config import Scraper_config

from Entry import Entry

import Utils as u

DATE=u.DATE
DATETIME=u.DATETIME
DATEHOUR=u.DATEHOUR
FMT_DATE=u.FMT_DATE
FMT_DATETIME=u.FMT_DATETIME
FMT_DATEHOUR=u.FMT_DATEHOUR

################################################################################

DEBUG_MODE=False
DEBUG_INFO=False
TEST_MODE=False

SAVE_ERRORS=list()

################################################################################
# Entry filtering

select_entries=None
select_urls=None

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

EMAIL_CONFIG_KEYS=list({
    'SEND_TO', 'SENDER_EMAIL', 'SENDER_NAME', 'SMTP_HOST', 'SEND_MAIL_MIN_BYTES',
    'SEND_MAIL_INDIVIDUAL', 'SEND_MAIL_GLOBAL',
    'SEND_ERROR_MAIL_INDIVIDUAL', 'SEND_ERROR_MAIL_GLOBAL',
    'SEND_MAIL_SUMMARY'
    })

for key in EMAIL_CONFIG_KEYS:
    if (not key in Scraper_config):
        print "Entry for config item '" + key + "' is missing from Scraper_config"
        exit(255)

u.SENDER_EMAIL = Scraper_config['SENDER_EMAIL']
u.SENDER_NAME = Scraper_config['SENDER_NAME']
u.SEND_MAIL_MIN_BYTES = Scraper_config['SEND_MAIL_MIN_BYTES']
u.SMTP_HOST = Scraper_config['SMTP_HOST']

SEND_TO = Scraper_config['SEND_TO']
SEND_MAIL_INDIVIDUAL = Scraper_config['SEND_MAIL_INDIVIDUAL']
SEND_MAIL_GLOBAL = Scraper_config['SEND_MAIL_GLOBAL']
SEND_ERROR_MAIL_INDIVIDUAL = Scraper_config['SEND_ERROR_MAIL_INDIVIDUAL']
SEND_ERROR_MAIL_GLOBAL = Scraper_config['SEND_ERROR_MAIL_GLOBAL']
SEND_MAIL_SUMMARY = Scraper_config['SEND_MAIL_SUMMARY']

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
# def filterSortEntries(entries, select_entries, select_urls, category, runid):

def filterSortEntries(entries, select_entries, select_urls, category, runid):

    #TODO: sort by category / name

    filtered_entries = dict()

    DEBUG_MODE_FILTER=True
    DEBUG_MODE_FILTER=False

    #print "runid="+runid
    for key in entries.iterkeys():
        url=key
        entry=entries[key]
        name=entry.name

        e_runid=None
        if (entry.fields.get('runid')):
            e_runid=entry.fields.get('runid').lower()

        e_category=None
        if (entry.fields.get('category')):
            e_category=entry.fields.get('category')

        enabled=True
        if (entry.fields.get('enabled')):
            e_enabled=entry.fields.get('enabled').lower()

            enabled=False
            if (e_enabled == 'true'):
                 enabled=True

        if (enabled == False):
            if DEBUG_MODE_FILTER:
                print "DISABLED: " + url
            continue

        if (select_entries and name.lower().find(select_entries.lower()) == -1):
            if DEBUG_MODE_FILTER:
                print "SELECT_ENTRIES: " + select_entries + " not found " + url
            continue

        if (select_urls and url.lower().find(select_urls.lower()) == -1):
            if DEBUG_MODE_FILTER:
                print "SELECT_URLS: " + select_urls + " not found " + url
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
# def mkdirp(directory):

def mkdirp(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)

################################################################################
# get_pages(entries, DOWNLOAD_DIR):

def get_pages(entries, DOWNLOAD_DIR):

    mkdirp(DOWNLOAD_DIR)

    for key in entries.iterkeys():
        url=key
        entry=entries[key]
        name=entry.name
        print "\nGET: " + name + " => <" + url + ">"

        try:
            entry.get_page(DOWNLOAD_DIR)
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
        name=entry.name
        print name + " => <" + url + ">"

        return entry.parse_page(DIR)

################################################################################
# def cleanText(text):

def cleanText(text):

    by=0
    line=1
    linepos=0
    return u.encode2Ascii(text)

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
# readUrlList(filename):

def readUrlList(filename):
    debug_flag=debug_readUrlList

    file_lines = u.readFile(filename)

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

    entry = Entry()
    entry.url=None
    entry.name='entry'+str(entry_no)+'_line'+str(line_no)
    entry.fields['name']='entry'+str(entry_no)+'_line'+str(line_no)
    entry.debug=DEBUG_MODE
    entry.dinfo=DEBUG_INFO

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
            url = entry.url
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

            if (entry.get('debug') and ((entry.get('debug').lower == "true") or (entry.get('debug').lower == "enabled"))):
                entry.debug=True

            if (entry.get('dinfo') and ((entry.get('dinfo').lower == "true") or (entry.get('dinfo').lower == "enabled"))):
                entry.dinfo=True

            debug("Adding entry#"+str(entry_no))
            entries[url]=entry
            entry_no = entry_no+1

            entry = Entry()
            entry.url=None
            entry.debug=DEBUG_MODE
            entry.dinfo=DEBUG_INFO
            entry.name='entry'+str(entry_no)+'_line'+str(line_no)
            entry.fields['name']='entry'+str(entry_no)+'_line'+str(line_no)
            continue

        ########################################
        ## Detect title lines: (No spaces before line)
        if (file_line.find(" ") != 0): 
            entry.fields['name']=file_line
            entry.name=file_line
            entries_started=True;
            continue

        file_line=file_line.lstrip()
        entries_started=True;

        ########################################
        ## Detect url lines:
        if (p_url.match(file_line)):
            entry.url=file_line
            continue

        ########################################
        ## Treat other lines:
        elements = file_line.split(":")
        name = elements[0]
        value = ":".join(elements[1:])
        entry.fields[name]=value

    return entries


################################################################################
# def diff_pages(entries, NEW_DIR, OLD_DIR):

def diff_pages(entries, NEW_DIR, OLD_DIR):

    global period

    diff_pages = ""

    for url in entries.iterkeys():
        entry=entries[url]
        name=entry.name
        print 40 * '_'
        print "\nDIFF: " + name + " => <" + url + ">"

        classId=getUrlId(url)

        email_attrs=dict()
        email_attrs['select_entries']=select_entries
        email_attrs['category']=category
        email_attrs['period']=period
        email_attrs['name']=name
        email_attrs['SEND_TO']=SEND_TO
        email_attrs['SEND_MAIL_INDIVIDUAL']=SEND_MAIL_INDIVIDUAL

        page = ""
        try:
            page = entry.diff_page(classId, NEW_DIR, OLD_DIR, email_attrs)
        except:
            error = "ERROR: on diff_page("+url+")" + traceback.format_exc()
            print error

            full_error= "<pre>" + traceback.format_exc() + "</pre>"
            full_error_header="<b> Errors for '<u>"+name+"</u>'</b><br>"

            SAVE_ERRORS.append(full_error_header+full_error)

            if entry.debug:
                u.sendmail( entry, [ SEND_TO ], full_error, select_entries, category, period, "ERROR: " + name, runid)

        diff_pages = diff_pages + page

    return diff_pages

################################################################################
# def showlist(entries):

def showlist(entries):

    print "\nEntries: " + str(len(entries)) + " entries (filtered)"

    for key in entries.iterkeys():
        url=key
        value=entries[key]
        name=value.name
        print name + " => <" + url + ">"

    print "\nFinished list of " + str(len(entries)) + " entries (filtered)"

    print ""

################################################################################
# CMD-LINE ARGS:

args=sys.argv

print 80 * '_'
print "Programe started at: " + u.DATETIME + " as:"
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

    if opt == "-u":
        a=a+1
        select_urls=args[a]
        continue

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

    if opt == "-parser":
        a=a+1
        Entry.Parser = args[a]
        continue

    if opt == "-dinfo":
        print "Setting DEBUG_INFO to True"
        DEBUG_INFO=True
        continue

    if opt == "-debug":
        print "Setting DEBUG_MODE to True"
        DEBUG_MODE=True
        continue

    if opt == "-test":
        print "Setting TEST_MODE to True"
        TEST_MODE=True
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

    if opt == "-nomail":
        SEND_MAIL_INDIVIDUAL=False
        SEND_MAIL_GLOBAL=False
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

HOME=os.getenv("HOME")

Entry.globalRunID=runid

CACHE=HOME + "/var/SCRAPER-CACHE/"
if TEST_MODE:
    CACHE=HOME + "/var/SCRAPER-CACHE-TEST/"

LATEST=CACHE + "LATEST"

if (not os.path.exists(CACHE)):
    os.makedirs(CACHE)

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

entries = filterSortEntries(entries, select_entries, select_urls, category, runid)

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
            u.sendmail( None, [ SEND_TO], body, select_entries, category, period, "GLOBAL", runid)

        elif SEND_MAIL_SUMMARY and (len(SAVE_ERRORS) > 0):
            body = '<H1> Errors: </H1>' + ' '.join(SAVE_ERRORS) + '<br>'

            u.sendmail( None, [ SEND_TO], body, select_entries, category, period, "SUMMARY", runid)


exit(0)


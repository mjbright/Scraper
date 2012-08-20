
import unicodedata

import socket
import smtplib

import traceback

import datetime
from datetime import date

SENDER_EMAIL=None
SENDER_NAME=None
SEND_MAIL_MIN_BYTES=None

TEST_MODE=False

FMT_DATE='%G_%B_%d'
FMT_DATEHOUR='%G_%B_%d_%Hh'
FMT_DATETIME='%G_%B_%d_%Hh%Mm%S'

DATE=datetime.datetime.now().strftime(FMT_DATE)
DATEHOUR=datetime.datetime.now().strftime(FMT_DATEHOUR)
DATETIME=datetime.datetime.now().strftime(FMT_DATETIME)

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
# readFile(filename):

def readFile(filename):
    """Read a file"""

    lines = [line.rstrip() for line in open(filename)]

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
# def isAscii(mystring):

def isAscii(mystring):
    try:
        mystring.decode('ascii')
    except UnicodeDecodeError:
        return "it was not a ascii-encoded unicode string"
    else:
        return "It may have been an ascii-encoded unicode string"

################################################################################
# def sendmail( entry, to, body, select_entries, category, period, name, runid):

def sendmail( entry, to, body, select_entries, category, period, name, runid):

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
        for key in entry.fields.keys():
            entry_info = entry_info + "&nbsp;&nbsp;&nbsp;&nbsp;" + key + ": " + entry.fields.get(key) + "<br>\n"
            
        body = entry_info + "<br>" + str(body_bytes) + " body bytes<br><br>" + body

        if ('mailto' in entry.fields):
            to = [ entry.fields.mailto ]

        if ('mailto+' in entry.fields):
            to.append( entry.fields.mailto )

    if (runid == None):
        print "ERROR: in sendmail() runid is unset: " + traceback.format_exc()
        #runid=runids.get(period)
        runid="__NO_RUNID__"

    subject='[' + runid + ']: ' + name
    if TEST_MODE:
        subject='[TEST_MODE]: ' + subject

    if (select_entries):
        subject = subject + '<' + select_entries + '> '

    if (category):
        subject = subject + '[' + category + ']'

    subject = subject + '[' + DATEHOUR + '] '

    headers=[ 'MIME-Version: 1.0\n', 'Content-type: text/html\n' ]
    
    _sendmail( to, headers, body, subject)

################################################################################
# def _sendmail(to, headers, body, subject="Scraper", sender=SENDER_EMAIL, sender_name=SENDER_NAME):

#def _sendmail(to, headers, body, subject="Scraper", sender=SENDER_EMAIL, sender_name=SENDER_NAME):
def _sendmail(to, headers, body, subject="Scraper"):

    sender=SENDER_EMAIL
    sender_name=SENDER_NAME

    #print "SENDER_EMAIL=" + SENDER_EMAIL
    #print "sender="+sender
    #print "sender_name="+sender_name

    message = "From: " + sender_name
    message = message + " <"+sender+">\n" + "To: "
    message = message + ' '.join(to)
    message = message + "\nSubject: " + subject + "\n"

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



import unicodedata

import socket
import smtplib

NLTK=False
try:
    import nltk
    NLTK=True
except ImportError:
    print("No nltk module available")

import traceback

import datetime
from datetime import date

SENDER_EMAIL=None
SENDER_NAME=None
SEND_MAIL_MIN_BYTES=None
SEND_MAIL_MIN_LINES=None

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
        #print("STR")
        return lines

    #    return lines
    try:
        return lines.encode('ascii','ignore')
    except:
         return lines

    try:
        text = unicodedata.normalize('NFKD', lines).encode('ascii','ignore')
    except:
        text = unicodedata.normalize('NFKD', lines).encode('utf-8','ignore')

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
        print("ERROR: in writeFile("+filename+"):" + traceback.format_exc())
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
    print(f"sendmail( {entry}, {to}, {body}, {select_entries}, {category}, {period}, {name}, {runid})")

    print(f"type(body)={type(body)}") # <class 'bytes'>
    if str(type(body)) == "<class 'bytes'>":
        body=body.decode('ascii','ignore')
        print(f"AFTER decode('ascii'): type(body)={type(body)}")

    try:
        body=''.join(body)
        print("len")
        num_body_bytes = len(str(body))
        print("count")
        num_body_lines = body.count('\n')
    except:
        print("join failed")
        num_body_bytes=0
        num_body_lines=0

    try:
        print("-----------------------------------------------------------------------------------")
        #print(f"str(body)={str(body)}")
        #print("-----------------------------------------------------------------------------------")
        print(f"num_body_bytes={num_body_bytes}")
        print(f"num_body_lines={num_body_lines}")
        print("body_info")
        body_info = "HTML TEXT: "
        print("body_info+")
        body_info = body_info + \
            str(num_body_bytes) + " body bytes &nbsp;&nbsp; " + \
            str(num_body_lines) + " body lines<br>"
        print("OK")
    except:
        body=""
        body_info=""
        num_body_bytes = 0
        num_body_lines=0

        if NLTK:
            try:
                text = nltk.clean_html(body)
                plain_bytes = len(text)
                plain_lines = text.count('\n')
                body_info = body_info + "PLAIN TEXT: " + \
                    str(plain_bytes) + " plain bytes &nbsp;&nbsp; " + \
                    str(plain_lines) + " plain lines<br>"
            except:
                print("Failed to calculate plaintext size using NLTK")

    if (num_body_bytes < SEND_MAIL_MIN_BYTES):
        print(f"{type(name)}=>{name}")
        print(f"{type(num_body_bytes)}=>{num_body_bytes}")
        print(f"{type(SEND_MAIL_MIN_BYTES)}=>{SEND_MAIL_MIN_BYTES}")
        #print("**** Not sending mail as num bytes="+str(num_body_bytes)+"< min("+str(SEND_MAIL_MIN_BYTES)+") [" + name + "]")
        print(f"**** Not sending mail as num bytes={num_body_bytes} < min({SEND_MAIL_MIN_BYTES}) [{name}]")
        return
    else:
        #print("**** Sending mail as num bytes="+str(num_body_bytes)+">= min("+str(SEND_MAIL_MIN_BYTES)+") [" + name + "]")
        print(f"**** Sending mail as num bytes={num_body_bytes} >= min({SEND_MAIL_MIN_BYTES}) [{name}]")

    print(f"SEND_MAIL_MIN_LINES={SEND_MAIL_MIN_LINES}")
    if (num_body_lines < SEND_MAIL_MIN_LINES):
        print(f"**** Not sending mail as num lines={num_body_lines} < min({SEND_MAIL_MIN_LINES} ) [{name}]")
        return
    else:
        print(f"**** Sending mail as num lines={num_body_lines} >= min({SEND_MAIL_MIN_LINES} ) [{name}]")

    if (entry != None):
        #entry_info ="<br><h3>Entry info:</h3>\n"
        entry_info ="<br><b>Entry info:</b>\n"
        entry_info = entry_info + "&nbsp;&nbsp;&nbsp;&nbsp; <b>url</b>: "
        entry_info = entry_info + "<a href='" + entry.url + "'> " + entry.url + "</a>"
        entry_info = entry_info + "<br>\n"

        for key in entry.fields.keys():
            entry_info = entry_info + "&nbsp;&nbsp;&nbsp;&nbsp;" + key + ": " + entry.fields.get(key) + "<br>\n"

        debug_info_text=""
        if (entry.dinfo):
            debug_info_text = "<hr>" + entry.dinfo_text
            
        #body = entry_info + "<br>" + str(num_body_bytes) + " body bytes<br><br>" + debug_info_text + body
        body = entry_info + body_info + debug_info_text + body

        if ('mailto' in entry.fields):
            #to = [ entry.fields.mailto ]
            to = entry.fields.get('mailto')

        if ('mailto+' in entry.fields):
            #to.append( entry.fields.mailto )
            to.append( entry.fields.get('mailto+') )

    if (runid == None):
        print("ERROR: in sendmail() runid is unset: " + traceback.format_exc())
        #runid=runids.get(period)
        runid="__NO_RUNID__"

    subject=f'[{runid}]<{num_body_bytes}c, {num_body_lines}l>: {name}'
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

    print("SENDER_EMAIL=" + SENDER_EMAIL)
    print("sender="+sender)
    print("sender_name="+sender_name)

    message = "From: " + sender_name
    message = message + " <"+sender+">\n" + "To: "
    message = message + ' '.join(to)
    message = message + "\nSubject: " + subject + "\n"

    for header in headers:
        message = message + header

    message = message + "\n\n" + body

    num_body_bytes = len(body)
    by = "[ with " + str(num_body_bytes) + " bytes]"

    #sender = 'from@mjbright.net'
    #receivers = ['mjbrightfr@gmail.com']

    PWD=None
    USER=None
    if SMTP_HOST_PWD_FILE:  PWD=readFile(SMTP_HOST_PWD_FILE)[0].strip()
    if SMTP_HOST_USER_FILE: USER=readFile(SMTP_HOST_USER_FILE)[0].strip()
    print(f"PWD={PWD} USER={USER}")

    try:
       if PWD:
           s = smtplib.SMTP('smtp.gmail.com', 587)
           s.set_debuglevel(2)
           s.starttls()
           s.ehlo()
       else:
           s = smtplib.SMTP(SMTP_HOST)
    except smtplib.SMTPException:
       print(f"**** Error: unable to connect to smtp host {SMTP_HOST}")

    if PWD:
        try:
            s.login(USER, PWD)
        except smtplib.SMTPException:
           print(f"**** Error: unable to login({USER}, {PWD}) to smtp host {SMTP_HOST}")

    try:
       s.sendmail(sender, to, message)
       print("**** Sent email to <" + ' '.join(to) + "> " + by + " " + subject)
    except smtplib.SMTPException:
       print("**** Error: unable to send email" + by + " " + subject)



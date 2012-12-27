
from bs4 import BeautifulSoup

# optional parser:
import html5lib
    
# parser used by json2html
import json

import urllib  # For POST data encoding
import urllib2 # For actual http GET/POST requests
import difflib

import os
import traceback
import gzip # For check_file_not_gzipped()

#from Utils import *
import Utils as u

#import unicodedata

class Entry:
    globalRunID=None
    Parser=None

    def __init__(self):
        self.fields = {}
        self.debug=False
        self.dinfo=False
        self.dinfo_text=""

    ################################################################################
    # get(self, field):

    def get(self, field):
        if field in self.fields:
            return self.fields[field]

        #if (self.fields[field]):
            #return self.fields[field]

        #if (self.fields.get(field)):
            #return self.fields.get(field)
            
        return None

    ################################################################################
    # set(self, field):

    def set(self, field, value):
        self.fields.set(field, value)

    ################################################################################
    # createFileName(self):

    def createFileName(self):

        if (self.get('filename_base')):
            return self.get('filename_base')

        file = self.url
        file = file.replace("http://", "")
        file = file.replace("https://", "")
        file = file.replace("/", "_")
        file = file.replace("?", "_")
        file = file.replace("&", "_")

        #return file[0:100]
        return file

    ################################################################################
    # get_page(self, DOWNLOAD_DIR):
    
    def get_page(self, DOWNLOAD_DIR):
        op_file = DOWNLOAD_DIR + "/" + self.createFileName()

        # Configure User-Agents:
        #TODO: read this from Scraper_config:
        UAs = dict({
          'ffox5': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'
          })

        ua = UAs.get('ffox5') # TODO: browser-configurable
    
        #HACK: remove trailing " in url used to distinguish multiple entries with same URL:
        #url = str(self.get('url')).rstrip('\"')
        url = str(self.url).rstrip('\"')
        print "url:" + url
    
        try:

            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', ua)]
            #opener = urllib2.build_opener()
            #opener.addheaders = [('User-agent', ua)]
            #req = opener.open(url, timeout=30)

            if ('post' in self.fields):
                #s= "Name1=Value1&Name2=Value2&Name3=Value3"
                post=self.fields['post']
                values = dict(item.split("=") for item in post.split("&"))
                #dict(csv.reader([item], delimiter='=', quotechar="'").next() 
                #for item in csv.reader([s], delimiter=';', quotechar="'").next())

                print "POST("+str(values)+") "+url
                data = urllib.urlencode(values)
                req = opener.open(url, data, timeout=30)
                #req = urllib2.Request(url, data)
                #response = urllib2.urlopen(req)
                #the_page = response.read()
            else:
                print "GET() "+url
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
            self.check_file_not_gzipped(op_file)
        except:
            print "ERROR: in get_page - failed gzip checking - " + traceback.format_exc()
    
        #except urllib2.Error as e:
                #print "urllib2.Error: " + e.fp.read()
    
    
    ################################################################################
    # def get_subtree_from_html(self, file, html, tag, attribute_name, attribute_value):

    def get_subtree_from_html(self, file, html, tag, attribute_name, attribute_value):
        value = None

        entry_key = tag + "_" + attribute_name

        search = "<" + tag + " " + attribute_name + "='" + attribute_value + "'>"
        search_text = "&lt;" + tag + " " + attribute_name + "='" + attribute_value + "'&gt;"

        #print "Getting content from root " + entry_key + "='" + attribute_value +"'"
        print "Getting content from root " + search + " tag"

        try:
            attrs=dict()
            attrs[attribute_name]=attribute_value

            print "main = html.find_all(" + tag + ",  attrs={" + attribute_name + " : " + attribute_value + "})"
            main = html.find_all(tag, attrs)

            # Would be good "sometimes" to show failed matches also - for now only show actual MATCH:
            if (len(main) > 0):
                self.dinfo_text = self.dinfo_text + "MATCHED " + str(len(main)) + " element(s) for root '" + search_text + "' tag <br>\n"
            print "MATCHED " + str(len(main)) + " element(s) for root '" + search + "' tag <br>\n"

            if (len(main) > 1):
                print "WARN: matched on more than 1 " + search + " tag"

            if (len(main) == 0):
                raise Exception("Not", " found")

            #print repr(main)

            contents=main[0].contents # Return contents of first match only
            #self.dinfo_text = self.dinfo_text + "MATCHED 1/" + str(len(main)) + " element(s) for root '" + search_text + "' tag [" + str(len(str(contents))) + " bytes]<br>\n"

            if self.debug:
                file = file + "." + entry_key + ".selection"
                print "Writing selection file: " + file
                u.writeFile(file, str(contents))

            return contents

        except:
            #self.dinfo_text = self.dinfo_text + "FAILED to match root '" + search_text + "' tag<br>\n"
            print "ERROR: Failed to find root at " + search + " tag"
            if self.debug:
                print traceback.format_exc()
                self.dinfo_text = self.dinfo_text + traceback.format_exc() + "<br>\n"
            raise

    ################################################################################
    # def _json2html(self, text):

    def _json2html(self, jsonStr, args=[]):

        jsonObj = json.loads(jsonStr)

        result = "<html>\n<title> Unknown </title>\n<body>\n"
        result = result + "<table>\n"

        items=0

        for item in jsonObj:
            items = items + 1
            #print "Adding item "+str(items)
	    result = result + "<tr>\n"

            for key in item.keys():
                if (args and (not key in args)):
                    continue

                result = result + "<td>"

                try:
                    value = u.encode2Ascii(item.get(key))
                    result = result + "<pre>" + value + "</pre>"
                except:
                    result = result + "UNICODE_ERROR"

                result = result + "</td>\n"

	    result = result + "</tr>\n"
           
        result = result + "</table>\n"
        result = result + "</body></html>\n"

        #print "return result=>len:"+str(len(result))
        return result
   

    ################################################################################
    # def json2html(self, text):
    
    def json2html(self, jsonStr, args=[]):
        try:
            return self._json2html(jsonStr, args)
        except:
            print "Failed to parse json: " + traceback.format_exc()
            return "Failed to parse json: " + traceback.format_exc()

    ################################################################################
    # def parse_page(self, DIR):
    
    def parse_page(self, DIR):

        url = self.get('url')
        print "--->parse_page(" + str(url) + ")"
        file = DIR + "/" + self.createFileName()
    
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
        text = u.encode2Ascii(text)
        f.close()
    
        try:
            if (self.get('parse')):
                parse = self.get('parse')

                if ("json" in parse):
                    if (parse == "json"):
                        text=self.json2html(text, [])
                    else:
                        #print "ARGS="+parse
                        args=parse[5:-1].split(",")
                        #print "args="+":".join(args)
                        text=self.json2html(text,args)
                        if (not text):
                            print "NO TEXT"
                            print "ERROR: Failed to parse json file: " + file
                            text="text(Failed to parse json)"
                        #else:
                            #print "len(text)="+str(len(text))

                    htmlfile = file + ".html"

            parser=Entry.Parser
            if (self.get('parser')):
                parser=self.get('parser')
        
            print "soup = BeautifulSoup(text, " + str(parser) +")"
           
	    if (parser == None):
	        soup = BeautifulSoup(text)
            else:
                if (parser == "html5lib"):
                    soup = BeautifulSoup(text, html5lib)
                else:
                    soup = BeautifulSoup(text, parser)

            #exit(0)

        except:
            print "ERROR: Failed to parse html file: " + file
            print traceback.format_exc()
            #return '<br> Failed to parse ' + file + '\n' + ''.join(open(file).readlines())
            return '<br> Failed to parse ' + file + '\n' + text
    
        try:
            print "Original encoding = " + str(soup.originalEncoding)
        except:
            print "Original encoding = <exception>"
    
        body = soup.body
    
        if (body == None):
            return ""
    
        #self.dinfo_text = self.dinfo_text + "<b> Searching in file '" + file + "'</b><br>\n"
        # TODO: strip off /home/mjb/var/:
        self.dinfo_text = self.dinfo_text + "<b> " + file + "</b><br>\n"

        ############################################################
        ## Try first root_div_class, root_div_id entries if present:
    
        for key in self.fields:
            if (key[0:5] == "root_"):
                attr_val=self.fields[key]
    
                parts=key.split("_")
                tag=parts[1]
                attr=parts[2]
                
                try:
                    return self.get_subtree_from_html(file, body, tag, attr, attr_val)
                except:
                    if (attr == "class"):
                        attr="id"
    
                    try:
                        return self.get_subtree_from_html(file, body, tag, attr, attr_val)
                    except:
                        pass
    
        root_div_class = None
        if ('root_div_class' in self.fields):
            root_div_class = self.get('root_div_class')
            try:
                return self.get_subtree_from_html(file, body, 'div', 'class', root_div_class)
            except:
                if (not 'root_div_id' in self.fields):
                    print "Trying as 'root_div_id'"
                    self.fields['root_div_id'] = root_div_class
    
        root_div_id = None
        if ('root_div_id' in self.fields):
            root_div_id = self.get('root_div_id')
    
            try:
                return self.get_subtree_from_html(file, body, 'div', 'id', root_div_id)
            except:
                pass
    
        ############################################################
        ## Then try root_div_class, root_div_id as 'content':
    
        if (not root_div_class == 'content'):
            root_div_class = 'content'
            try:
                return self.get_subtree_from_html(file, body, 'div', 'class', root_div_class)
            except:
                pass
    
        if (not root_div_id == 'content'):
            root_div_id='content'
            try:
                return self.get_subtree_from_html(file, body, 'div', 'id', root_div_id)
            except:
                pass
    
        ############################################################
        ## Then try body
        if (body):
            self.dinfo_text = self.dinfo_text + "Used full body<br>\n"
            return body.contents
    
        ############################################################
        ## If all else fails return nothing!
        print "Returning NO content"
        return "";
    
        #print main.prettify()
        #print repr(soup.prettify())
    
    ################################################################################
    # def diff_page(self, classId, NEW_DIR, OLD_DIR, email_attrs):
    
    def diff_page(self, classId, NEW_DIR, OLD_DIR, email_attrs):
        itemno=0
    
        new_lines = self.parse_page(NEW_DIR)
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
    
        if ((new_lines != "") and email_attrs['SEND_MAIL_INDIVIDUAL']):
            #body = ''.join(lines.readlines())
            #body = new_lines
            body = u.encode2Ascii(new_lines)
    
            if (('action' in self.fields) and (self.get('action')  == "email_selection")):
                print "email_selection"
    
                select_entries=email_attrs['select_entries']
                category=email_attrs['category']
                period=email_attrs['period']
                name=email_attrs['name']
                send_to= [ email_attrs['SEND_TO'] ]
                u.sendmail( self, send_to, body, select_entries, category, period, "SELECT: " + name, Entry.globalRunID)
                return ""
    
        try:
            old_lines = self.parse_page(OLD_DIR)
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
    
        
        file = NEW_DIR + "/" + self.createFileName() + ".new.prediff"
        u.writeFile(file, u.encode2Ascii(new_lines))
        file = NEW_DIR + "/" + self.createFileName() + ".old.prediff"
        u.writeFile(file, u.encode2Ascii(old_lines))
    
        print "   diff("+str(len(old_lines))+" old bytes vs. "+str(len(new_lines))+" new bytes)"
        diff_text = difflib.unified_diff(old_lines.split("\n"), new_lines.split("\n"))
        #print "   ==> "+str(len(diff))+" bytes different"
    
        if self.debug:
            try:
                #### file = NEW_DIR + "/" + self.createFileName() + ".diff"
                print "Writing diff file: " + file
                debug_diff_text = diff_text[:] # Deepcopy !!
                debug_diff_text = ' '.join(list(debug_diff_text))
                print "debug_diff_text len="+str(len(debug_diff_text))
                debug_diff_text = u.encode2Ascii(debug_diff_text)
                print "debug_diff_text len="+str(len(debug_diff_text))
                u.writeFile(file, debug_diff_text)
            except:
                print "ERROR: failed to write diff file: " + traceback.format_exc()
    
        show_new_only=True
        show_new_only=False
    
        div_page_diffs = "<hr>\n<div class id='"+classId+"'>\n"
        ##if (itemno > 0):
            ##item=str(itemno)
            ##div_page_diffs = div_page_diffs + "<a href='#item_"+item+"'> Prev</a>\n"
        ##nextno=str(itemno+2)
        ##div_page_diffs = div_page_diffs + "<a href='#item_"+nextno+"'>Next</a>\n"
    
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
    
            d = self.substitute_local_links(d)
    
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
    
        if self.debug:
            try:
                file = NEW_DIR + "/" + self.createFileName() + ".diff.NEW"
                print "Writing diff file: " + file
                debug_page_diffs = page_diffs[:] # Deepcopy !!
                debug_page_diffs = ' '.join(list(debug_page_diffs))
                print "debug_page_diffs len="+str(len(debug_page_diffs))
                debug_page_diffs = u.encode2Ascii(debug_page_diffs)
                print "debug_page_diffs len="+str(len(debug_page_diffs))
                u.writeFile(file, debug_page_diffs)
            except:
                print "ERROR: failed to write diff file: " + traceback.format_exc()
        page_diffs = div_page_diffs + page_diffs + "</div><<br/> <!-- "+classId+"-->\n\n"
    
        if ((page_diffs != "") and email_attrs['SEND_MAIL_INDIVIDUAL']):
            #body = ''.join(lines.readlines())
            body = page_diffs
    
            select_entries=email_attrs['select_entries']
            category=email_attrs['category']
            period=email_attrs['period']
            name=email_attrs['name']
            send_to= [ email_attrs['SEND_TO'] ]
            u.sendmail( self, send_to, body, select_entries, category, period, name, Entry.globalRunID)
    
        return page_diffs
    
    ################################################################################
    # def check_file_not_gzipped(self, file):

    def check_file_not_gzipped(self, file):
    
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
    
            u.writeFile(file, content)
     
    ################################################################################
    # def substitute_local_links(self, d):
    
    def substitute_local_links(self, d):
    
       file_slash=d.find('href="/')
    
       if (file_slash < 0):
           file_slash=d.find("href='/")
    
           if (file_slash < 0):
               return d
    
       slash=self.url.find("/")
    
       protocol = self.url[:slash-1]
       addr = self.url[slash+2:]
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
      
       #d = d.replace("href='/", "href='"+self.url)
       #d = d.replace('href="/', 'href="'+self.url)
    
       #if (orig != d):
          #print "orig("+orig+")=>"+d
    
       return d
    

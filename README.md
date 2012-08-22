Scraper
=======

Python-based Web Scraper script

Scraper is a Python-script to perform web scraping.

The intended functionality is to monitor web-sites specified in a text-file,
detecting changes and sending changes as fragments of HTML by e-mail.

History:
--------

2012-07-19: Creation of github archive
	Checkin of first code version (needs to be cleaned up to be used by you ...!)

FAQ:
----

- Why don't I just use an RSS reader for this?
    - Many web pages of interest don't have an RSS feed
    - I like to recieve notifications by e-mail not by other means
    - I've never liked using RSS readers
    - At some point maybe I'll allow other forms of notification

- Why reinvent the wheel?
    - I needed a good example application to teach myself Python
    - I didn't find the wheel I was looking for

NOTES:
------

**UNICODE problems notes:**
    http://stackoverflow.com/questions/492483/setting-the-correct-encoding-when-piping-stdout-in-python
    A rule of thumb is: Always use unicode internally. decode what you receive, encode what you send.

INSTALLATION:
-------------

**Dependencies**

  This software is currently developed and run using Python running under Debian "Wheezy"
  (more precisely "Raspbian" running on a Raspberry Pi => http://www.raspberrypi.org).

  It should have no problem running with most Unices and even under Windows.

  - Python
     This software is currently developed using Python 2.7.3

  - Beautiful Soup: (error tolerant) HTML parsing software
     This software is currently developed using bs4

  - *Other Python modules?* (requests?)

**To install**
  - Make sure you have Python, BeautifulSoup installed

  - Copy the *.py files to a suitable directory

  - Modify Scraper_Config.py to set the appropriate SMTP and SENDER parameters to be used for sending results e-mail

  - Create your own LIST.txt listing sites to be scraped, use TEST_LIST.txt as an example
          See below for explanation of syntax.

LIST SYNTAX:
------------

Each URL to be monitored has an entry of the form
  Entry Title
     tag1: value1
     tag2: value2
     tag3: value3

Where the "Entry Title" appears at the beginning of a line, serving as a delimiter between entries
(it is also strongly recommended that a blank line appears before this title line for readability)

The tag lines must be indented with spaces (arbitrary but at least 1).

*Acceptable tags are the following:*
    - http, https - to specify the URL to be monitored
              In this case the "tag:value" pair represents the full URL, e.g. http://mysite.com

    - root_<tag>_<attr> - to specify a subsection of the document to be treated
              By identifying that all useful content is contained within a <div id=content> tag for
              example, we can only interest ourselves in content within this tag.
              The line to specify this would be:
                    root_div_id:content

              This can allow to avoid unwanted sections of a page.

              Currently we use only the first corresponding entry (as multiple matching tags may exist)

              If no root tag is specified then the whole <body> is used.

    - runid - Used to specify the runid associated with this entry
              Typically the script will be run from cron with a specified period such as -week
              which automatically sets the runid to week

              A specific runid can also be set on the command-line using the -id argument.

    - filename_base - The software saves web pages, or the specified root section into a file
              with name based upon the specified URL.
              This option allows to specify another more readable base name for the file(s).

    - category - Arbitrary categories can be used to assign to entries
              These can be used to specify a subset of entries to treat using the "-c <category>" argument

    - enabled - By default all entries are enabled, but they may be enabled/disabled by
              setting this value to true or false

    - debug - Set debug mode for this entry, overides global debug mode setting
              Equivalent to -debug commd-line arg which sets global debug mode for all entries

    - dinfo - Set dinfo mode for this entry, overides global dinfo mode setting
              Equivalent to -dinfo commd-line arg which sets global dinfo mode for all entries

              Setting dinfo mode allows to include debugging info in the result e-mails, e.g.
              indicating if root_* entries were matched or not.

    - parser - By default the Beautiful Soup default parser is used, but it is recommended
              to specify a particular parser for each entry.

              Available parsers are 'html.parser', 'lxml', 'xml', 'html5lib'.
              For more info please refer to the BeautifulSoup documentation here:
                http://www.crummy.com/software/BeautifulSoup/bs4/doc/#specifying-the-parser-to-use

    - action - Default action to perform is to determine differences compared to a previous run.
              Another action is possible 'email_selection' which sends the whole selection,
              not just differences

    - mailto - By default mails are sent to the SEND_TO address configured in Scraper_Config.py
              Alternatively, a different value can be set for a particular entry using this value.

    - mailto+ - As mailto, but also sends mail to the SEND_TO address configured in
              Scraper_Config.py

    - proc - TODO

    - when - TODO

Running the scraper:
--------------------

    To list entries:
        all entries:
            ./Scraper.py -l LIST.txt

        all entries for weekly run:
            ./Scraper.py -week -l LIST.txt

        all entries for weekly run, and runid week_thurs:
            ./Scraper.py -week -id week_thurs -l LIST.txt

        all entries for category electronics:
            ./Scraper.py -c electronics -l LIST.txt

        all entries for category electronics, with arduino in the url:
            ./Scraper.py -c electronics -u arduino -l LIST.txt

        all entries for category electronics, with arduino in the entry tile:
            ./Scraper.py -c electronics -e arduino -l LIST.txt

    To obtain differences:

        For 4 hourly checks:
            ./Scraper.py -hour4 -get -diff -l 4HOURLY.txt

        For daily checks:
            ./Scraper.py -day -get -diff -l FULL_LIST.txt

        For weekly checks:
            ./Scraper.py -week -get -diff -l FULL_LIST.txt

Command-line invocations:
------------------------

    To be done later, in the meantime please refer to the following cron entries.

Example crontab entries:
------------------------

    ################################################################################
    ## Screen scraping:

    SCRAPER_DIR=/home/user/usr/cron/SCRAPER
    SCRAPER_VAR=/home/user/var
    SCRAPER=/home/user/usr/cron/SCRAPER/Scraper.py

    # Get pages:

    #Roughly every 4 hours (for pages which change often):
    01 03,07,12,15,19 * * * $SCRAPER -hour4 -get -diff -l $SCRAPER_DIR/4HOURLY.txt >> $SCRAPER_VAR/SCRAPER_hour.log 2>&1

    #Daily:
    03 06 * * * $SCRAPER -day  -get -diff -l $SCRAPER_DIR/FULL_LIST.txt >> $SCRAPER_VAR/SCRAPER_day.log 2>&1

    #Weekly: Thursday
    20 19 * * 4 $SCRAPER -week -get -diff -l $SCRAPER_DIR/OTHER_PEOPLE.txt >> $SCRAPER_VAR/SCRAPER_week_OTHERS.log 2>&1

    #Weekly: Thursday
    02 12 * * 4 $SCRAPER -week -get -diff -l $SCRAPER_DIR/FULL_LIST.txt >> $SCRAPER_VAR/SCRAPER_week.log 2>&1

    #Weekly: Friday-WE
    02 17 * * 5 $SCRAPER -week -id weekend -get -diff -l $SCRAPER_DIR/FULL_LIST.txt >> $SCRAPER_VAR/SCRAPER_weekend.log 2>&1

    #Monthly: 1st day of month
    02 05 11 * * $SCRAPER -month -get -diff -l $SCRAPER_DIR/FULL_LIST.txt >> $SCRAPER_VAR/SCRAPER_month.log 2>&1



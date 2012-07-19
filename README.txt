

                               Scraper - README
                             *------------------*

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

    UNICODE problems notes:
        http://stackoverflow.com/questions/492483/setting-the-correct-encoding-when-piping-stdout-in-python
        A rule of thumb is: Always use unicode internally. decode what you receive, encode what you send.



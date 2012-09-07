
Scraper_config = {
    # Parser to use:
    'PARSER' : None,
    #'PARSER' : 'html.parser',
    #'PARSER' : 'lxml'
    #'PARSER' : 'xml'
    #'PARSER' : 'html5lib'

    # Put your e-mail address here:
    'SEND_TO'     : 'scraper@jean-dupont.net',

    # Put the hostname or ip address of your service providers SMTP server here:
    'SMTP_HOST' : 'smtp.provider.fr',

    # Put the desired sender e-mail address here: no need to change this
    'SENDER_EMAIL': 'scraper_cron@scraper.net',

    # Put the desired sender name: no need to change this
    'SENDER_NAME' : 'Scraper',

    # If diffs to send are less than this number, don't send an e-mail, probably just junk: no need to change this
    'SEND_MAIL_MIN_BYTES'  : 30,

    # Send a separate e-mail of diffsfor each site: no need to change this
    'SEND_MAIL_INDIVIDUAL' : True,

    # Send diffs of all sites in just one e-mail: no need to change this
    'SEND_MAIL_GLOBAL'     : False,

    # Send error e-mail for each site which encounters an error in processing: no need to change this
    'SEND_ERROR_MAIL_INDIVIDUAL' : False,

    # Send one error e-mail for all sites which encounter errors in processing: no need to change this
    'SEND_ERROR_MAIL_GLOBAL'     : False,

    # Send an e-mail summary of all sites processed: no need to change this
    'SEND_MAIL_SUMMARY'          : False,
}


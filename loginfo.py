#!/usr/bin/env python3


import logging
import logging.config
from datetime import datetime


def getLogDetails():
    logging.config.fileConfig('/home/python/config/logging.ini',
                              defaults={'logfilename': getFileName()})
    logger = logging.getLogger('AddMember')
    return logger


def getFileName():
    frmt = datetime.today().strftime('%d-%m-%Y')
    fileName = '/home/python/textfile/Addmemberlog-' + frmt + '.log'
    return fileName

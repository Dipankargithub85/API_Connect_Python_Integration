#!/usr/bin/env python3

import requests
import urllib3
import configparser
import sys
import os
from os import path
import loginfo as log
from collections import Counter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = log.getLogDetails()


def getPropDetails():
    config = configparser.RawConfigParser()
    config.read('config/config.properties')
    details_dict = dict(config.items('Auth'))
    return details_dict


def getCatalogName(filename):
    if path.exists(filename):
        val = ""
        if os.path.getsize(filename) > 0:
            fl = open(filename, "r")
            val = fl.readlines().pop(0).replace("\n", "")
            logger.info('Catalog Name : %s', val)

    else:
        logger.warning('Catalog File Not Found')
        sys.exit(0)

    return val


def getAllSpace(envVal, spacecount, spacefile,
                catalogfile, getheader, hostName):
    url = getCatalogSpaceUrl(envVal, catalogfile, hostName)
    logger.debug('Space Url %s', url)
    wrfile = open(spacefile, 'a')
    wrfile.write("dummyRecord\n")
    response = requests.get(url, headers=getheader, verify=False)  # nosec
    if response.status_code != 200:
        logger.warning('Invalid end point to get All Space Name %s', url)
        sys.exit(0)
    data = response.json()
    totlen = len(data)
    i = 1

    for entry in data:
        space = entry["name"]

        if totlen == 1:
            wrfile.write(space)
        elif i < spacecount:
            space = space + ","
            i = i + 1
            wrfile.write(space)
        else:
            wrfile.write(space)
            wrfile.write("\n")
            i = 1
        totlen = totlen - 1

    wrfile.close()


def getCatalogSpaceUrl(envVal, catalogfile, hostName):
    catName = getCatalogName(catalogfile)
    logger.debug('catalog name in getCatalogSpaceUrl method %s', catName)
    envList = ['dev', 'pre', 'prointernal', 'proexternal', 'playground']
    if envVal not in envList:
        logger.info("Please provide correct env")
        sys.exit(0)

    url = 'https://' + hostName + '/v1/orgs/<orgname>/environments/' \
          + catName + '/spaces'
    logger.info('url for Space %s', url)
    return url


def getSpaceDetailsVal(spacefile):
    fileread = open(spacefile, "r")
    spaceval = fileread.readline()
    logger.info('Space name: %s', spaceval)
    return spaceval


def addUser():
    logger.debug('Started addUser()')
    envVal = ""
    if len(sys.argv) == 2:
        envVal = sys.argv[1]
    else:
        logger.warning("Script need argument as env name")
        sys.exit(0)

    # Get All Properties details
    dictauth = getPropDetails()
    credential = os.getenv('PASSWORD')
    catalogfile = dictauth["catalogfile"]
    spacefile = dictauth["spacefile"]
    defaultKid = dictauth["defaultfile"]
    spacecount = int(os.getenv('SPACECOUNT'))
    inpuser = os.getenv('INPUSER')
    rolestr = os.getenv('ROLES')
    rolelist = rolestr.split(",")
    logger.debug('Input user: %s', inpuser)
    hostName = dictauth[envVal]
    logger.debug('Hostname : %s', hostName)
    # Set all flag
    spaceflag = False
    catflag = False
    delfile = False
    # Get header:
    getheader = {'Authorization': 'Basic ' + credential}
    postheader = {'Authorization': 'Basic ' + credential,
                  'Content-Type': 'application/json'}

    # Check the file exist or not
    if path.exists(spacefile):
        if os.path.getsize(spacefile) > 0:
            spaceflag = True

        elif os.path.getsize(catalogfile) > 0:
            catflag = True

        else:
            logger.info('Done with Full execution for the Environment %s',
                        envVal)
            delfile = True

    else:
        catflag = True

    if catflag:
        getAllSpace(envVal, spacecount, spacefile,
                    catalogfile, getheader, hostName)
        delFirstLine(spacefile)

    if delfile:
        os.remove(spacefile)
        os.remove(catalogfile)
        sys.exit(0)

    if spaceflag and not catflag:
        url = getCatalogSpaceUrl(envVal, catalogfile, hostName)
        spaces = getSpaceDetailsVal(spacefile)
        response = requests.get(url, headers=getheader, verify=False)  # nosec

        if response.status_code != 200:
            logger.warning('Invalid url %s', url)
            sys.exit(0)

        data = response.json()

        for fentry in data:

            if fentry["name"] in spaces:

                spacename = fentry["name"]
                memurl = fentry["url"] + '/members'
                logger.debug('Member Url : %s', memurl)
                deets = requests.get(fentry["url"] + '/members',
                                     headers=getheader, verify=False)  # nosec

                if response.status_code != 200:
                    logger.warning('Invalid member url %s', memurl)
                else:
                    details = deets.json()

                    for entry in details:
                        if str(entry["envId"]) != 'None' \
                                and str(entry["spaceId"]) != 'None':
                            if 'na' in inpuser.lower():
                                if entry["user"]["username"][0] == 'C' \
                                        or entry["user"]["username"][0] == 'c'\
                                        or entry["user"]["username"][0] == 'E'\
                                        or entry["user"]["username"][0] == 'e':
                                    doUpdate(entry, postheader,
                                             getheader, memurl,
                                             hostName, rolelist,
                                             defaultKid, spacename)
                            else:
                                if entry["user"]["username"] in inpuser:
                                    doUpdate(entry, postheader,
                                             getheader, memurl,
                                             hostName, rolelist,
                                             defaultKid, spacename)

        delFirstLine(spacefile)
        if os.path.getsize(spacefile) == 0:
            if os.path.getsize(catalogfile) > 0:
                delFirstLine(catalogfile)
            else:
                logger.info('Done with Full execution for the Environment %s',
                            envVal)
                os.remove(spacefile)
                os.remove(catalogfile)
                sys.exit(0)

        if os.path.getsize(spacefile) == 0 \
                and os.path.getsize(catalogfile) == 0:
            logger.info('Done with Full execution for the Environment %s',
                        envVal)
            os.remove(spacefile)
            os.remove(catalogfile)
            sys.exit(0)

    logger.debug('Ended addUser()')


def delFirstLine(fileName):
    filedel = open(fileName, "r")
    lines = filedel.readlines()
    logger.debug('Deleted Spaces : %s', lines[0])
    filedel.close()

    del lines[0]
    modfile = open(fileName, "w+")
    for line in lines:
        modfile.write(line)

    modfile.close()


def doUpdate(entry, postheader, getheader, memurl, hostName, rolelist,
             defaultKid, spacename):
    logger.debug('Started doUpdate()')
    ldapid = entry["user"]["idpId"]
    userid = entry["user"]["username"]
    statuslist = ['200', '201', '202', '203', '200 OK', '204']
    if checkldapuser(ldapid, userid, getheader, hostName):
        userid = userid.replace(userid[0], 'K')
        if checkldapuser(ldapid, userid, getheader, hostName):
            roles = []
            for role in entry["roles"]:
                roles.append(role["name"])

            logger.debug('roles actual: %s', roles)
            finalRoles = getRolesDetails(roles, rolelist)
            logger.info('Roles Details to be added : %s', finalRoles)

            if len(finalRoles) > 0:
                email = entry["user"]["email"]
                fname = entry["user"]["firstName"]
                lname = entry["user"]["lastName"]
                context = entry["user"]["context"]
                payload = {
                    "email": email,
                    "firstName": fname,
                    "idpId": ldapid,
                    "lastName": lname,
                    "username": userid,
                    "context": context
                }
                # headers = {'Content-Type': "application/json"}
                logger.debug('Add User Detail %s', payload)

                response = requests.post('https://' + hostName + '/v1/users',
                                         json=payload, headers=postheader,
                                         verify=False)  # nosec

                if str(response.status_code) in statuslist:
                    respayload = response.json()
                    logger.debug('User Add Response: %s', respayload)
                    # preapare json file for next call to add role
                    addRole = {"user": respayload["id"], "roles": finalRoles}
                    logger.info('Add Role Payload: %s', addRole)
                    addRoleRs = requests.post(memurl, json=addRole,
                                              headers=postheader,
                                              verify=False)  # nosec

                    if str(addRoleRs.status_code) not in statuslist:
                        logger.warning('Roles are not added because :%s',
                                       addRoleRs.json())
                else:
                    logger.warning('User is not added:%s', response.json())
            else:
                logger.warning('%s User is not added.Role Details:%s',
                               userid, roles)
        else:
            wrkfile = open(defaultKid, 'a')
            wstr = userid + ':user is not available in ' \
                            'ldap under space:' + spacename
            wrkfile.write(wstr)
            wrkfile.write("\n")
            wrkfile.close()


def getRolesDetails(roles, rolelist):
    userRole = Counter(roles)
    notuseRole = Counter(rolelist)
    finallist = list((userRole - notuseRole).elements())
    return finallist


def checkldapuser(ldapid, userid, getheader, hostName):
    ldap = requests.get('https://' + hostName + '/v1/users/idp/'
                        + ldapid + '?searchFilter=' + userid,
                        headers=getheader, verify=False)  # nosec

    if ldap.status_code != 200:
        logger.debug('%s User is not available in ldap', userid)

    ldapjson = ldap.json()

    if isinstance(ldapjson, list):
        return True
    else:
        return False


if __name__ == "__main__":
    logger.info('JOB has Started')
    addUser()
    logger.info('JOB has Completed')

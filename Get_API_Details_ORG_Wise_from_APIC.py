#!/usr/bin/python

import requests
import urllib3
import configparser
import xlsxwriter
import sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def getPropDetails():

    config = configparser.RawConfigParser()
    config.read('C:\\Pyhon\\GETDEVORG\\config\\config.properties')
    details_dict = dict(config.items('Auth'))
    return details_dict


def getdetails():
    envList = ['dev', 'test']
    dictauth = getPropDetails()
    key = dictauth["id"]
    val = dictauth["val"]
    catlist = dictauth["catlist"]
    envVal=''
    catval=''
    if len(sys.argv) == 3:
        envVal = sys.argv[1]
        catval=  sys.argv[2]
        if envVal not in envList:
            print('Please provide valid env name dev/test')
            sys.exit(0)
        if catval not in catlist:
            print('Please provide valid catalog name as per environment',''.join(catlist))
            sys.exit(0)
    
    else:
        print('please provide two arguments environment name and catalog name')
        sys.exit(0)
    hostname= dictauth[envVal]
    baseurl= 'https://' + hostname + '/v1/orgs/<org-name>/environments/' + catval 
    response = requests.get(baseurl, auth=(key,val), verify=False)  # nosec
    data = response.json()
    baseurl = data['url']
    devorgurl = baseurl + '/subscriptions'  
    
    ogres = requests.get(devorgurl, auth=(key,val), verify=False)  # nosec
    ogdata = ogres.json()
    #print(ogdata)
    
    filename='APIDetailsORGWise_'+ envVal +'_'+catval +'.xlsx'
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet('APIDevorg')
    cell_format = workbook.add_format()
    
    cell_format.set_border()
    
    row=0
    col=0    
    worksheet.set_column(0,4,40)
    cell_format1 = workbook.add_format()
    cell_format1.set_border()
    
    cell_format1.set_bold(True)
    cell_format1.set_bg_color('#ccddff')
    worksheet.write(row, col, 'DevORGName',cell_format1)
    worksheet.write(row, col+1, 'ProductName',cell_format1)
    worksheet.write(row, col+2, 'ProductVer',cell_format1)
    worksheet.write(row, col+3, 'APIName',cell_format1)
    worksheet.write(row, col+4, 'APIVer',cell_format1)
    worksheet.write(row, col+5, 'APIStatus',cell_format1)
    
    i=0
    #j=1
    for fentry in ogdata:
       
        orgname=''
        prdid=''
        prdname=''
        prdver=''
        #status=''
        #fstnm=''
        #lnm=''
        try:
            orgname=fentry["consumerOrg"]["displayName"]
        except:
            orgname=''
            
            
        try:
            prdid=fentry["product"]["id"]
        except:
            prdid=''
            
        
        try:
            prdname=fentry["product"]["name"]
        except:
            prdname=''
            
        try:
            prdver=fentry["product"]["version"]
        except:
            prdver=''
            
        
        
       
        for sp in fentry["spaces"]:
            
            try:
                spaceid=sp["id"]
            except:
                spaceid=''
                     
            break

        
        prdurl = baseurl + '/spaces/'+ spaceid + '/products/' + prdid  
        prdres = requests.get(prdurl, auth=(key,val), verify=False)  # nosec
        prdresdata = prdres.json()
        for aver in prdresdata["dependents"]["APIVERSION"]:
            row = i
            apiname=''
            apiver=''
            status=''
            
            try:
                apiname = aver["apiName"]
            except:
                apiname=''
             
            try:
                apiver  = aver["apiVersion"]
            except:
                apiver=''    
                
            
            try:
                status  = aver["deploymentState"]
            except:
                status=''
            
            worksheet.write(row+1, col, orgname,cell_format)
            worksheet.write(row+1, col+1, prdname,cell_format)
            worksheet.write(row+1, col+2, prdver,cell_format)
            worksheet.write(row+1, col+3, apiname,cell_format)
            worksheet.write(row+1, col+4, apiver,cell_format)
            worksheet.write(row+1, col+5, status,cell_format)
          
            i = i+ 1  
        
    workbook.close()


getdetails()
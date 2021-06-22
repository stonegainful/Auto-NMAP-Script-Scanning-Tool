#***********************
#*     Main Program    *
#***********************

#-----------------------
#--- Import Library ----
#-----------------------
import nmap
import json
from argparse import ArgumentParser
from NSE_Module import *  #Costumize Module

#-----------------------
#--- Variable Define ---
#-----------------------
#--- Arguments variable ---
parser = ArgumentParser(description='Auto-NMAP Script Scaning Tool using NMAP NSE script to brute-force on open port and service, its based on port scanning result.', epilog='See the about&doc: https://hackmd.io/37N0NZXdQjWqZreM6EIYwQ')
parser.add_argument('HOST_IP', help='Target HOST IP Address')
parser.add_argument('-o', help='Using other tools brute-force, <OPT> is tool name. Support tool lists: HYDRA', dest='opt', default='')
args = parser.parse_args()
#--- Dictionary variable ---
# Host Scan Result (HOST IP->Servive Name->Product,Verison,Port,Script{Result})
dictPortScan = {}
#---- NMAP variable ----
nmScan = nmap.PortScanner()
#---- NSE_Moudule variable ----
nseScript = NSE_Module()
#-----------------------
#---- main function ----
#-----------------------
def main():
  # Welcome Message
  print ('Auto-NMAP Script Scaning Tool Starting...')
  # start nmap scan, 1st argument is IP address, 
  # command: nmap -oX - -sV <strIP_Address>
  # nmScan.scan(strIP_Address)
  processNMAP = subprocess.Popen(['nmap', '-Pn', args.HOST_IP, '-sV', '-sC', '-O', '-oX', 'ScanResult.xml'])
  processNMAP.wait()
  RawData = nmScan.scan(args.HOST_IP, arguments='-sV -O')
  # Write NMAP RAW Data into JSON file
  #with open('nmap_rawdata.txt', 'w+') as outfile:  
  #  json.dump(RawData, outfile)
  # List all hosts using for loop
  # nmScan.all_hosts() will list all scanned hosts
  # variable:host is one of scanned hosts, value is IP_Address
  for host in nmScan.all_hosts():
    print('----------------------------------------------------')
    # index: nmScan[<IP>]['hostnames']['name']
    print('Host : %s (%s)' % (host, nmScan[host].hostname())) 
    # index: nmScan[<IP>]['status']['state']
    print('State : %s' % nmScan[host].state()) 
    # Get OS information from [host]['osmatch'][ArrayIndex]['osclass'][ArrayIndex]['osfamily']
    # To Do: If Scanning results had multi os match results, it should change into for loop to get OS info
    for hostOS in range(len(nmScan[host]['osmatch'])):
      strOS = nmScan[host]['osmatch'][hostOS]['osclass'][hostOS]['osfamily']
      dictPortScan[host] = {'OS':strOS}
    # List all protocol on host using for loop
    # nmScan[host].all_protocols() will list all of protocols on host
    # variable:proto is one of scanned hosts, value is tcp || udp
    for proto in nmScan[host].all_protocols():
      print('----------')
      print('Protocol : %s' % proto)
      # nmScan[<IP>][proto].keys() will list all keys(key are port number)
      # vaiable:lport are ports
      lport = nmScan[host][proto].keys()
      lport.sort()
      # List all port number & state(up || down) on host using for loop
      # variable:port, type is <int>
      # A host scan info in Dictionary(Servive Name->Product,Verison,Port)
      dictService = {}
      # traverse every port info into dictService
      for port in lport:
        # print infomation
        print ('port : %s\tstate : %s' % (port, nmScan[host][proto][port]['state']))
        # record Product, Name(Service Name) and version
        strProc=nmScan[host][proto][port]['product']
        strName=nmScan[host][proto][port]['name']
        strVer=nmScan[host][proto][port]['version']
        
        if strName not in dictService:
          # if Service Name is new, add new record into dictService
          dictService[strName] = {'products':strProc, 'versions':strVer, 'ports': str(port), 'scripts':{}}
        else:
          # if Service Name is existed, append new record into dictService
          dictService[strName]['products'] = dictService[strName]['products'] + ';' + strProc
          dictService[strName]['versions'] = dictService[strName]['versions'] + ';' + strVer
          dictService[strName]['ports'] = dictService[strName]['ports'] + ',' + str(port)
  
      # append dictService into dictPortScan[<host_IP>]
      dictPortScan[host] = dictService
  
  for ip in dictPortScan.keys():
    # FTP Service
    if 'ftp' in dictPortScan[ip].keys():
      print ('***Start FTP brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['ftp']['ports'], 'ftp', dictPortScan[ip]['ftp'])
      else: 
        nseScript.FTP(ip, dictPortScan[ip]['ftp']['ports'], dictPortScan[ip]['ftp'])
      print ('***Complete FTP brute force scan***')
    # SSH Service
    if 'ssh' in dictPortScan[ip].keys():
      print ('***Start SSH brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['ssh']['ports'], 'ssh', dictPortScan[ip]['ssh'])
      else: 
        nseScript.SSH(ip, dictPortScan[ip]['ssh']['ports'], dictPortScan[ip]['ssh'])
      print ('***Complete SSH brute force scan***')
    # Telnet Service
    if 'telnet' in dictPortScan[ip].keys():
      print ('***Start Telnet brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['telnet']['ports'], 'telnet', dictPortScan[ip]['telnet'])
      else: 
        nseScript.Telnet(ip, dictPortScan[ip]['telnet']['ports'], dictPortScan[ip]['telnet'])
      print ('***Complete Telnet brute force scan***')
    # SMTP Service
    if 'smtp' in dictPortScan[ip].keys():
      print ('***Start SMTP brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['smtp']['ports'], 'smtp', dictPortScan[ip]['smtp'])
      else: 
        nseScript.SMTP(ip, dictPortScan[ip]['smtp']['ports'], dictPortScan[ip]['smtp'])
      print ('***Complete SMTP brute force scan***')
    # DNS Service
    if 'domain' in dictPortScan[ip].keys():
      print ('***Start DNS brute force scan***')
      nseScript.DNS(ip, dictPortScan[ip]['domain']['ports'], dictPortScan[ip]['domain'])
      # HYDRA is not support DNS service
      print ('***Complete DNS brute force scan***')
    # HTTP Service
    if 'http' in dictPortScan[ip].keys():
      print ('***Start HTTP brute force scan***')
      # Using <http-auth-finder> to find authentication form
      # Function returned a list of authentication form, listPath is temporary variable to store returned value
      listPath = nseScript.HTTP_Auth_Finder(ip, dictPortScan[ip]['http']['ports'], dictPortScan[ip]['http'])
      # Initial dictPortScan[ip]['http']['scripts'], data type is array
      dictPortScan[ip]['http']['scripts'] = []
      # In list, format is port/path, so using '/' to split.
      # Reason of split('/', 1) is only need to split port & path. Keep other '/'symbol in path
      for path in listPath:
        listurl = path.split('/', 1)
        # Every list after split, send to HTTP_FORM function (IP, port, path, host_info)
        if "wordpress" in str(listurl[1]):
          nseScript.HTTP_WORDPRESS(ip, str(listurl[0]), '/' + str(listurl[1]), dictPortScan[ip]['http']['scripts'])
        else:
          nseScript.HTTP_FORM(ip, str(listurl[0]), '/' + str(listurl[1]), dictPortScan[ip]['http']['scripts'])
      # To do: 
      #   If found web service, call W3AF to do web vulnerablility scan
      #   HYDRA is support HTTP(S) service, but have to choose http-{head|get|post} method or http-{get|post}-form method
      #   So that's need to customize for HTTP(S) service
      print ('***Complete HTTP brute force scan***')
    # POP3 Service
    if 'pop3' in dictPortScan[ip].keys():
      print ('***Start POP3 brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['pop3']['ports'], 'pop3', dictPortScan[ip]['pop3'])
      else: 
        nseScript.POP3(ip, dictPortScan[ip]['pop3']['ports'], dictPortScan[ip]['pop3'])
      print ('***Complete POP3 brute force scan***')
    # SMB Service for Samba on Linux
    if 'netbios-ssn' in dictPortScan[ip].keys():
      print ('***Start SMB brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['netbios-ssn']['ports'], 'smb', dictPortScan[ip]['netbios-ssn'])
      else: 
        nseScript.SMB(ip, dictPortScan[ip]['netbios-ssn']['ports'], dictPortScan[ip]['netbios-ssn'])
      print ('***Complete SMB brute force scan***')
    # SMB Service for Microsoft-OS
    if 'microsoft-ds' in dictPortScan[ip].keys(): 
      print ('***Start SMB brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['microsoft-ds']['ports'], 'smb', dictPortScan[ip]['microsoft-ds'])
      else: 
        nseScript.SMB(ip, dictPortScan[ip]['microsoft-ds']['ports'], dictPortScan[ip]['microsoft-ds'])
      print ('***Complete SMB brute force scan***')
    # SNMP Service
    if 'snmp' in dictPortScan[ip].keys():
      print ('***Start SNMP brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['snmp']['ports'], 'snmp', dictPortScan[ip]['snmp'])
      else: 
        nseScript.SNMP(ip, dictPortScan[ip]['snmp']['ports'], dictPortScan[ip]['snmp'])
      print ('***Complete SNMP brute force scan***')
    # IMAP Service
    if 'imap' in dictPortScan[ip].keys():
      print ('***Start IMAP brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['imap']['ports'], 'imap', dictPortScan[ip]['imap'])
      else: 
        nseScript.IMAP(ip, dictPortScan[ip]['imap']['ports'], dictPortScan[ip]['imap'])
      print ('***Complete IMAP brute force scan***')
    # LDAP Service
    if 'ldap' in dictPortScan[ip].keys():
      print ('***Start LDAP brute force scan***')
      nseScript.LDAP(ip, dictPortScan[ip]['ldap']['ports'], dictPortScan[ip]['ldap'])
      # HYDRA is support LDAP service, but have to choose LDAP2 or LDAP3 service
      # Need to customize for LDAP service
      print ('***Complete LDAP brute force scan***')
    # HTTPS Service
    if 'https' in dictPortScan[ip].keys():
      print ('***Start SSL scan***')
      nseScript.SSL(ip, dictPortScan[ip]['https']['ports'], dictPortScan[ip]['https'])
      # HYDRA is support HTTP(S) service, but have to choose http-{head|get|post} method or http-{get|post}-form method
      # So that's need to customize for HTTP(S) service
      print ('***Complete SSL scan***')
    # Exec Service
    if 'exec' in dictPortScan[ip].keys():
      print ('***Start Exec brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['exec']['ports'], 'rexec', dictPortScan[ip]['exec'])
      else: 
        nseScript.Rexec(ip, dictPortScan[ip]['exec']['ports'], dictPortScan[ip]['exec'])
      print ('***Complete Exec brute force scan***')
    # Login Service
    if 'login' in dictPortScan[ip].keys():
      print ('***Start Login brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['login']['ports'], 'rlogin', dictPortScan[ip]['login'])
      else: 
        nseScript.Rlogin(ip, dictPortScan[ip]['login']['ports'], dictPortScan[ip]['login'])
      print ('***Complete Login brute force scan***')
    # Microsoft SQL Server Service
    if ('ms-sql-s' in dictPortScan[ip].keys()) or (1433 in nmScan[host][proto].keys()):
      print ('***Start Microsoft SQL Server brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['ms-sql-s']['ports'], 'mssql', dictPortScan[ip]['ms-sql-s'])
      else: 
        nseScript.MSSQL(ip, dictPortScan[ip]['ms-sql-s']['ports'], dictPortScan[ip]['ms-sql-s'])
      print ('***Complete Microsoft SQL Server brute force scan***')
    # Oracle Service
    if ('oracle' in dictPortScan[ip].keys()) or (1521 in nmScan[host][proto].keys()):
      print ('***Start Oracle brute force scan***')
      if args.opt == 'HYDRA': 
        # HYDRA support oracle for oracle-listener || oracle-sid
        # That's why there are two function but have different service name
        nseScript.HYDRA(ip, dictPortScan[ip]['oracle']['ports'], 'oracle-listener', dictPortScan[ip]['oracle'])
        nseScript.HYDRA(ip, dictPortScan[ip]['oracle']['ports'], 'oracle-sid', dictPortScan[ip]['oracle'])
      else: 
        nseScript.Oracle(ip, dictPortScan[ip]['oracle']['ports'], dictPortScan[ip]['oracle'])
      print ('***Complete Oracle brute force scan***')
    # MySQL Service
    if 'mysql' in dictPortScan[ip].keys():
      print ('***Start MySQL brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['mysql']['ports'], 'mysql', dictPortScan[ip]['mysql'])
      else: 
        nseScript.MySQL(ip, dictPortScan[ip]['mysql']['ports'], dictPortScan[ip]['mysql'])
      print ('***Complete MySQL brute force scan***')
    # PostgreSQL Service
    if 'postgresql' in dictPortScan[ip].keys():
      print ('***Start PostgreSQL brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['postgresql']['ports'], 'postgres', dictPortScan[ip]['postgresql'])
      else: 
        nseScript.PgSQL(ip, dictPortScan[ip]['postgresql']['ports'], dictPortScan[ip]['postgresql'])
      print ('***Complete PostgreSQL brute force scan***')
    # VNC Service
    if 'vnc' in dictPortScan[ip].keys():
      print ('***Start VNC brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['vnc']['ports'], 'vnc', dictPortScan[ip]['vnc'])
      else: 
        nseScript.VNC(ip, dictPortScan[ip]['vnc']['ports'], dictPortScan[ip]['vnc'])
      print ('***Complete VNC brute force scan***')
    '''
    # IRC Service
    if 'irc' in dictPortScan[ip].keys():
      print ('***Start IRC brute force scan***')
      if args.opt == 'HYDRA': 
        nseScript.HYDRA(ip, dictPortScan[ip]['irc']['ports'], 'irc', dictPortScan[ip]['irc'])
      else:         
        nseScript.IRC(ip, dictPortScan[ip]['irc']['ports'], dictPortScan[ip]['irc'])
      print ('***Complete IRC brute force scan***')
    '''
    # Apache JServ Protocol Service
    if 'ajp13' in dictPortScan[ip].keys():
      print ('***Start Apache Jserv brute force scan***')
      nseScript.AJP(ip, dictPortScan[ip]['ajp13']['ports'], dictPortScan[ip]['ajp13'])
      # HYDRA is not support Apache JServ Protocol service
      print ('***Complete Apache Jserv brute force scan***')
    # MongoDB Service
    if ('mongodb' in dictPortScan[ip].keys()) or (27017 in nmScan[host][proto].keys()) or (27018 in nmScan[host][proto].keys()) or (27019 in nmScan[host][proto].keys()):
      # To do comfirm service name is "mongodb" or not
      print ('***Start MongoDB brute force scan***')
      nseScript.Mongo(ip, dictPortScan[ip]['mongodb']['ports'], dictPortScan[ip]['mongodb'])
      # HYDRA is not support MongoDB service
      print ('***Complete MongoDB brute force scan***')
    # IBM DB2 (DRDA) Service
    if ('drda' in dictPortScan[ip].keys()) or (50000 in nmScan[host][proto].keys()):
      # To do comfirm service name is "drda" or not
      print ('***Start IBM DB2 (DRDA) brute force scan***')
      nseScript.DRDA(ip, dictPortScan[ip]['drda']['ports'], dictPortScan[ip]['drda'])
      # HYDRA is not support DRDA service
      print ('***Complete IBM DB2 (DRDA) brute force scan***')
  #print dictPortScan
  # Wrtie Scanning Result into file (JSON Format)
  with open('ScanResult.json', 'w+') as outfile:  
    json.dump(dictPortScan, outfile)
  # Re-name Scan Result File    
  os.rename('ScanResult.xml', args.HOST_IP+'.xml')
  os.rename('ScanResult.json', args.HOST_IP+'.json')
  
if __name__ =="__main__":
  main()
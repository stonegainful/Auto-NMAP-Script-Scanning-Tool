#***********************
#* NMAP Script Module  *
#***********************

#-----------------------
#--- Import Library ----
#-----------------------
import nmap
import subprocess
import os
import json
import configparser
#-----------------------
#--- Variable Define ---
#-----------------------
#--- String variable ---
# Loading from config file
config = configparser.ConfigParser()
config.read('Config.ini')
# Set HYDRA, User Dictionary and Password Dictionary File Path
if os.name == 'nt':
  strHYDRA_Path = os.path.dirname(__file__) + config.get('Windows', 'HYDRA_Path')
  strUserName_Path = config.get('Windows', 'UserName_Dictionary_Path')
  strPassword_Path = config.get('Windows', 'Password_Dictionary_Path')
elif os.name == 'posix':
  strHYDRA_Path = config.get('Linux', 'HYDRA_Path')
  strUserName_Path = config.get('Linux', 'UserName_Dictionary_Path')
  strPassword_Path = config.get('Linux', 'Password_Dictionary_Path')
else:
  print ('OS cannot define!! Variable setting Fail!!')

class NSE_Module:

  # HYDRA brute-force Function
  # using HYDRA to scan <service_name>://<target_ip>:<port>, and brute-force with USER_NAME & PASSWORD Dictionary file
  # ip: Targer ip Address
  # ports: Targer service port, it concat with ",". So need to split with "," to extract every ports
  # name: Servive Name, like <ftp>, <ssh> and etc
  # host: host scan info, need to combine script scanning result
  def HYDRA(self, ip, ports, name, host):
    # Dictionary variable for script results (temporary)
    dictScript = {}
    for port in ports.split(','):
      # for HYDRA, Service string format is: <service_name>://<server_ip>:<port>
      # Using input parameters to concat string for HYDRA 
      strService = name + '://' + ip + ':' + port
      strFile = ip + '_' + port + '.json'
      # Start HYDRA
      # strHYDRA_Path is Global Variable in NSE_Module.py
      # -L <username_list_file>: using username dictionary file, strUserName_Path is Global Variable in NSE_Module.py
      # -P <password_list_file>: using password dictionary file, strPassword_Path is Global Variable in NSE_Module.py
      # -o <output_file>: output to <output_file>. in this case, output file name format is "<ip>_<port>.txt"
      # -b JSON: output result format. in this case output file format is JSON
      processHYDRA = subprocess.Popen([strHYDRA_Path, '-L', strUserName_Path, '-P', strPassword_Path, '-e', 'ns', '-o', strFile, '-b', 'json', strService])
      #processHYDRA = subprocess.Popen([strHYDRA_Path, '-l', 'user', '-p', 'user', '-o', strFile, '-b', 'json', strService])
      processHYDRA.wait()
      # Read result (json file) and Wrtie back to host
      # (In fact, host is dictPortScan variable in main.py)
      if(os.path.isfile(strFile)):
        with open(strFile) as json_file:
          data = json.load(json_file)
          # make sure data is not null
          if not (data['results'] is None):
            dictScript[port] = [] # initail dictScript{}
            for result in data['results']:
              # append on dictScript
              dictScript[port].append({'username': str(result['login']), 'password': str(result['password'])})
              print ('[port:%s] username: ''%s'' password: ''%s''' % (port, result['login'], result['password']))
          else:
            print ('*No executed Results on Port %s*' % (port))
        # remove result file after extract result
        os.remove(strFile)
      else:
        print ('*No file existed!!')
    # Script results update into host(host is dictPortScan[ip][service_name])
    host['scripts'] = dictScript
      
    return 0
    
  # FTP Script Scan Function
  # using nmap script <ftp-brute> to scan port 21 & brute force crack password
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def FTP(self, ip, ports, host):
    # >> nmap <ip> -p 21 -script=ftp-brute || >> nmap <ip> -p 21 -script=ftp-*
    # NMAP variable in FTP func()
    nmScan_FTP = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=ftp-brute,ftp-anon'
    # strArgs = '-p ' + port + ' -script=ftp-*' # if want to using all of FTP Script, open this command
    # FTP brute force script <ftp-brute>
    nmScan_FTP.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_FTP[ip]['tcp']:
      thisDict = nmScan_FTP[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # SSH Script Scan Function
  # using nmap script <ssh-brute> to scan port 22 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def SSH(self, ip, ports, host):
    # >> nmap <ip> -p 22 -script=ssh-brute || >> nmap <ip> -p 22 -script=ssh-*
    # NMAP variable in SSH func()
    nmScan_SSH = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=ssh-brute'
    # strArgs = '-p ' + port + ' -script=ssh-*' # if want to using all of SSH Script, open this command
    # SSH brute force script <ssh-brute>
    nmScan_SSH.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_SSH[ip]['tcp']:
      thisDict = nmScan_SSH[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # Telnet Script Scan Function
  # using nmap script <telnet-brute> to scan port 23 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def Telnet(self, ip, ports, host):
    # >> nmap <ip> -p 23 -script=telnet-brute || >> nmap <ip> -p 23 -script=telnet-*
    # NMAP variable in Telnet func()
    nmScan_Telnet = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=telnet-brute'
    # strArgs = '-p ' + port + ' -script=telnet-*' # if want to using all of Telnet Script, open this command
    # Telnet brute force script <telnet-brute>
    nmScan_Telnet.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_Telnet[ip]['tcp']:
      thisDict = nmScan_Telnet[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('No Script executed on Port %s' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # SMTP Script Scan Function
  # using nmap script <smtp-brute> to scan port 25 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def SMTP(self, ip, ports, host):
    # >> nmap <ip> -p 25 -script=smtp-brute || >> nmap <ip> -p 25 -script=smtp-*
    # NMAP variable in SMTP func()
    nmScan_SMTP = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=smtp-brute'
    # strArgs = '-p ' + port + ' -script=smtp-*' # if want to using all of SMTP Script, open this command
    # SMTP brute force script <smtp-brute>
    nmScan_SMTP.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_SMTP[ip]['tcp']:
      thisDict = nmScan_SMTP[ip]['tcp'][port]      
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # DNS Script Scan Function
  # using nmap script <dns-brute> to scan port 53 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def DNS(self, ip, ports, host):
    # >> nmap <ip> -p 53 -script=dns-brute || >> nmap <ip> -p 53 -script=dns-*
    # NMAP variable in DNS func()
    nmScan_DNS = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=dns-brute'
    # strArgs = '-p ' + port + ' -script=dns-*' # if want to using all of DNS Script, open this command
    # DNS brute force script <dns-brute>
    nmScan_DNS.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_DNS[ip]['tcp']:
      thisDict = nmScan_DNS[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # HTTP Authentication Form Script Scan Function
  # Using nmap script <http-auth-finder> to scan HTTP service to find web pages requiring form-based or HTTP-based authentication
  # Results are returned in a table with each url and the detected method
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def HTTP_Auth_Finder(self, ip, ports, host):
    # >> nmap <ip> -p 80 -script=http-brute,http-form-brute || >> nmap <ip> -p 80 -script=http-*
    # NMAP variable in HTTP func()
    nmScan_HTTP_Auth_Finder = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    intMaxdepth = config.get('Common', 'MAX_DEPTH')
    intMaxpagecount = config.get('Common', 'MAX_PAGECOUNT')
    # return list
    listPath = []
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script="http-auth-finder" -script-args="http-auth-finder.maxdepth='+ intMaxdepth +',http-auth-finder.maxpagecount=' + intMaxpagecount + '"'
    # strArgs = '-p ' + port + ' -script=http-*' # if want to using all of HTTP Script, open this command
    # HTTP brute force script <http-brute>, <http-form-brute>, <http-iis-short-name-brute>,
    # <http-proxy-brute>, <http-wordpress-brute>
    nmScan_HTTP_Auth_Finder.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_HTTP_Auth_Finder[ip]['tcp']:
      thisDict = nmScan_HTTP_Auth_Finder[ip]['tcp'][port]
      if 'script' in thisDict: 
        #print ('*Script executed on Port %s*' % (port))
        #dictScript[str(port)] = {} # Initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          #print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          #dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
          # split path to extracrt path for execute <http-form-brute> script
          for strTemp in thisDict['script'][str(thisScript)].split('\n'):
            if "withinhost=" in strTemp:
              ip = strTemp.split('withinhost=')[1] # extract ip address
            elif "http" in strTemp:
              tempPath = strTemp.split(ip)[1] # extract url path without protocal+ip <http://ip>
              realPath = tempPath.split()[0] # extract url path without method <FORM, HTTP: Basic>
              if port == 80:
                realPath = str(port) + realPath 
              listPath.append(realPath.strip(':'))
      else:
        print ('*No Script executed on Port %s*' % (port))
    #Script results update into host(host is dictPortScan[ip][service_name])
    #host['scripts'] = dictScript
    
    return listPath
  
  # HTTP_FORM_BRUTE Script Scan Function
  # using nmap script <http-form-brute> to brute force crack password on HTTP service with authantication
  # Arguments:
  #   ip: ip address with url path
  #   ports: all ports of this service
  #   path: url path for nmap script arguments <http-form-brute.path >
  #   host: host scan info, need to combine script scanning result.
  #         Different then other function, <host> data type is array, not a dictionary
  # Return Value:
  #   None
  def HTTP_FORM(self, ip, ports, path, host):
    # >> nmap <ip> -p 80 -script="http-form-brute" -script-args="http-form-brute.path='<path>'"
    # NMAP variable in HTTP_FORM func()
    nmScan_HTTP_FORM = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script="http-form-brute" -script-args="http-form-brute.path=\'' + path + '\'"'
    nmScan_HTTP_FORM.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_HTTP_FORM[ip]['tcp']:
      thisDict = nmScan_HTTP_FORM[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s, Path:%s*' % (port, path))
        tmpIndexName = str(port)+path # temp variable for index name
        dictScript[tmpIndexName] = {} # Initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[tmpIndexName][str(thisScript)] = thisDict['script'][str(thisScript)]
        #Script results update into host(host is dictPortScan[ip][service_name][scripts], is an array)
        host.append(dictScript)
      else:
        print ('*No Script executed on Port %s, Path:%s*' % (port, path))
    
    return 0
  
  # HTTP Script Scan Function
  # using nmap script <http-brute>, <http-form-brute>, <http-iis-short-name-brute>,
  # <http-proxy-brute>, <http-wordpress-brute> to scan port 80 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def HTTP_WORDPRESS(self, ip, ports, path, host):
    # >> nmap <ip> -p 80 -script=http-brute,http-form-brute || >> nmap <ip> -p 80 -script=http-*
    # NMAP variable in HTTP func()
    nmScan_HTTP_WORDPRESS = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script="http-wordpress-brute" -script-args="http-wordpress-brute.uri=\'' + path + '\'"'
    # strArgs = '-p ' + port + ' -script=http-*' # if want to using all of HTTP Script, open this command
    # HTTP brute force script <http-brute>, <http-form-brute>, <http-iis-short-name-brute>,
    # <http-proxy-brute>, <http-wordpress-brute>
    nmScan_HTTP_WORDPRESS.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_HTTP_WORDPRESS[ip]['tcp']:
      thisDict = nmScan_HTTP_WORDPRESS[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s, Path:%s*' % (port, path))
        tmpIndexName = str(port)+path # temp variable for index name
        dictScript[tmpIndexName] = {} # Initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[tmpIndexName][str(thisScript)] = thisDict['script'][str(thisScript)]
        host.append(dictScript)
      else:
        print ('*No Script executed on Port %s*' % (port))
    #Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    #host['scripts'] = dictScript
    
    return 0
    
  # POP3 Script Scan Function
  # using nmap script <pop3-brute> to scan port 110 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def POP3(self, ip, ports, host):
    # >> nmap <ip> -p 110 -script=pop3-brute || >> nmap <ip> -p 110 -script=pop3-*
    # NMAP variable in POP3 func()
    nmScan_POP3 = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=pop3-brute'
    # strArgs = '-p ' + port + ' -script=pop3-*' # if want to using all of POP3 Script, open this command
    # POP3 brute force script <pop3-brute>
    nmScan_POP3.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_POP3[ip]['tcp']:
      thisDict = nmScan_POP3[ip]['tcp'][port]
      if 'script' in thisDict:
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
  
  # SMB Script Scan Function
  # using nmap script <smb-brute> to scan port 139,445 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def SMB(self, ip, ports, host):
    # >> nmap <ip> -p 139,445 -script=smb-brute || >> nmap <ip> -p 139,445 -script=smb-*
    # NMAP variable in SMB func()
    nmScan_SMB = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=smb-brute,smb-os-discovery'
    # strArgs = '-p ' + port + ' -script=smb-*' # if want to using all of SMB Script, open this command
    # SMB brute force script <smb-brute>
    nmScan_SMB.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    if 'hostscript' in nmScan_SMB[ip]:
      print ('*Script executed on Port %s*' % (ports))
      dictScript[str(ports)] = {} # initail dictScript{}
      for index in nmScan_SMB[ip]['hostscript']:
        print ('Script Name ''%s'':%s' % (index['id'], index['output']))
        # index: script name in nmScan_SMB[ip]['hostscript'][index num]['id']
        # index: script result in nmScan_SMB[ip]['hostscript'][index num]['output']
        dictScript[str(ports)][str(index['id'])] = index['output']
    else:
      print ('*No Script executed on Port %s*' % (ports))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # SNMP Script Scan Function
  # using nmap script <snmp-brute> to scan port 161 & brute force crack password
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def SNMP(self, ip, ports, host):
    # >> nmap <ip> -p 161 -script=snmp-brute || >> nmap <ip> -p 161 -script=snmp-*
    # NMAP variable in SNMP func()
    nmScan_SNMP = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=snmp-brute'
    # strArgs = '-p ' + port + ' -script=snmp-*' # if want to using all of SNMP Script, open this command
    # SNMP brute force script <snmp-brute>
    nmScan_SNMP.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_SNMP[ip]['tcp']:
      thisDict = nmScan_SNMP[ip]['tcp'][port]     
      if 'script' in thisDict:
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # IMAP Script Scan Function
  # using nmap script <imap-brute> to scan port 220 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def IMAP(self, ip, ports, host):
    # >> nmap <ip> -p 220 -script=imap-brute || >> nmap <ip> -p 220 -script=imap-*
    # NMAP variable in IMAP func()
    nmScan_IMAP = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=imap-brute'
    # strArgs = '-p ' + port + ' -script=imap-*' # if want to using all of IMAP Script, open this command
    # IMAP brute force script <imap-brute>
    nmScan_IMAP.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_IMAP[ip]['tcp']:
      thisDict = nmScan_IMAP[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # LDAP Script Scan Function
  # using nmap script <ldap-brute> to scan port 389 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def LDAP(self, ip, ports, host):
    # >> nmap <ip> -p 389 -script=ldap-brute || >> nmap <ip> -p 389 -script=ldap-*
    # NMAP variable in IMAP func()
    nmScan_LDAP = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=ldap-brute'
    # strArgs = '-p ' + port + ' -script=ldap-*' # if want to using all of LDAP Script, open this command
    # LDAP brute force script <ldap-brute>
    nmScan_LDAP.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_LDAP[ip]['tcp']:
      thisDict = nmScan_LDAP[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
  
  # SSL Script Scan Function
  # using nmap script <ssl-heartbleed> & <ssl-poodle> to scan port 443 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def SSL(self, ip, ports, host):
    # >> nmap <ip> -p 443 -script=ssl-heartbleed,ssl-poodle || >> nmap <ip> -p 443 -script=ssl-*
    # NMAP variable in SSL func()
    nmScan_SSL = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=ssl-heartbleed,ssl-poodle'
    # strArgs = '-p ' + port + ' -script=ssl-*' # if want to using all of SSL Script, open this command
    # SSL script <ssl-heartbleed> & <ssl-poodle>
    nmScan_SSL.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_SSL[ip]['tcp']:
      thisDict = nmScan_SSL[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
  
  # rexec Script Scan Function
  # using nmap script <rexec-brute> to scan port 512 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def Rexec(self, ip, ports, host):
    # >> nmap <ip> -p 512 -script=rexec-brute
    # NMAP variable in Rexec func()
    nmScan_Rexec = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=rexec-brute'
    # rexec brute force script <rexec-brute>
    nmScan_Rexec.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_Rexec[ip]['tcp']:
      thisDict = nmScan_Rexec[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # rlogin Script Scan Function
  # using nmap script <rlogin-brute> to scan port 513 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def Rlogin(self, ip, ports, host):
    # >> nmap <ip> -p 513 -script=rlogin-brute
    # NMAP variable in Rlogin func()
    nmScan_Rlogin = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=rlogin-brute'
    # rlogin brute force script <rlogin-brute>
    nmScan_Rlogin.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_Rlogin[ip]['tcp']:
      thisDict = nmScan_Rlogin[ip]['tcp'][port]
      # print 'Port ' + str(port) + ': ' + thisDict['product'] + ', v' + thisDict['version']
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          #index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          #Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # MS-SQL Script Scan Function
  # using nmap script <ms-sql-brute> to scan port 1433 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def MSSQL(self, ip, ports, host):
    # >> nmap <ip> -p 1433 -script=ms-sql-brute
    # NMAP variable in MSSQL func()
    nmScan_MSSQL = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=ms-sql-brute'
    # strArgs = '-p ' + port + ' -script=ms-sql-*' # if want to using all of MS-SQL Script, open this command
    # MS-SQL brute force script <ms-sql-brute>
    nmScan_MSSQL.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_MSSQL[ip]['tcp']:
      thisDict = nmScan_MSSQL[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # Oracle Script Scan Function
  # using nmap script <oracle-brute> to scan port 1526 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def Oracle(self, ip, ports, host):
    # >> nmap <ip> -p 1526 -script=oracle-brute
    # NMAP variable in Oracle func()
    nmScan_Oracle = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=brute and oracle-*'
    # strArgs = '-p ' + port + ' -script=oracle-brute'
    # strArgs = '-p ' + port + ' -script=oracle-*' # if want to using all of Oracle Script, open this command
    # Oracle brute force script <oracle-brute>
    nmScan_Oracle.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_Oracle[ip]['tcp']:
      thisDict = nmScan_Oracle[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # MySQL Script Scan Function
  # using nmap script <mysql-brute> to scan port 3306 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def MySQL(self, ip, ports, host):
    # >> nmap <ip> -p 3306 -script=mysql-brute
    # NMAP variable in MySQL func()
    nmScan_MySQL = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=mysql-brute'
    # strArgs = '-p ' + port + ' -script=mysql-*' # if want to using all of MySQL Script, open this command
    # MySQL brute force script <mysql-brute>
    nmScan_MySQL.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_MySQL[ip]['tcp']:
      thisDict = nmScan_MySQL[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # PostgreSQL Script Scan Function
  # using nmap script <pgsql-brute> to scan port 5432 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def PgSQL(self, ip, ports, host):
    # >> nmap <ip> -p 5432 -script=pgsql-brute
    # NMAP variable in PgSQL func()
    nmScan_PgSQL = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=pgsql-brute'
    # PostgreSQL brute force script <pgsql-brute>
    nmScan_PgSQL.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_PgSQL[ip]['tcp']:
      thisDict = nmScan_PgSQL[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # VNC Script Scan Function
  # using nmap script <vnc-brute> to scan port 5800 || 5900 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def VNC(self, ip, ports, host):
    # >> nmap <ip> -p 5800,5900 -script=vnc-brute
    # NMAP variable in VNC func()
    nmScan_VNC = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=vnc-brute'
    # strArgs = '-p ' + port + ' -script=vnc-*' # if want to using all of VNC Script, open this command
    # VNC brute force script <vnc-brute>
    nmScan_VNC.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_VNC[ip]['tcp']:
      thisDict = nmScan_VNC[ip]['tcp'][port]      
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
  
  # IRC Script Scan Function
  # using nmap script <irc-brute> & <irc-sasl-brute> to scan port 6667 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def IRC(self, ip, ports, host):
    # >> nmap <ip> -p 6667 -script=irc-brute,irc-sasl-brute
    # NMAP variable in IRC func()
    nmScan_IRC = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=irc-brute,irc-sasl-brute'
    # strArgs = '-p ' + port + ' -script=irc-*' # if want to using all of IRC Script, open this command
    # IRC brute force script <irc-brute> & <irc-sasl-brute>
    nmScan_IRC.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_IRC[ip]['tcp']:
      thisDict = nmScan_IRC[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # Apache JServ Protocol Script Scan Function
  # using nmap script <ajp-brute> to scan port 8009 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def AJP(self, ip, ports, host):
    # >> nmap <ip> -p 8009 -script=ajp-brute
    # NMAP variable in AJP func()
    nmScan_AJP = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=ajp-brute'
    # strArgs = '-p ' + port + ' -script=ajp-*' # if want to using all of AJP Script, open this command
    # AJP brute force script <ajp-brute>
    nmScan_AJP.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_AJP[ip]['tcp']:
      thisDict = nmScan_AJP[ip]['tcp'][port]      
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
  
  # MongoDB Script Scan Function
  # using nmap script <mongodb-brute> to scan port 27017~27019 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def Mongo(self, ip, ports, host):
    # >> nmap <ip> -p 27017-27019 -script=mongodb-brute
    # NMAP variable in Mongo func()
    nmScan_Mongo = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=mongodb-brute'
    # strArgs = '-p ' + port + ' -script=mongodb-*' # if want to using all of MongoDB Script, open this command
    # MongoDB brute force script <mongodb-brute>
    nmScan_Mongo.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_Mongo[ip]['tcp']:
      thisDict = nmScan_Mongo[ip]['tcp'][port]
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
    
  # DRDA (ex:IBM DB2) Script Scan Function
  # using nmap script <drda-brute> to scan port 50000 & brute force crack password  
  # ip: ip address
  # ports: all ports of this service
  # host: host scan info, need to combine script scanning result
  def DRDA(self, ip, ports, host):
    #>> nmap <ip> -p 27017-27019 -script=drda-brute
    # NMAP variable in DRDA func()
    nmScan_DRDA = nmap.PortScanner()
    # Dictionary variable for script results (temporary)
    dictScript = {}
    # concat port & other nmap command flag
    strArgs = '-p ' + ports + ' -script=drda-brute'
    # strArgs = '-p ' + port + ' -script=drda-*' # if want to using all of DRDA Script, open this command
    # DRDA brute force script <drda-brute>
    nmScan_DRDA.scan(ip, arguments=strArgs)
    # List Script Name & Scanning result
    for port in nmScan_DRDA[ip]['tcp']:
      thisDict = nmScan_DRDA[ip]['tcp'][port]      
      if 'script' in thisDict: 
        print ('*Script executed on Port %s*' % (port))
        dictScript[str(port)] = {} # initail dictScript{}
        for thisScript in thisDict['script']:
          # index: nmScan[<IP>][protocols][<port>]['script'][<script name>]
          print ('Script Name ''%s'':%s' % (str(thisScript), thisDict['script'][str(thisScript)]))
          # Add new script scanning record into dictScript[<script name>]:<script result>
          dictScript[str(port)][str(thisScript)] = thisDict['script'][str(thisScript)]
      else:
        print ('*No Script executed on Port %s*' % (port))
    # Script results update into host(host is dictPortScan[ip][service_name], is an dictionary)
    host['scripts'] = dictScript
    
    return 0
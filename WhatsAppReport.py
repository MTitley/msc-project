
#Built from template @ https://github.com/sleuthkit/autopsy/blob/develop/pythonExamples/reportmodule.py
#With permission From author ( Brian Carrier [carrier <at> sleuthkit [dot] org] )


import os, time, json, re, codecs
import java.io

import xml.etree.cElementTree as et
from java.lang import System
from java.util.logging import Level
from org.sleuthkit.datamodel import TskData
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.report import GeneralReportModuleAdapter
from org.sleuthkit.autopsy.report.ReportProgressPanel import ReportStatus
from org.sleuthkit.autopsy.casemodule.services import FileManager


from java.io import File
from java.lang import Class
from java.lang import System
from java.sql import DriverManager, SQLException

from org.sleuthkit.autopsy.datamodel import ContentUtils
from org.sleuthkit.autopsy.ingest import DataSourceIngestModule

# Class responsible for defining module metadata and logic
class Account():
    app_version = ""
    inst_time = None
    pp_location = "Not Present"
    status = ""
    
    def getVersion(self):
        return self.app_version    
    def getTime(self):
        return self.inst_time
    def getPP(self):
        return self.pp_location
    def getStatus(self):
        return self.status
    
class WhatsAppReportModule(GeneralReportModuleAdapter):

    moduleName = "WhatsApp Report"
    registeredNumber = ""


    def getName(self):
        return self.moduleName
    
    def getNumber(self):
        return self.registeredNumber    

    def getDescription(self):
        return "Writes details of messenger"

    def getRelativeFilePath(self):
        return "whatsapp.txt"
    
    def timeStampConverter(self, timestamp):
        #Converts Epoch timestamp
        t = time.strftime("%a %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp / 1000.0))
        return t  
      

    def generateReport(self, baseReportDir, progressBar):
        # Open the output file.
        fileName = os.path.join(baseReportDir, self.getRelativeFilePath())
        
        report = codecs.open(fileName, 'w', encoding='utf-8')
        
        report.write("'")
        report.write("WHATSAPP REPORT\n")
        report.write("This report extracts content from the WhatsApp app\n")
        report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n")
        
        
        

        

        # Query the database for the files (ignore the directories)
        dataSources = Case.getCurrentCase().getDataSources()
        fileManager = Case.getCurrentCase().getServices().getFileManager()

        for dataSource in dataSources:
            msgstore = fileManager.findFiles(dataSource, 'msgstore.db','com.whatsapp/databases')
            msgstorewal = fileManager.findFiles(dataSource, 'msgstore.db-wal','com.whatsapp/databases')
            wadb = fileManager.findFiles(dataSource, 'wa.db','com.whatsapp/databases')
            wawal = fileManager.findFiles(dataSource, 'wa.db-wal','com.whatsapp/databases')
            washm = fileManager.findFiles(dataSource, 'wa.db-shm','com.whatsapp/databases')
            
            phone = fileManager.findFiles(dataSource, 'registration.RegisterPhone.xml', 'com.whatsapp/shared_prefs')
            account = fileManager.findFiles(dataSource, 'registration.VerifySms.xml', 'com.whatsapp/shared_prefs')
            timepref = fileManager.findFiles(dataSource, 'com.google.android.gms.measurement.prefs.xml', 'com.whatsapp/shared_prefs')
            verpref = fileManager.findFiles(dataSource, 'com.whatsapp_preferences_light.xml', 'com.whatsapp/shared_prefs')
            pp = fileManager.findFiles(dataSource, 'me.jpg', 'com.whatsapp/files')
            status = fileManager.findFiles(dataSource, 'status', 'com.whatsapp/files')
            
        ###VAR LIST###
        mess_list = []
        contact_list = []
        call_list = []
        convo_list = []
        gpart_list = []
        jid_list = []
        b_users_list = []
        rem_user_list = []
        broads_list = []
        
        
        accountone = Account()
        
        ################################################    USER DATA COLLECTOR  ###################################################
        for file in verpref:
            verpref_path = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()))
            ContentUtils.writeToFile(file, File(verpref_path))
            
            xmlcontent = et.parse(verpref_path)
            root = xmlcontent.getroot()            
            for string in root.findall('string'):
                if string.get('name') == "version":
                    accountone.app_version = string.text
                if string.get('name') == "my_current_status":
                    accountone.status = string.text
        
        for file in pp:
            #Assigns path if profile picture exists
            accountone.pp_location = "/data/com.whatsapp/files/me.jpg"
        for file in status:
            #Assigns path if status is present
            accountone.status = "status file is present"
            
        if float(accountone.getVersion().replace(".","")) >= 219175:
            #Checks application is compatible with tool
            
            for file in timepref:
                timepref_path = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()))
                ContentUtils.writeToFile(file, File(timepref_path))
                
                xmlcontent = et.parse(timepref_path)
                root = xmlcontent.getroot()            
                for lon in root.findall('long'):
                    #Find time the application was installed
                    if lon.get('name') == "first_open_time":
                        accountone.inst_time = float(lon.get('value'))
                
                
            report.write("APP DATA\n")
            #Write profile to report
            
            report.write("+ App Version: " + accountone.getVersion() + "\n")
            report.write("+ App first opened: " + self.timeStampConverter(accountone.getTime()) + "\n")
            os.remove(timepref_path)  
            os.remove(verpref_path)  
            report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n")    
            report.write("USER DATA\n")
            xmlcontent = ""
            for file in phone:
                pathtophone = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()) + ".db")
                ContentUtils.writeToFile(file, File(pathtophone))

                xmlcontent = et.parse(pathtophone)
                root = xmlcontent.getroot()
                
                #Get phone number and country code
                for string in root.findall('string'):
                    if string.get('name') == "com.whatsapp.registration.RegisterPhone.phone_number":
                        mobnum = string.text
                    if string.get('name') == "com.whatsapp.registration.RegisterPhone.country_code":
                        code = string.text
                registered_phone = code + mobnum
                report.write("+ Registered phone number: " + registered_phone + ".\n")
            os.remove(pathtophone)  
            
            xmlcontent = ""
            for file in account:
                pathtoaccount = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()) + ".db")
                ContentUtils.writeToFile(file, File(pathtoaccount))
                
                xmlcontent = et.parse(pathtoaccount)
                root = xmlcontent.getroot()
                regtime = ""
                for lon in root.findall('long'):
                    if lon.get('name') == "com.whatsapp.registration.VerifySms.call_countdown_end_time":
                        regtime = float(lon.get('value'))
             
              
            report.write("+ Account Registered: " + self.timeStampConverter(regtime) + ".\n")  
            report.write("+ Profile Picture: " + accountone.getPP() + ".\n")
            
            os.remove(pathtoaccount)                    
            
            for file in msgstorewal:
                messwalpath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(messwalpath))                 
            for file in msgstore:
                messpath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(messpath))                
                
                try:
                    #Open database
                    Class.forName("org.sqlite.JDBC").newInstance()
                    dbConn = DriverManager.getConnection("jdbc:sqlite:%s"  % messpath)
                except SQLException as e:
                    report.write("Cant open db/wal/shm \n")
                
                    
                #Get list of jids
                try:
                    jidstmt = dbConn.createStatement()
                    jids = jidstmt.executeQuery('SELECT _id, user FROM jid;')
                except:
                    report.write("Cant get used jids\n")
                    
                while jids.next():
                    try:
                        _id = jids.getString("_id")
                        user = jids.getString("user")
                        j = [_id, user]
                        jid_list.append(j)
                    except:
                        report.write("Can't allocate jids.\n")
            
            
                try:
                    hisstmt = dbConn.createStatement()
                    history = jidstmt.executeQuery('SELECT jid, gjid, timestamp FROM group_participants_history;')
                except:
                    report.write("Cant get used history\n")
                    
                while history.next():
                    #Writes users no longer present in conversations
                    rem_user_list.append([history.getString('jid'),history.getString('gjid'),history.getString('timestamp')])
                    
                
            
            jidstmt.close() 
            hisstmt.close()
            os.remove(messpath)
            os.remove(messwalpath)
            dbConn.close()
            ################################################    CONTACT COLLECTOR    ##################################################
            for file in wadb:
                dbPath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(dbPath))
            
            for file in wawal:
                walPath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(walPath)) 
                
            for file in washm:
                shmPath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(shmPath))     
                
                
            ##################################################################################################################################    
            report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n")    
            report.write("CONTACTS ON DEVICE.\n")    
            
            
            try:
                #Open database
                Class.forName("org.sqlite.JDBC").newInstance()
                dbConn = DriverManager.getConnection("jdbc:sqlite:%s"  % dbPath)
            except SQLException as e:
                report.write("Cant open db/wal/shm \n")
              
            try:
                statement = dbConn.createStatement()
                contacts = statement.executeQuery('SELECT * FROM wa_contacts')
            except SQLException as e:
                report.write("Cant query first db \n")
                report.write(e.getMessage() + "\n")
            
            while contacts.next():
                #Get details of all contacts on the application
                try:
                    jid = contacts.getString("jid")
                    number = contacts.getString("number")
                    disp_name = contacts.getString("display_name")
                    contact = [jid,number,disp_name]
                    contact_list.append(contact)
                    photoname = jid + ".j"
                    try:
                        #Locates profile photo if present
                        contactphoto = fileManager.findFiles(dataSource, photoname, 'com.whatsapp/files/Avatars')
                        contactphoto = "is at /data/com.whatsapp/files/Avatars" + photoname 
                    except:
                        contactphoto = "not found"
                        
                    report.write("+ Name: " + disp_name + "    Number: " + number + "    ID: " + jid + "    Profile photo: " + contactphoto + "\n")
                except:
                    pass
                
            statement.close()
            
            try:
                b_statement = dbConn.createStatement()
                blocked = statement.executeQuery('SELECT * FROM wa_block_list')
            except SQLException as e:
                report.write("Cant query first db \n")
                report.write(e.getMessage() + "\n")
            while blocked.next():
                #Gets details of blocked users
                try:
                    b_jid = blocked.getString('jid')
                    for u in contact_list:
                        if u[0] == b_jid:
                            b_users_list.append([u[1], u[2]])
                except:
                    report.write("Can't get blocked user.\n")
                
            blocked.close()
            dbConn.close()
            os.remove(dbPath)
            
            
            ##################################################################################################################################
            mess_list = []
            for file in msgstorewal:
                messwalpath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(messwalpath))                 
                
            for file in msgstore:
                ts = ""
                messpath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(messpath))                 
                
                try:
                    #Open database
                    Class.forName("org.sqlite.JDBC").newInstance()
                    dbConn = DriverManager.getConnection("jdbc:sqlite:%s"  % messpath)
    
    
                    
                except SQLException as e:
                    report.write("Cant open db \n")
                    break
##############################################################################################################################################################################                
##############################################################################################################################################################################
##############################################################################################################################################################################    
    
                try:
                    stmt = dbConn.createStatement()
                    messages = stmt.executeQuery('SELECT key_remote_jid, data, key_from_me, timestamp, media_mime_type, media_caption, _id, media_hash, media_wa_type, status, edit_version, hex(thumb_image) FROM messages WHERE key_remote_jid != "status@broadcast";')
                except SQLException as e:
                    report.write("Cant query db \n")
                    report.write(e.getMessage())
                    break
                
                #Gets message details
                while messages.next():
                    try:
                        thumb = ""
                        t = ""
                        att_type = ""
                        mesageid = messages.getString("_id")
                        jid  = messages.getString("key_remote_jid")
                        data = messages.getString("data")
                        sendrec = messages.getString("key_from_me")
                        timestamp = messages.getString("timestamp")
                        mtype = messages.getString("media_mime_type")
                        caption = messages.getString("media_caption")
                        mhash = messages.getString("media_hash")
                        medwatype = messages.getString("media_wa_type")
                        status = messages.getString('status')
                        edit_version = messages.getString('edit_version')
                        thumb_image = messages.getString('hex(thumb_image)')
                        messagetype = ""
                        
                        if medwatype == "1" or medwatype == "3" or medwatype == "2" or medwatype == "13" or medwatype == "9":
                            #IF message contains an attachment
                            convert = []
                            #Convert from hex
                            thumbhex = [thumb_image[i:i+2] for i in range(0,len(thumb_image),2)]
                            for h in thumbhex:
                                h = int(h, 16)
                                if h >= 32 and h <= 126:
                                    h = hex(h).replace("0x","")
                                    h = h.decode("hex")
                                    convert.append(h)
                                else:
                                    pass
                            t = ''.join(convert)
                            t = re.findall(r"\/WhatsApp.+\w+\.\w+\ww",t)
                            
                        
                            
                        if medwatype == "1":
                            if sendrec == "1":
                                messagetype = "sent_image"
                            elif sendrec == "0":
                                messagetype = "rec_image"
                        elif medwatype == "3":
                            messagetype = "video"
                        elif medwatype == "2":
                            messagetype = "voice"
                        elif medwatype == "13":
                            messagetype = "gif"
                        elif medwatype =="9":
                            messagetype = "document"

      
                        if edit_version == "7":
                            messagetype = "deleted"
                                
                        thumb = t
                           
                        try:
                            mtype = mtype.split("/")[0]
                        except:
                            mtype = "No type"
                        
                        mess = [jid, data,sendrec,float(timestamp),mtype,caption, thumb, mhash, status, messagetype, mesageid]
                        
                        if mess[0].endswith('@broadcast') or mess[0] == "-1" or mess[8] == "6":
                            #Don't write broadcast or status messages
                            pass
                        else:
                            
                            mess_list.append(mess)
                        
                    except SQLException as e:
                        report.write("\n Loop Error \n")
                        
                # Clean up
                stmt.close()
                
##############################################################################################################################################################################                
##############################################################################################################################################################################
##############################################################################################################################################################################
                
                #Get call details and write to array
                try:
                    stmt = dbConn.createStatement()
                    calls = stmt.executeQuery('SELECT from_me, timestamp, duration, video_call, jid_row_id FROM call_log;')
                except SQLException as e:
                    report.write("Cant query call db \n")
                    report.write(e.getMessage())
                    break
                
                while calls.next():
                    try:
                        from_me  = calls.getString("from_me")
                        timestamp = calls.getString("timestamp")
                        duration = calls.getString("duration")
                        video_call = calls.getString("video_call")
                        row = calls.getString("jid_row_id")
                        for jid in jid_list:
                            if jid[0] == row:
                                row = jid[1]
                        for cont in contact_list:
                            if cont[0].startswith(row):
                                row = cont[2]
                                                      
                        
                        call = [from_me, timestamp, duration, video_call, row]
                        call_list.append(call)
                        
                    except SQLException as e:
                        report.write("\n Loop Error \n")            
                
                stmt.close()
                
                
                #Write details to report
                report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n")    
                ##########################################################################################################################################
                report.write("BLOCKED USERS\n")
                for b in b_users_list:
                    report.write("+ " + b[1] + " (" + b[0] + ").\n")
                
                ##########################################################################################################################################
                ##########################################################################################################################################
                report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n")    
                report.write("BROADCASTS\n")
                
                try:
                    broadstmt = dbConn.createStatement()
                    broads = broadstmt.executeQuery('SELECT * FROM messages WHERE status == 4;')
                    report.write("got stuff\n")
                except SQLException as e:
                    report.write("Cant ex broad query" + e.getMessage() + "\n")
                    
                b_keys = []   
                
                
                while broads.next():
                    b_keys.append(broads.getString('key_id'))
                    broads_list.append([broads.getString('key_remote_jid'),broads.getString('key_id'),broads.getString('data'),broads.getString('timestamp')])
                b_keys = list(dict.fromkeys(b_keys)) ##delete duplicates
                
                report.write(str(broads_list) + "\n")
                for k in b_keys:
                    report.write(" + " + self.timeStampConverter(float(broads_list[0][3])) + " Broadcast '" + broads_list[0][2] + "' sent to: \n")
                    for b in broads_list:
                        if b[1] == k:
                            for u in contact_list:
                                if u[0] == b[0] and b[0].endswith("@broadcast") == False:
                                    report.write(" ++ To: " + u[2] + "(" + u[1] + ").\n") 
                                
                broadstmt.close()
                broads.close()
                
                ##########################################################################################################################################
                ##########################################################################################################################################
                
                
                report.write("\n")
                report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n")    
                report.write("LIST OF CONVERSATIONS\n")
                
                try:
                    stmt = dbConn.createStatement()
                    stmtii = dbConn.createStatement()
                    calls = stmt.executeQuery('SELECT key_remote_jid, subject, _id FROM chat_list;')
                    g_parts = stmtii.executeQuery('SELECT gjid, jid FROM group_participants;')
                except SQLException as e:
                    report.write("Cant query call db \n")
                    report.write(e.getMessage())
                    break
                
                while g_parts.next():
                    try:
                        gjid = g_parts.getString("gjid")
                        jid = g_parts.getString("jid")
                        g = [gjid,jid]
                        gpart_list.append(g)
                    except:
                        report.write("\n Loop Error \n")
                        
                while calls.next():
                    try:
                        jid  = calls.getString("key_remote_jid")
                        subject = calls.getString("subject")
                        _id = calls.getString("_id")
                                           
                        convo = [jid, subject, _id]
                        convo_list.append(convo)
                        
                    except SQLException as e:
                        report.write("\n Loop Error \n")  
                        
                for convo in convo_list:
                    
                    if convo[0].endswith("@g.us"):
                        removed = ""
                        temp_parts = []
                        for group_participant in gpart_list:
                            if group_participant[0] == convo[0]:
                                for contact in contact_list:
                                    if contact[0] == group_participant[1]:
                                        temp_parts.append(contact[2])
                        for r in rem_user_list:
                            if r[1] == convo[0]:
                                for u in contact_list:
                                    if u[0] == r[0]:
                                        r_u = (u[1] + "(" + u[2] + ")")
                                        break
                                removed = removed + (", " + r_u)
                                
                        if removed == "":
                            report.write("+ GROUP CHAT. Subject: " + convo[1] + " --- Participants: " + ', '.join(temp_parts) + ". \n")
                        else:
                            report.write("+ GROUP CHAT. Subject: " + convo[1] + " --- Participants: " + ', '.join(temp_parts) + ". --- Removed users: " + removed + " .\n")
                        
                    else:
                        report.write("+ CHAT. Recipient: " + convo[0][:-15] + ".\n")
                dbConn.close()
                stmt.close()
                os.remove(messpath)
                report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n")    
                ##########################################################################################################################################            
                
                
                
                report.write("CALLS\n")            
                for call in call_list:
                    tofrom = ""
                    if call[0] == "1":
                        tofrom = "to"
                    else:
                        tofrom = "from"
                    if video_call == "1":
                        report.write("+ " + self.timeStampConverter(float(call[1])) + " --- Video call " + tofrom + " " + str(call[4]) + ". --- Duration: " + call[2] + " seconds. \n")
                    else:
                        report.write("+ " + self.timeStampConverter(float(call[1])) + " --- Voice call " + tofrom + " " + str(call[4]) + ". --- Duration: " + call[2] + " seconds. \n")
                                              
    
     
                report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n")    
                ##########################################################################################################################################
                report.write("MESSAGES\n")
                
                
                
                for conversation in convo_list:
                    if conversation[0].endswith('@g.us'):
                        report.write("\nGROUP CHAT: " + conversation[1] + ".\n")
                    else:
                        for contact in contact_list:
                            if contact[0] == conversation[0]:
                                report.write("\nCONVERSATION WITH " + contact[2] + ".\n")
                    
                        
                    for message in mess_list:
                        if message[1] is not None:
                            message[1] = message[1].encode("utf-8")
                        if message[0] == conversation[0]:
                            sender = ""
                            if message[2] == "1":
                                sender = "User"
                            
                            else:
                                for contact in contact_list:
                                    if contact[0] == message[0]:
                                        sender = str(contact[2])
                                    else:
                                        pass
                                    
                                                   
                            if message[8] == "6":
                                ###NOTIFICATION
                                report.write("+ "+ self.timeStampConverter(float(message[3])) + "    --- NOTIFICATION: Action executed by: " + sender + ".\n")
                            if message[9] == "deleted":
                                ###DELETED
                                report.write("+ " + self.timeStampConverter(float(message[3])) +"    --- From " + sender + "    --- Message: #DELETED#" + ".\n")
                            
                            if message[7] is not None:
                                
                                try:
                                    report.write("+ " + self.timeStampConverter(float(message[3])) +"    --- From " + sender + " --- Message: '" + message[5] + "'. Attachment stored at: " + str(message[6]) + "\n") ##message[6] causing unicode error
                                except:
                                    report.write("+ " + self.timeStampConverter(float(message[3])) +"    --- From " + sender + " --- No message. Attachment stored at: " + str(message[6]) + "\n") ##message[6] causing unicode error
                                
                            else:
                                if message[1] is not None:
                                    a = (''.join([i if ord(i) <= 126 and ord(i) >= 32 else '*' for i in message[1]])).replace("****************","*")
                                try:
                                    report.write("+ " + self.timeStampConverter(float(message[3])) +"    --- From " + sender + "    --- Message: '" + str(a) + "'.\n")
                                except:
                                    #String includes Non-Ascii
                                    report.write("++++++++ " + self.timeStampConverter(float(message[3])) +"    --- From " + sender + " MESSAGE NOT AVAILABLE.\n")
                    
                  
                    
    
            report.close()
            
        else:
            report.write("WhatsApp Version not compatible. Version 2.19.175 or higher required.\n")
            report.close()
        
        
        # Add the report to the Case, so it is shown in the tree
        Case.getCurrentCase().addReport(fileName, self.moduleName, "WhatsApp TXT")
    
        progressBar.complete(ReportStatus.COMPLETE)


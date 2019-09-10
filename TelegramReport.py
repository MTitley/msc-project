

#Built from template @ https://github.com/sleuthkit/autopsy/blob/develop/pythonExamples/reportmodule.py
#With permission From author ( Brian Carrier [carrier <at> sleuthkit [dot] org] )


import os, time, json, base64, re, struct, array
import java.io
import xml.etree.cElementTree as et
#from jhplot.io import *
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
class TelegramReportModule(GeneralReportModuleAdapter):

    moduleName = "Telegram Report"

    def getName(self):
        return self.moduleName
    
    def getNumber(self):
        return self.registeredNumber    

    def getDescription(self):
        return "Writes details of Telegram Messenger"

    def getRelativeFilePath(self):
        return "TelegramReport.txt"
    
    def Convert(self, string):
        ##takes hex string and reverses
        uid = [string[i:i+2] for i in range(0, len(string), 2)]
        uid.reverse()
        uid = ''.join(uid)
        uid = int(uid, 16)
        return uid
    
    def timeStampConverter(self, timestamp):
        t = time.strftime("%a %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp / 1000.0))
        return t      
    
    def generateReport(self, baseReportDir, progressBar):
        # Open the output file.
        fileName = os.path.join(baseReportDir, self.getRelativeFilePath())
        
        
        report = open(fileName, 'w')
        report.write("TELEGRAM REPORT\n")
        report.write("This report extracts content from the Telegram Messenger app\n")
        report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
        
        
        
        
        

        

        # Query the database for the files (ignore the directories)
        dataSources = Case.getCurrentCase().getDataSources()
        fileManager = Case.getCurrentCase().getServices().getFileManager()

        for dataSource in dataSources:
            msgstore = fileManager.findFiles(dataSource, 'cache4.db','org.telegram.messenger/files/')
            msgstorewal = fileManager.findFiles(dataSource, 'cache4.db-wal','org.telegram.messenger/files/')
            msgstoreshm = fileManager.findFiles(dataSource, 'cache4.db-shm','org.telegram.messenger/files/')
            
            userconfig = fileManager.findFiles(dataSource, 'userconfing.xml','org.telegram.messenger/shared_prefs')
            #media = fileManager.addLocalFilesDirs('media/0/telegram')
            
            
        
            
        ###VAR LIST###
        mess_list = []
        user_list = []
        dialog_list = []
        chatgroup_list = []
        secret_list = []
        enc_list = []
        settings_list = []
        for file in userconfig:
            confingpath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
            ContentUtils.writeToFile(file, File(confingpath)) 
            
            
            xmlcontent = et.parse(confingpath)
            root = xmlcontent.getroot() 
            
            for string in root.findall('string'):
                if string.get('name') == "user":
                    user = str(base64.b64decode(string.text))
            
            ###Below functions gives ASCII characters but includes obsolete chars. - job is to check if Name is always at certain position within string
            
            #for u in user:
                #if ord(u) >= 32 and ord(u) <= 126:
                    #report.write( u + "\n")
            
            
            
        os.remove(confingpath)         
        for file in msgstore:
            if file.getParentPath() == "/data/org.telegram.messenger/files/":
                dbPath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(dbPath))   
                
        for file in msgstorewal:
            if file.getParentPath() == "/data/org.telegram.messenger/files/":        
                dbwal = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(dbwal))   
                
        for file in msgstoreshm:
            if file.getParentPath() == "/data/org.telegram.messenger/files/":    
                dbshm = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getName()))
                ContentUtils.writeToFile(file, File(dbshm))   
        try:
            #Open database
            Class.forName("org.sqlite.JDBC").newInstance()
            dbConn = DriverManager.getConnection("jdbc:sqlite:%s"  % dbPath)
        except SQLException as e:
            report.write("Cant open cache4.db.\n")
        
            
        try:
            userstatement = dbConn.createStatement()
            users = userstatement.executeQuery('SELECT uid, name, data FROM users WHERE status IS NOT 0;')
        except SQLException as e:
            report.write("Cant query first db \n")
            report.write(e.getMessage() + "\n") 
            
        
        while users.next():
            names = users.getString('name').split(";;;")
            c_name = names[0]
            u_name = names[1]
            d = users.getString('data')
            ##blob extraction
            content = ''.join([i if ord(i) <= 126 and ord(i) >= 32 else '.' for i in d])
            content = re.findall(r"\d{7,15}",content)
            
            if len(content) > 0:
                user_list.append([users.getString('uid'),c_name, u_name,content[0]])
            
        userstatement.close()
        
        try:
            encstatement = dbConn.createStatement()
            enc_chats = encstatement.executeQuery('SELECT name FROM enc_chats;')
        except SQLException as e:
            report.write("Cant query enc db \n")
            report.write(e.getMessage() + "\n") 
            
        
        while enc_chats.next():
            names = enc_chats.getString('name').split(";;;")
            c_name = names[0]
            u_name = names[1]
            
            
            enc_list.append([c_name, u_name])
            
        encstatement.close()        
        
        report.write("CONTACTS\n")
        for user in user_list:
            report.write(" + " + user[0] + " -- Name: " + user[1] + " -- Username: " + user[2] + " -- Phone: " + user[3] + ".\n")
        
        
        ##############################################################################################################################
        ##############################################################################################################################
        #get group chats and channels
        
        try:
            set_statement = dbConn.createStatement()
            settings = set_statement.executeQuery('SELECT uid, hex(info) FROM chat_settings_v2')
        except SQLException as e:
            report.write("Cant query first db \n")
            report.write(e.getMessage() + "\n")
            
        while settings.next():   
            
            if settings.getString('hex(info)')[:4] == "745C":
                t = "Channel"
            else:
                t = "Group"
            settings_list.append([settings.getString('uid'), t])
                               
        set_statement.close()        
        
        ##############################################################################################################################
        ##############################################################################################################################
        
        #Get list of chats (dialogs)
        #
        try:
            dialogstatement = dbConn.createStatement()
            dialogs = dialogstatement.executeQuery('SELECT did FROM dialogs')
        except SQLException as e:
            report.write("Cant query first db \n")
            report.write(e.getMessage() + "\n")
            
        while dialogs.next():   
            for s in settings_list:
                if dialogs.getString('did').replace("-","") == str(s[0]):
                    dialog_list.append([dialogs.getString('did'), s[1]])
                               
        dialogstatement.close()
        
        ##############################################################################################################################
        ##############################################################################################################################
        #get group chats and channels
        
        try:
            cc_statement = dbConn.createStatement()
            cc = cc_statement.executeQuery('SELECT uid, name, data FROM chats;')
        except SQLException as e:
            report.write("Cant query first db \n")
            report.write(e.getMessage() + "\n")
            
        while cc.next():   
            chatgroup_list.append([cc.getString('uid'),cc.getString('name'),cc.getString('data')])
                               
        cc_statement.close()        
        
        ##############################################################################################################################
        ##############################################################################################################################
        
        
        try:
            statement = dbConn.createStatement()
            messages = statement.executeQuery('SELECT date, hex(data), out, uid FROM messages')
        except SQLException as e:
            report.write("Cant query first db \n")
            report.write(e.getMessage() + "\n")
            
        while messages.next():
            decoded_message = []
            conv = ""
            uid = ""
            mtype = ""
            inter = ""
            dur = "0"
            conn = "n/a"   
            raw_mess = ""
            try:
                
                date = messages.getString("date")
                message = messages.getString("hex(data)")
                out = messages.getString("out")
                conv = messages.getString("uid")
                if out == "1":
                    out = "sent"
                else:
                    out = "received"
                    
                if message[:8] == "F6A1199E":
                    if message[32:40] == "BBE5D0BA":
                        mtype = "channel created"
                        
                                               
                        
                        
                        
                    if message[32:40] == "6DBCB19D":
                        mtype = "call"
                        for u in user_list:
                            if str(u[0]) == str(self.Convert(message[24:32])):
                                uid = u[1]
                            elif str(u[0]) == str(self.Convert(message[40:48])):
                                inter = u[1]
                        date = self.Convert(message[40:48])
                        conn = str(message[65:66])
                        if conn == "3":
                            conn = "connected"
                            dur = str(self.Convert(message[96:104]))
                        elif conn == "1":
                            conn = "did not connect"
                        
                        
                             
                                
                    if message[32:40] == "32E5DDBD":
                        mtype = "channel created by another"  
                        #for u in user_list:
                            #if str(u[0]) == str(self.Convert(message[24:32])):
                        
                        
                    if message[24:32] == "32E5DDBD":
                        mtype = "channel interaction"
                        mess_size = int(str(message[56:58]),16)
                        raw_mess = message[58:(58 + (mess_size*2))]
                        if raw_mess is not "":
                            raw_mess = raw_mess.decode("hex") 
                            
                            
                            
                            
                        
                if message[:8] == "3DB4F944":
                    if message[32:40] == "BBE5D0BA":
                        mtype = "group message"
                        uid = [(message[24:32])[i:i+2] for i in range(0, len(message[24:32]), 2)]
                        uid.reverse()
                        uid = ''.join(uid)
                        uid = int(uid, 16)
                        for u in user_list:
                            if str(u[0]) == str(uid):
                                uid = u[1]   
                        mess_size = int(str(message[56:58]),16)
                        if mess_size == 0 and uid:
                            pass ######################################################---------------------------get photo here
                        raw_mess = message[58:(58 + (mess_size*2))]
                        if raw_mess is not "":
                            raw_mess = raw_mess.decode("hex")        
                                
                                
                    if message[32:40] == "6DBCB19D":
                        mtype = "chat message"    
                        uid = self.Convert(message[24:32])
                                           
                        for u in user_list:
                            if str(u[0]) == str(uid):
                                uid = u[1]
                            elif str(u[0]) == str(self.Convert(message[40:48])):
                                inter = u[1]
                        mm = message[56:58]
                        mess_size = int(str(message[56:58]),16)
                        if mess_size == 0 and uid:
                            pass ######################################################---------------------------get photo here
                        raw_mess = message[58:(58 + (mess_size*2))]
                        if raw_mess is not "":
                            raw_mess = raw_mess.decode("hex")
                                     
                        

                    if message[24:32] == "32E5DDBD":
                            mtype = "channel message" 
                            mess_size = int(str(message[48:50]),16)
                            raw_mess = message[50:(50 + (mess_size*2))]
                            if raw_mess is not "":
                                raw_mess = raw_mess.decode("hex")
                                
                                
                            
                if message[:8] == "FA555555":
                    mtype = "secure chat message"
                    uid = [(message[48:56])[i:i+2] for i in range(0, len(message[48:56]), 2)]
                    uid.reverse()
                    uid = ''.join(uid)
                    uid = int(uid, 16)
                    for u in user_list:
                        if str(u[0]) == str(self.Convert(message[32:40])):
                            uid = u[1]
                        elif str(u[0]) == str(self.Convert(message[48:56])):
                            inter = u[1]
                        
                    mess_size = int(str(message[64:66]),16)
                    raw_mess = message[66:(66 + (mess_size*2))]
                    if raw_mess is not "":
                        raw_mess = raw_mess.decode("hex")
                        
            except SQLException as e:
                report.write("Can't perform" + e.getMessage() + ".\n") 
                
            if raw_mess == "":
                raw_mess =  "#media unobtainable#"
            if messages.getString('uid') != "777000":
                if mtype == "secure chat message":
                    secret_list.append([date,raw_mess,mtype, conv, inter, conn, dur, uid])
                else:
                    mess_list.append([date, raw_mess, mtype, conv, inter, conn, dur, uid])
        
        
        report.write("-----------------------------------------------------------------------------------------------------------------------------------------------\n")
        report.write("-----------------------------------------------------------------------------------------------------------------------------------------------\n")
        
                
        
                
        report.write("\n\n CHANNELS CREATED\n")        
        for m in mess_list:
            if m[2] == "channel interaction":
                report.write(" + " + "Channel: " + m[1] + "\n")
                
        #report.write("\n\n CHANNEL MESSAGES\n")        
        #for m in mess_list:
            #if m[2] == "channel message":
                #report.write(" + " + "Message: " + m[1] + "\n")
                
        
        
        
        report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
        report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
        report.write("MESSAGES\n")
        for d in dialog_list:
            found = False
            for u in user_list:
                if d[0] == u[0]:
                    report.write("\nConversation with: " + u[1] + ".\n")
                    found = True
                    for m in mess_list:
                        if m[3] == d[0]:
                            
                            if m[2] == "call":
                                report.write(" + " + self.timeStampConverter(float(m[0])) + "Call from: " + str(m[7]) + " To: " + str(m[4]) + ". ---- Call " + str(m[5]) + ". Duration: " + str(m[6]) + " seconds. \n")
                            else:
                                report.write(" + " + self.timeStampConverter(float(m[0])) + m[7] + " sent: " + m[1] + "...\n")
            for c in chatgroup_list:
                if d[0].replace("-","") == c[0]:
                    report.write("\n" + d[1] + ": " + c[1] + ".\n")
                    found = True
                    
                    for m in mess_list:
                        if m[3] == d[0]:
                            if m[2] == "channel interaction":
                                report.write(" + "  + self.timeStampConverter(float(m[0])) + " Channel Event: " + m[1] + ".\n")
                            else:
                                report.write(" + "  + self.timeStampConverter(float(m[0])) + " " + m[1] + "...\n")                    
                    
            if not found:
                report.write("\n -- Secret Chat ID: " + d[0] + "-- \n")
                report.write("     -- See Messages Below --\n")
                
        report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
        report.write("SECRET MESSAGES\n")
        for e in enc_list:
            report.write("Encrypted Conversation with: " + e[0] + ".\n")
            for m in secret_list:
                if e[0] == m[4] or e[0] == m[7]:
                    report.write(" + " + self.timeStampConverter(float(m[0])) +  "From: " + m[7] + " To: " + m[4] + " Message: " + m[1] + "\n") #+m[1] + "\n")        
                
            
            
           
        statement.close()
        #report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
        #report.write("CHANNELS.\n")
        
        #try:
            #statement = dbConn.createStatement()
            #chats = statement.executeQuery('SELECT * FROM chats')
        #except SQLException as e:
            #report.write("Cant query first db \n")
            #report.write(e.getMessage() + "\n")
            
            
            
        #report.write(str(type(chats)))
        #while chats.next():
            #report.write("Found.\n")
            #try:
                #uid = chats.get('uid')
                #name = chats.get('name')
                #report.write("Channel: " + uid + ". Name: " + name + ".\n")                
            #except:
                #report.write("Can't get channel info.\n")
        
        #statement.close()
        #dbConn.close()
        #os.remove(dbPath)
        #try:
            #os.remove(dbwal)
        #except:
            #pass
        
        #try:
            #os.remove(dbshm)
        #except:
            #pass        
        
                
            
            
            
            
            
        report.close()

        # Add the report to the Case, so it is shown in the tree
        Case.getCurrentCase().addReport(fileName, self.moduleName, "Telegram TXT")

        progressBar.complete(ReportStatus.COMPLETE)

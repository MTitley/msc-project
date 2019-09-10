#!/usr/bin/env python
# -*- coding: utf8 -*-


#Built from template @ https://github.com/sleuthkit/autopsy/blob/develop/pythonExamples/reportmodule.py
#With permission From author ( Brian Carrier [carrier <at> sleuthkit [dot] org] )



import os, time, json, re, ast 

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
class MessengerReportModule(GeneralReportModuleAdapter):

    moduleName = "Messenger Report"

    def getName(self):
        return self.moduleName

    def getDescription(self):
        return "Writes details of messenger"

    def getRelativeFilePath(self):
        return "messenger.txt"
    
    #converts from Epoch time
    def timeStampConverter(self, timestamp):
        t = time.strftime("%a %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp / 1000.0))
        return t    

    def generateReport(self, baseReportDir, progressBar):

        # Open the output file.
        fileName = os.path.join(baseReportDir, self.getRelativeFilePath())
        report = open(fileName, 'w')

        report.write("FACEBOOK MESSENGER REPORT\n")
        report.write("This report extracts content from the Messenger app\n")
        report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n")

        # Query the database for the files (ignore the directories)
        dataSources = Case.getCurrentCase().getDataSources()
        fileManager = Case.getCurrentCase().getServices().getFileManager()

        for dataSource in dataSources:
            files = fileManager.findFiles(dataSource, 'threads_db2','databases')
            fb_prefs = fileManager.findFiles(dataSource, 'prefs_db','com.facebook.orca/databases')
            


        # Setup the progress bar
        progressBar.setIndeterminate(False)
        progressBar.start()
        progressBar.setMaximumProgress(len(files))

        users_array = []
        conv_array = []
        message_array = []
        part_array = []
        call_array = []
        loggedun = ""
        
        
        for file in files:
            
            lclDbPath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()) + ".db")
            ContentUtils.writeToFile(file, File(lclDbPath))
            
            try:
                #Open database
                Class.forName("org.sqlite.JDBC").newInstance()
                dbConn = DriverManager.getConnection("jdbc:sqlite:%s"  % lclDbPath)
    
    
                
            except SQLException as e:
                report.write("Cant open database \n")
                
    
       ##################### USERS ARRAY CONSTRUCTION ###################### 
            #Set up an array to store the details of each user
            try:
                stmt = dbConn.createStatement()
                users = stmt.executeQuery('SELECT * FROM thread_users')
            except SQLException as e:
                report.write("Cant query db 1\n")
                report.write(e.getMessage())
            
            while users.next():
                try:
                    username  = users.getString("username")
                    userkey = users.getString("user_key")
                    name = users.getString("name")
                except:
                    report.write("Can't get values")
                    
                us = [username, userkey, name]
                users_array.append(us)   
        
        stmt.close()
        dbConn.close()
        os.remove(lclDbPath)        
        
        
        ####################################################################
        
        
        for file in fb_prefs:
            #Write details of the currently logged in user
            localpath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()) + ".db")
            ContentUtils.writeToFile(file, File(localpath))
            
            uid = ""
            version = ""
            
            try:
                Class.forName("org.sqlite.JDBC").newInstance()
                dbConn = DriverManager.getConnection("jdbc:sqlite:%s" % localpath)
            except SQLException as e:
                report.write("Can't open prefs_db")
            
            try:
                stmt = dbConn.createStatement()
                user_data = stmt.executeQuery('SELECT * FROM preferences WHERE key = "/prefs_user_id" OR key = "/settings/app_version_name_current"')      
            except:
                report.write("Statement failed\n")
                
            while user_data.next():
                try:
                    if user_data.getString('key') == "/prefs_user_id":
                        uid = user_data.getString('value')
                        
                    else:
                        version = user_data.getString('value')
                except:
                    report.write("Can't get values\n")
            run = ""
            rn = ""
            #get username and userid
            for user in users_array:
                if user[1][9:] == uid:
                    run = user[0]
                    rn = user[2]
                    break
                else:
                    run = "Unavailable"
                    rn = "Unavailable"                    
                    
                   
            report.write("PROFILE.\n")
            report.write("Name: " + rn + ".\n")
            report.write("Username: "+ run + ".\n")
            report.write("User ID: " + uid + ".\n")
            report.write("App Version: " + version + ".\n")
            
            
            
            
            stmt.close()
            dbConn.close()
            os.remove(localpath)              
        
        for file in files:
            ts = ""

            lclDbPath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()) + ".db")
            ContentUtils.writeToFile(file, File(lclDbPath))
            
            try:
                #Open database
                Class.forName("org.sqlite.JDBC").newInstance()
                dbConn = DriverManager.getConnection("jdbc:sqlite:%s"  % lclDbPath)
                #report.write("db successfully opened. \n")
            except SQLException as e:
                report.write("Cant open db \n")
              
            
             
            ##############################################################################################################################
            #############################################################################################################################
            #Build array with details of each conversation
            try:
                stmt = dbConn.createStatement()
                convos = stmt.executeQuery('SELECT thread_key, name FROM threads')
            except SQLException as e:
                report.write("Cant query db 3\n")
                report.write(e.getMessage())
                break  
            
            while convos.next():
                
                try:
                    convokey = convos.getString('thread_key')
                    convoname = convos.getString('name')
                    conv_array.append([convokey, convoname])
                except:
                    report.write("Error getting values\n")
            
            
            


            #############################################################################################################################            
            #Build list of which user was in each conversation
            try:
                stmt = dbConn.createStatement()
                participants = stmt.executeQuery('SELECT thread_key, user_key FROM thread_participants')
            except:
                report.write('cant query thread_pariticipants\n')
                report.write(e.getMessage())
                
            while participants.next():
                try:
                    thread = participants.getString('thread_key')
                    userkey = participants.getString('user_key')
                except:
                    report.write("Loop Error")
                p = [thread, userkey]
                part_array.append(p)
                
                    
                
            stmt.close()    
                
                
            #######################################################################################################
            #######################################################################################################
            #######################################################################################################
            

            # Get full details of each message sent and received using the App
            try:
                stmt = dbConn.createStatement()
                messages = stmt.executeQuery('SELECT thread_key, text , sender, timestamp_ms, attachments, pending_send_media_attachment, snippet, sticker_id, source, admin_text_thread_rtc_event, msg_type, admin_text_type, shares, generic_admin_message_extensible_data FROM messages')
            except SQLException as e:
                report.write("Cant query db 4\n")
                report.write(e.getMessage())
                break

            while messages.next():
                try:
                    messagetype = ""
                    thread = messages.getString('thread_key')
                    text = messages.getString('text')
                    sender = messages.getString('sender')
                    
                    timesent = messages.getString('timestamp_ms')
                    
                    
                    attachments = messages.getString('attachments')
                    pending_send_media_attachment = messages.getString('pending_send_media_attachment')
                    snippet = messages.getString('snippet')
                    sticker_id = messages.getString('sticker_id')
                    source = messages.getString('source')
                    admin_text_thread_rtc_event = messages.getString('admin_text_thread_rtc_event')
                    msg_type = messages.getString('msg_type')
                    admin_text_type = messages.getString('admin_text_type')
                    shares = messages.getString('shares')
                    generic_admin_message_extensible_data = messages.getString('generic_admin_message_extensible_data')
                    mimetype = ""
                    location = ""
                    calldetails = []
                    
                except:
                    report.write("Error getting values")
                    
                try:
                    sender = json.loads(sender)
                except:
                    sender = "no sender"
                if type(sender) == dict:
                    #isolate sender username and display name
                    sender = sender.get('user_key')
                    sendkey = sender.split(":")[1]
                    for user in users_array:
                        if user[1] == sender:
                            sender = (user[2] + "(" + user[0] + ")")
                else:
                    sender = "no sender"                

                if msg_type == "-1" or timesent == "0" or msg_type == "8":
                    #unknown message
                    messagetype = "nothing"


                
                elif admin_text_type != None and int(admin_text_type) > 0:
                    #generic admin message
                    
                    if admin_text_type == "57":
                        #Get call details
                        messagetype = "call"
                        v = ""
                        call = json.loads(generic_admin_message_extensible_data)
                        calldetails.append(call.get('event'))
                        if call.get('video') == "false":
                            calldetails.append("voice")
                            v = "voice"
                        else:
                            calldetails.append("video")
                            v = "video"
                        calldetails.append(call.get('call_duration'))
                        
                        recip = thread.split(":")
                        del recip[0]
                        recip = ''.join(recip).replace(sendkey,"")
                        for u in users_array:
                            if u[1].replace("FACEBOOK:","") == recip:
                                recip = u[2] + "(" + u[0] + ")"
                        
                        call_array.append([sender, timesent, v, call.get('call_duration'), admin_text_thread_rtc_event, recip])
                        
                        

                    elif admin_text_type == "20":
                        #Reminder created
                        messagetype = "reminder created"
                        
                    elif admin_text_type == "26":
                        #Responded going
                        messagetype = "responded going"
                        
                    elif admin_text_type == "22":
                        #Happening Now
                        messagetype = "happening now"


                    
                elif snippet is not None:
                    #Wave or location
                    if "wav" in snippet:
                        #wave
                        #Use snippet for details
                        messagetype = "wave"
                        
                    if "location" in snippet:
                        #location
                        messagetype = "location"
                        try:
                            shares = shares[1:]
                            shares = shares[:-1]
                            shares = json.loads(shares)
                            if type(shares) == dict:
                                shares = shares.get("href")
                                coord = re.compile('\-?\d{1,3}\.\d+')
                                shares = coord.findall(shares)
                                shares = ("(" + shares[0] + "," + shares[1] + ")")
                        except:
                            shares = "(No location found)"
                        
                    
                elif sticker_id is not None:
                    #sticker
                    messagetype = "sticker"


                
                    
                elif attachments is not None:
                    #sent or received
                    a = attachments.replace("[{","")
                    a = a.replace("}]","")
                    a = a.split(",")
                    a_type = a[2].split(":")[1]
                    a_name = a[3].split(":")[1]
                    

                    if a_type == '"image/gif"':
                        ##gif
                        messagetype = "gif"
                        
                    elif a_type == '"image/jpeg"' or a_type == '"image/png"':
                        ##image
                        messagetype = "image"
                        
                    elif a_type == '"audio/mpeg"':
                        ##audio
                        messagetype = "audio"
                    else:
                        ##evrything else
                        messagetype = "other"

                    if pending_send_media_attachment is not None:
                        pending_send_media_attachment = pending_send_media_attachment[2:]
                        pending_send_media_attachment = pending_send_media_attachment[:-2]
                        
                        location = pending_send_media_attachment.split(",")[0].split(":")
                        location = location[len(location)-1]
                    else:
                        location = "Received attachment: Location not available. (see 'cache/image')"
                        
                        
                        
                else:
                    messagetype = "text"
                    try:
                        text = ''.join([i if ord(i) < 127 else '(e)' for i in text])  
                    except:
                        text = "Error getting string"
                 
                
                
                
    
                
                me = [messagetype, thread, text, sender, timesent, attachments, pending_send_media_attachment, snippet, sticker_id, source, admin_text_thread_rtc_event, msg_type, admin_text_type, mimetype, location, shares, calldetails]
                message_array.append(me)
    


            # Clean up
            
                
            stmt.close()
            
            
            dbConn.close()
            os.remove(lclDbPath)
            
            
            report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n")    
            ##########################################################################################################################################
            report.write("CONVERSATIONS\n")
            
            for conv in conv_array:
                try:
                    #Write Conversation details
                    report.write("\nConversation ID: " + conv[0] + ". Name: '" + conv[1] + "'.\n")
                    report.write("Participants:\n")
                    for user in part_array:
                        if user[0] == conv[0]:
                            for u in users_array:
                                if user[1] == u[1]:
                                    report.write("    +" + u[2]+" (" + u[0] + ")\n") 
                    
                except:
                    #conversation has no name
                    report.write("\nConversation ID: " + conv[0] + ". Has no name.\n")
                    report.write("Participants:\n")
                    for user in part_array:
                        if user[0] == conv[0]:
                            for u in users_array:
                                if user[1] == u[1]:
                                    report.write("    +" + u[2]+" (" + u[0] + ")\n")                    
                
                
            report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n")    
            ##########################################################################################################################################
            report.write("CALLS\n")     
            
            # Write details of all calls sent and received
            for call in call_array:
                if call[4] == "missed_call":
                    report.write(" + " + self.timeStampConverter(float(call[1])) + ": Missed " + call[2] + " call from " + call[0] + " to " + call[5] + ".\n")
                elif call[4] == "one_on_one_call_ended":
                    report.write(" + " + self.timeStampConverter(float(call[1])) + ": " + call[2] + " call from from " + call[0] + " to " + call[5] + ". Duration: " + str(call[3]) +" seconds.\n")
            
            report.write("------------------------------------------------------------------------------------------------------------------------------------------------------------\n")    
            ##########################################################################################################################################
            report.write("MESSAGES\n")   
            
            
            for conv in conv_array:
                if conv[0].startswith("G"):
                    if conv[1] is not None:
                        i = conv[1]
                    else:
                        i = conv[0]
                    report.write("\nGROUP CHAT: '" + i + "'\n")
                else:
                    n = str(conv[0])
                    n = n.replace("ONE_TO_ONE:","").replace(":","").replace(uid,"")
                    for user in users_array:
                        if user[1].replace("FACEBOOK:", "") == n:
                            report.write("\nCONVERSATION WITH " + user[2] +"\n")
                
                for m in message_array:
                    if m[1] == conv[0]:
                        
                        if m[0] == "call":
                            if m[16][0] == "one_on_one_call_ended":
                                report.write(" + " + self.timeStampConverter(float(m[4])) + " -- " + m[16][1].capitalize() + "call from " + m[3] + " lasted " + str(m[16][2]) + " seconds.\n")
                            if m[16][0] == "missed_call":
                                report.write(" + " + self.timeStampConverter(float(m[4])) + " -- Missed " + m[16][1].capitalize() + " from " + m[3] + ".\n")
                        if m[0] == "wave":
                            report.write(" + " + self.timeStampConverter(float(m[4])) + " -- " + m[3] + " waved.\n")
                        elif m[0] == "sticker":
                            report.write(" + " + self.timeStampConverter(float(m[4])) + " -- " + m[3] +  " sent -- Sticker: " + m[8] + "\n")
                        elif m[0] == "image":
                            report.write(" + " + self.timeStampConverter(float(m[4])) + " -- " + m[3] + " sent -- Image name: " + str(m[14]) + "\n")
                        elif m[0] == "gif":
                            report.write(" + " + self.timeStampConverter(float(m[4])) + " -- " + m[3] + " sent -- Gif name: " + str(m[14]) + "\n")
                        elif m[0] == "audio":
                            report.write(" + " + self.timeStampConverter(float(m[4])) + " -- " + m[3] + " sent -- Sound name: " + str(m[14]) + "\n")
                        elif m[0] == "text" and m[2] is not None:
                            try:                            
                                report.write(" + " + self.timeStampConverter(float(m[4])) + " -- " + m[3] + " sent -- '" + m[2] +  "'.\n")
                            except:
                                report.write(" + " + self.timeStampConverter(float(m[4])) + " -- " + m[3] + " sent -- Cant get text" +  "\n")    
                                    
                        elif m[0] == "location":
                            
                            report.write(" + " + self.timeStampConverter(float(m[4])) + " -- " + m[3] + " sent -- Location: " + m[7] + " " + m[15] + "\n")
                        elif m[0] == "nothing":
                            pass
                        
                            
                        
                        
                        else:
##                            report.write(m[0] + "-----" + m[4] + "------\n")
                            pass
                                            
                        

        report.close()

        # Add the report to the Case, so it is shown in the tree
        Case.getCurrentCase().addReport(fileName, self.moduleName, "Messenger TXT")

        progressBar.complete(ReportStatus.COMPLETE)


#Built from template @ https://github.com/sleuthkit/autopsy/blob/develop/pythonExamples/reportmodule.py
#With permission From author ( Brian Carrier [carrier <at> sleuthkit [dot] org] )



import os, time
from java.lang import System
from java.util.logging import Level
from org.sleuthkit.datamodel import TskData
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.report import GeneralReportModuleAdapter
from org.sleuthkit.autopsy.report.ReportProgressPanel import ReportStatus
from org.sleuthkit.autopsy.casemodule.services import FileManager

import xml.etree.cElementTree as et

from java.io import File
from java.lang import Class
from java.lang import System
from java.sql import DriverManager, SQLException

from org.sleuthkit.autopsy.datamodel import ContentUtils
from org.sleuthkit.autopsy.ingest import DataSourceIngestModule

# Class responsible for defining module metadata and logic
class SnapchatReportModule(GeneralReportModuleAdapter):

    moduleName = "Snapchat Report"

    def getName(self):
        return self.moduleName

    def getDescription(self):
        return "Writes details of Snapchat"

    def getRelativeFilePath(self):
        return "Snapchat.txt"
    
    #Convert from Epoch Time
    def timeStampConverter(self, timestamp):
        t = time.strftime("%a %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp / 1000.0))
        return t

    def generateReport(self, baseReportDir, progressBar):
        
        
        username = ""
        dispname = ""
        phone = ""
        user_id = ""
        
        
        friends_array = []
        feeds_array = []
        message_array = []
        
        # Open the output file.
        fileName = os.path.join(baseReportDir, self.getRelativeFilePath())
        report = open(fileName, 'w')
        
        report.write("SNAPCHAT REPORT\n")
        report.write("This report harvests and displays the user data and communications from the Snapchat Application\n")
        report.write("-----------------------------------------------------------------------------------------------------------------------\n\n")        

        # Query the database for the files (ignore the directories)
        dataSources = Case.getCurrentCase().getDataSources()
        fileManager = Case.getCurrentCase().getServices().getFileManager()
        for dataSource in dataSources:
            maindb = fileManager.findFiles(dataSource, 'main.db','com.snapchat.android/databases')
            userprefs = fileManager.findFiles(dataSource, 'user_session_shared_pref.xml','com.snapchat.android/shared_prefs')

        
        #Get user details from user_session_shared_pref.xml
        for file in userprefs:
            prefspath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()) + ".xml")
            ContentUtils.writeToFile(file, File(prefspath))
            
            tree = et.parse(prefspath)
            root = tree.getroot()
            
            for string in root.findall('string'):
                if string.get('name') == "key_display_name":
                    dispname = string.text
                if string.get('name') == "key_username":
                    username = string.text
                if string.get('name') == "key_phone":
                    phone = string.text
                if string.get('name') == "key_user_id":
                    user_id = string.text
                    
        report.write("SNAPCHAT PROFILE.\n")
        report.write("Username: " + username + "\n")
        report.write("Display Name: " + dispname + "\n")
        report.write("Registered Phone: " + phone + "\n")
        report.write("User ID: " + user_id + "\n\n")
        report.write("----------------------------------------------\n")
                
                        
        
        
        
        
            
            
        for file in maindb:
            
            lclDbPath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()) + ".db")
            ContentUtils.writeToFile(file, File(lclDbPath))
            
            try:
                #Open database
                Class.forName("org.sqlite.JDBC").newInstance()
                dbConn = DriverManager.getConnection("jdbc:sqlite:%s"  % lclDbPath)
            except SQLException as e:
                report.write("Can't open db: " + e.getMessage() + "\n")

            #Query DB for friends details, only those that have been added
            try:
                stmt = dbConn.createStatement()
                friendsSet = stmt.executeQuery('SELECT _id, username, userId, displayName, addedTimestamp FROM Friend WHERE addedTimestamp IS NOT NULL;')
                report.write("CONTACTS.\n")
            except SQLException as e:
                    report.write("Can't query Friend db: " + e.getMessage() + "\n")            
            
            
            while friendsSet.next():
                try:
                    f_username = friendsSet.getString('username')
                    f_userid = friendsSet.getString('userId')
                    f_display = friendsSet.getString('displayName')
                    f_addtime = friendsSet.getString('addedTimestamp')
                    if f_addtime is not None:
                        f_addtime = self.timeStampConverter(float(f_addtime))
                    else:
                        f_addtime = "Not added"
                    f_id = friendsSet.getString('_id')
                    if f_username != "system_user_id":
                        f = [f_userid, f_username, f_display, f_addtime, f_id]
                    friends_array.append(f)
                    
                except SQLException as e:
                    report.write("Error getting values: " + e.getMessage()+ "\n")
        
            
            
            
            for friend in friends_array:
                report.write(friend[2] + " (" + friend[1] + ") --- " + "ID: " + friend[0] + " --- Added on: " + friend[3] + ".\n")
        
            stmt.close()
            #############################################################################################################
            #Get details of stories posted by self and others
            
            try:
                stmt = dbConn.createStatement()
                stories = stmt.executeQuery('SELECT username, captionTextDisplay, viewed, expirationTimestamp from StorySnap;')
            except SQLException as e:
                    report.write("Can't query story table: " + e.getMessage() + "\n")      
            stories_array = []
            while stories.next():
                try:
                    un = stories.getString('username')
                    caption = stories.getString('captionTextDisplay')
                    viewed = stories.getString('viewed')
                    expires = stories.getString('expirationTimestamp')
                    if caption is None:
                        caption = "#NO TEXT#"
                    if viewed == "1":
                        viewed = "has"
                    else:
                        viewed = "has not"
                    stories_array.append([un, caption, viewed, self.timeStampConverter(float(expires))])
                except SQLException as e:
                    report.write("Error getting stories: " + e.getMessage()+ "\n") 
                    
            report.write("----------------------------------------------\n")
            report.write("Stories\n")                
            for story in stories_array:
                report.write(" + " + story[0].capitalize() + " posted a story saying '" + story[1] + "'. -- Expires: " + story[3] + " --  It " + story[2] + " been viewed.\n")
            stmt.close()
            
            
            #############################################################################################################
            #Query db for list of conversations (feeds)
            try:
                stmt = dbConn.createStatement()
                feedSet = stmt.executeQuery('SELECT _id, key, specifiedName, participantString from Feed;')
            except SQLException as e:
                    report.write("Can't query Feed table: " + e.getMessage() + "\n")      
            
            while feedSet.next():
                try:
                    feed_id = feedSet.getString('_id')
                    feedKey = feedSet.getString('key')
                    feedName = feedSet.getString('specifiedName')
                    feedParts = feedSet.getString('participantString')
                    if feedName is None:
                        feedName = "#NO NAME#"
                    if feedParts is None:
                        feedParts = feedKey.split("~")[1]                    
                    feeds_array.append([feed_id, feedKey, feedName, feedParts])
                except SQLException as e:
                    report.write("Error getting values: " + e.getMessage()+ "\n")
                    
            
            report.write("----------------------------------------------\n")
            report.write("FEEDS\n")                
            for feed in feeds_array:
                report.write("Feed: " + feed[1] + "(" + feed[2] + ").  ----  Participants: " + feed[3] + ".\n")
            
            stmt.close()
            
            #########################################################################################################################################
            #Query DB for list of messages
            report.write("----------------------------------------------\n")
            report.write("MESSAGES\n")
                       
            try:
                stmt = dbConn.createStatement()
                resultSet = stmt.executeQuery('SELECT timestamp, feedRowId, senderId, type, mediaType, mediaTimerSec, hex(content), savedStates FROM Message;')
            except SQLException as e:
                report.write("Error executing message query " + e.getMessage() + ".\n")

                          
                
            while resultSet.next():
                try: 
                    messageTime  = float(resultSet.getString("timestamp"))
                    messageFeedRow = resultSet.getString("feedRowId")
                    messageSender = resultSet.getString("senderId")
                    for friend in friends_array:
                        if str(friend[4]) == str(messageSender):
                            messageSender = friend[2] + "(" + friend[1] + ")"
                            break
                    messageType = resultSet.getString("type")
                    messageMedTyp = resultSet.getString("mediaType")
                    messageTimSec = resultSet.getString("mediaTimerSec")
                    messageContent = resultSet.getString("hex(content)")
                    if messageContent is None:
                        messageContent = "No content"
                    else:
                        converted = []
                        conthex = [messageContent[i:i+2] for i in range(0,len(messageContent),2)]
                        for char in conthex:
                            
                            h = int(char, 16)
                            if h >= 32 and h <= 126:
                                h = hex(h).replace("0x","")
                                h = h.decode("hex")
                                converted.append(h)
                        messageContent = ''.join(converted)
                        
                                
                            
                    messageSaved = resultSet.getString("savedStates")
                    
                    
                            
                    message_array.append([messageTime, messageFeedRow, messageSender,messageType, messageMedTyp, messageTimSec, messageContent, messageSaved])

                    
                except SQLException as e:
                    report.write("\n Loop is Buggered \n")
                    break
                
                
                
            for feed in feeds_array:
                report.write("\n -- " + feed[1] + " --\n")
                #Write details for each message in feed
                for message in message_array:
                    if feed[0] ==  message[1]:
                        if message[3] == "text":
                            #Message is purely text
                            report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- sent a " + message[3] + " saying '" + message[6] + "'.\n")
                            
                        elif message[3] == "snap":
                            #Message is a "snap" or image
                            report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- sent a " + message[3] + " .\n")
                        elif message[3] == "erased_message":
                            #Message was erased
                            report.write(self.timeStampConverter(message[0]) + ": From: " + message[2] + ". Messaged erased.\n")
                        elif message[3] == "cognac_close":
                            #User initiated a game
                            report.write(self.timeStampConverter(message[0]) + ": " + message[2] + " played a game. .\n")
                        elif message[3] == "sticker_v3":
                            #Sticker was sent
                            report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- sent a sticker.\n")
                        elif message[3] == "media_v4":
                            #A form of media was sent
                            report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- sent a media item.\n")
                        elif message[3] == "audio_note":
                            #A voice recording was sent
                            report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- sent an audio note.\n")
                        elif message[3] == "welcome_message":
                            #One of Team Snapchat's welcome messages was sent ( Always present )
                            report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- sent a Welcome Message saying '" + message[6] + "'.\n")
                        elif message[3].endswith("call"):
                            #A form of call interaction occurred
                            if messageType == "joined_call":
                                report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- Joined a call.\n")
                            if messageType == "left_call":
                                report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- Left a call.\n")
                            if messageType == "missed_video_call":
                                report.write(self.timeStampConverter(message[0]) + ":      --- Missed video call from " + message[2] + ".\n")
                        elif message[3] == "screenshot":
                            report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- took a screenshot of the chat. \n")
                        
                        else:
                            report.write(self.timeStampConverter(message[0]) + ": " + message[2] + "      --- sent a " + message[3] + ".\n")
                
                
            # Clean up
            stmt.close()
            dbConn.close()
            os.remove(lclDbPath)

        report.close()

        # Add the report to the Case, so it is shown in the tree
        Case.getCurrentCase().addReport(fileName, self.moduleName, "Snapchat TXT")

        progressBar.complete(ReportStatus.COMPLETE)

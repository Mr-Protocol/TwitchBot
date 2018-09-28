#--------------------------------------------------------------------------
#---------------------------------- INFO ----------------------------------
#--------------------------------------------------------------------------
# This is some code to auto respond and mod Twitch channels.
# Files required: scriptconfig.py
#
# Requirements:
# Python3.x
# pip install irc
# pip install requests
import sys
import irc.bot
import requests
import time
import datetime
from datetime import timezone
import shutil
import re
import os
from os import system
import errno
import scriptconfig as cfg

#--------------------------------------------------------------------------
#---------------------------------- MAGIC ---------------------------------
#--------------------------------------------------------------------------

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, token, channels):
        # Create IRC bot connection
        self.token = token
        server = 'irc.chat.twitch.tv'
        port = 6667
        os.system('cls' if os.name == 'nt' else 'clear')
        self.CheckChannels()
        system(f'title TwitchBot @ {self.TimeStamp(cfg.LogTimeZone)}  - {cfg.username} in channel(s): {cfg.channels}')
        self.PrintTriggers()
        self.ClearLogs()
        self.DisplayOptions()
        print (f'{self.TimeStamp(cfg.LogTimeZone)}\r\nConnecting to {server} on port {port} as {username}...\r\n')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+token)], username, username)
        self.epoch = 0
        if cfg.EnableCopyPasta:
            self.epochCopyPasta = 0
        if cfg.EnableModTriggers:
            self.dbModChannels = []
        if cfg.EnableKeywordRepeater:
            self.RepeaterEpoch = 0
            self.dbRepeaterKeyword = {}
            splitchans = cfg.channels.split(',')
            for x in splitchans:
                self.dbRepeaterKeyword.update({x: ('', 0)})
        if cfg.EnableUniqueChatters:
            self.dbUniqueChatters = {}
            self.UniqueChattersStartTime = self.TimeStamp(0)
    
    def TimeStamp(self, tzone):
        if tzone:
            tstamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            tstamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + '-UTC'
        return f'{tstamp}'

    #Check for valid channels starting with #, and doesn't end with a comma
    def CheckChannels(self):
        if cfg.channels.endswith(','):
            print ()
            print ('Do not end channel list with a comma.\r\n')
            exit()
        ckchannels = cfg.channels.split(',')
        for chan in ckchannels:
            if chan.startswith('#'):
                pass
            else:
                print ()
                print ('Channels misconfigured, make sure there are # prepending the channel name. \r\n')
                print (chan)
                exit()

    def ClearLogs(self):
        clearalllogs = input('Do you want to clear all the logs (Y/N)? (Default: N)')
        if str.lower(clearalllogs) == 'y':
            try:
                shutil.rmtree('Logs')
                time.sleep(2)
                os.makedirs('Logs')
            except:
                os.makedirs('Logs')
        os.system('cls' if os.name == 'nt' else 'clear')
    
    #Prints out triggers to terminal output
    def PrintTriggers(self):
        print ('----- Review Triggers Below ----- \r\n')
        print ('Chat Triggers: ')
        for k in cfg.ChatTriggers.keys():
            print (k)
            for v in cfg.ChatTriggers[k]:
                print (v)
        print ()
        print ('Mod Triggers: ')
        for k in cfg.ModTriggers.keys():
            print (k)
            for v in cfg.ModTriggers[k]:
                print (v)
        print ()
        print ('Username Safe/Whitelist: ')
        print (cfg.SafelistUsers)
        print ()

    def DisplayOptions(self):
        if cfg.ChanFilters:
            print ('Channels filtered out from terminal.')
            print (f'Filtered Channels: {cfg.ChanTermFilters}\r\n')
        if cfg.LogChatMessages:
            print ('Logging chat messages.')
            print (f'Logging Channels: {cfg.ChatLogChannels}\r\n')
        if cfg.LogSystemMessages:
            if cfg.RawSystemMsgs:
                print('Logging RAW user notice (system) messages.')
                print (f'Logging Channels: {cfg.SysMsgLogChannels}\r\n')
            else:
                print ('Logging user notice (system) messages.')
                print (f'Logging Channels: {cfg.SysMsgLogChannels}\r\n')
        if cfg.AnnounceNewSubs:
            print ('Announcing new subs in the following channels.')
            for k,v in cfg.AnnounceNewSubsChanMsg.items():
                print (f'{k} - {v}')
                if cfg.AnnounceNewSubsChanMsg[k][0][1]:
                    print ('--- Tagging Sub users is enabled.')
            print ()
        if cfg.AnnounceResubs:
            print ('Announcing resubs in the following channels.')
            for k,v in cfg.AnnounceReSubsChanMsg.items():
                print (f'{k} - {v}')
                if cfg.AnnounceReSubsChanMsg[k][0][1]:
                    print ('--- Tagging Resub users is enabled.')
            print ()
        if cfg.AnnounceGiftSubs:
            print ('Announcing gifted subs in the following channels.')
            for k,v in cfg.AnnounceGiftSubsChanMsg.items():
                print (f'{k} - {v}')
                if cfg.AnnounceGiftSubsChanMsg[k][0][1]:
                    print ('--- Tagging Gifted users is enabled.')
            print ()
        if cfg.AnnounceRaids:
            print ('Announcing raids in the following channels.')
            print (f'{cfg.AnnounceRaidChannels} - {cfg.RaidMsg} systemmsg {cfg.RaidMsg} \r\n')
    
    def CheckLogDir(self, logpath):
        if not os.path.exists(f'Logs/{logpath}/'):
            try:
                os.makedirs(f'Logs/{logpath}/')
            except OSError as error:
                if error.errno != errno.EEXIST:
                    raise

    def on_welcome(self, c, e):
        print (f'Joining {cfg.channels}\r\n')
        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(cfg.channels)

    def on_pubmsg(self, c, e):
        themsg = e.arguments[0]
        currentchannel = e.target
        #Used for debugging.
        #print (e)
        
        #Chat log with usernames and Moderator status.
        for x in e.tags:
            if x['key'] == 'display-name':
                chatuser = x['value']
            if x['key'] == 'subscriber':
                isasub = x['value']
            if x['key'] == 'mod':
                isamod = x['value']
        if str.lower(chatuser) in currentchannel:
            chatheader = ' - !HOST!-'
        elif isamod == '1':
            chatheader = ' - !MOD!-'
        elif isasub == '1':
            chatheader = ' - !SUB!-'
        else:
            chatheader = ' - '
        
        #Terminal Chat Log - Prepend Host/Mod status to accounts in chat.
        #Filter channels using ChanTermFilters to hide channel(s) chat from terminal
        if cfg.ChanFilters and currentchannel in cfg.ChanTermFilters:
            pass
        else:  
            print (f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel}{chatheader}{chatuser}: {themsg}')
        
        #Chat Highlights Log - Will log messages that contain username
        if cfg.LogHighlights and str.lower(cfg.username) in str.lower(themsg):
            self.CheckLogDir('Chat')
            f = open (f'Logs/Chat/{currentchannel}_HighlightsLog.txt', 'a+', encoding='utf-8-sig')
            f.write(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel}{chatheader}{chatuser}: {themsg}\r\n')
            f.close()
        
        #Chat Logging To File
        if cfg.LogChatMessages:
            if 'GLOBAL' in cfg.ChatLogChannels or currentchannel in cfg.ChatLogChannels:
                self.CheckLogDir('Chat')
                f = open (f'Logs/Chat/{currentchannel}_ChatLog.txt', 'a+', encoding='utf-8-sig')
                f.write(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel}{chatheader}{chatuser}: {themsg}\r\n')
                f.close()
        
        #ASCII ART - Log potential messages for future mod triggers
        if cfg.LogAscii:
            if any(x in cfg.LogAsciiSet for x in themsg):
                self.CheckLogDir('Chat')
                f = open (f'Logs/Chat/{currentchannel}_ASCII.txt', 'a+', encoding='utf-8-sig')
                f.write(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel}{chatheader}{chatuser}: {themsg}\r\n')
                f.close()
        
        #Repeater Mode aka Giveaway Mode
        if cfg.EnableKeywordRepeater: #Counting keyword           
            if self.dbRepeaterKeyword[currentchannel][0] == themsg:
                self.dbRepeaterKeyword.update({currentchannel: (themsg, self.dbRepeaterKeyword[currentchannel][1] + 1)})
                if self.dbRepeaterKeyword[currentchannel][1] > cfg.KeywordRepeaterCount:
                    if time.time() - self.RepeaterEpoch >= 30: #A little anti-spam
                        c.privmsg(currentchannel, themsg)
                        self.dbRepeaterKeyword.update({currentchannel: ('', 0)})
                        self.RepeaterEpoch = time.time()
            else: #New keyword
                self.dbRepeaterKeyword.update({currentchannel: (themsg, 0)})
        
        #CopyPasta Mode
        if cfg.EnableCopyPasta:
            if currentchannel in cfg.CopyPastaTriggers:
                for x in range(len(cfg.CopyPastaTriggers[currentchannel])):
                    if str.lower(cfg.CopyPastaTriggers[currentchannel][x]) in str.lower(themsg):
                        if time.time() - self.epochCopyPasta >= 90:
                            self.epochCopyPasta = time.time()
                            c.privmsg(currentchannel, themsg)
                            print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} {cfg.username}: {themsg}\r\n')

        #Unique Chatters Info
        if cfg.EnableUniqueChatters:
            if currentchannel in self.dbUniqueChatters:
                for x in range(len(self.dbUniqueChatters[currentchannel])):
                    if str.lower(chatuser) in self.dbUniqueChatters[currentchannel]:
                        self.dbUniqueChatters[currentchannel][str.lower(chatuser)] = self.dbUniqueChatters[currentchannel][str.lower(chatuser)] + 1
                    else:
                        self.dbUniqueChatters[currentchannel].update({str.lower(chatuser): 1})
            else:
                self.dbUniqueChatters[currentchannel] = {str.lower(chatuser): 1}

            if themsg == '!uchatters' and str.lower(chatuser) in cfg.UniqueChattersMods:
                uchattersmsg = f'There are {len(self.dbUniqueChatters[currentchannel])} unique chatters since {self.UniqueChattersStartTime}.'
                c.privmsg(currentchannel, uchattersmsg)

            if '!ucount' in themsg[:7] and str.lower(chatuser) in cfg.UniqueChattersMods:
                ucountuser = themsg.split(' ')[1]
                try:
                    c.privmsg(currentchannel,f'The user {ucountuser} has {self.dbUniqueChatters[currentchannel][str.lower(ucountuser)]} messages since {self.UniqueChattersStartTime}.')
                except:
                    c.privmsg(currentchannel,f'User not found')

        #Skip parsing and triggers if the user is a mod/host or in safelist, also if user is a sub
        if isamod == '1':
            pass
        elif str.lower(chatuser) in cfg.SafelistUsers:
            pass
        elif cfg.DontTriggerSubs and isasub == '1':
            pass
        else:        
            #Chat Triggers - uses lcase themsg directly
            if cfg.EnableChatTriggers:
                for ChanAndGlobal in cfg.ChatTriggers:
                    if currentchannel == ChanAndGlobal or ChanAndGlobal == 'GLOBAL':
                        for x in range(len(cfg.ChatTriggers[ChanAndGlobal])):
                            if str.lower(cfg.ChatTriggers[ChanAndGlobal][x][0]) in str.lower(themsg):
                                cresponse = cfg.ChatTriggers[ChanAndGlobal][x][1]
                                if cfg.ChatTriggers[ChanAndGlobal][x][2]:
                                    cresponse = f'{cresponse} {chatuser}'
                                if cfg.AutomatedRespondEnabled:
                                    cresponse = f'{cresponse} {cfg.AutomatedResponseMsg}'
                                #Log it
                                self.CheckLogDir('ChatTriggers')
                                f = open (f'Logs/ChatTriggers/{currentchannel}_ChatTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                f.write(f'{self.TimeStamp(cfg.LogTimeZone)} TRIGGER EVENT: {currentchannel}{chatheader}{chatuser}: {themsg}\r\n')
                                f.close()
                                if time.time() - self.epoch >= 90: #A little anti-spam for triggered words
                                    self.epoch = time.time()
                                    c.privmsg(currentchannel, cresponse)
                                    print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {cfg.username}: {cresponse}')
                                    f = open (f'Logs/ChatTriggers/{currentchannel}_ChatTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                    f.write(f'{self.TimeStamp(cfg.LogTimeZone)} SENT: {chatheader}{cfg.username}: {cresponse}\r\n')
                                    f.close()
                                time.sleep(2)
           
            #Mod Triggers - uses the lcase themsg and splits words via spaces
            if cfg.EnableModTriggers:
                if currentchannel in self.dbModChannels:
                    for ChanAndGlobal in cfg.ModTriggers:
                        if currentchannel == ChanAndGlobal or ChanAndGlobal == 'GLOBAL':
                            for x in range(len(cfg.ModTriggers[ChanAndGlobal])):
                                if str.lower(cfg.ModTriggers[ChanAndGlobal][x][0]) in str.lower(themsg):
                                    mresponse = cfg.ModTriggers[ChanAndGlobal][x][1]
                                    self.CheckLogDir('ModTriggers')
                                    #Handle mod text response
                                    if cfg.ModTriggers[ChanAndGlobal][x][2]:
                                        txtreponse = cfg.ModTriggers[ChanAndGlobal][x][2]
                                        if cfg.ModTriggers[ChanAndGlobal][x][3]:
                                            txtreponse = f'{txtreponse} {chatuser}'
                                        c.privmsg(currentchannel, f'{txtreponse}')
                                        print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - !MOD!-{cfg.username}: {txtreponse}')
                                    try:
                                        splitresponse = mresponse.split(' ')
                                        modoptions = ''
                                        for x in splitresponse[1:]:
                                            modoptions = f'{modoptions} {x}'
                                        c.privmsg(currentchannel, f'{splitresponse[0]} {chatuser}{modoptions}')
                                        print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - !MOD!-{cfg.username}: {splitresponse[0]} {chatuser}{modoptions}')
                                        f = open (f'Logs/ModTriggers/{currentchannel}_ModTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                        f.write(f'{self.TimeStamp(cfg.LogTimeZone)} TRIGGER EVENT: {chatheader}{chatuser}: {themsg}\r\n')
                                        f.write(f'{self.TimeStamp(cfg.LogTimeZone)} SENT: !MOD!-{cfg.username}: {splitresponse[0]} {chatuser}{modoptions}\r\n')
                                        f.close()
                                    except:
                                        c.privmsg(currentchannel, f'{mresponse} {chatuser}')
                                        print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - !MOD!-{cfg.username}: {mresponse} {chatuser}')
                                        f = open (f'Logs/ModTriggers/{currentchannel}_ModTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                        f.write(f'{self.TimeStamp(cfg.LogTimeZone)} TRIGGER EVENT: {chatheader}{chatuser}: {themsg}\r\n')
                                        f.write(f'{self.TimeStamp(cfg.LogTimeZone)} SENT: !MOD!-{cfg.username}: {mresponse} {chatuser}\r\n')
                                        f.close()
    
    def on_userstate(self, c, e):
        #print (e)
        currentchannel = e.target
        #Detects if cfg.username is a mod in a joined channel and adds it to a list
        for x in e.tags:
            if x['key'] == 'mod':
                if x['value'] == '1':
                    self.dbModChannels.append(currentchannel)
                if str.lower(cfg.username) in currentchannel:
                    self.dbModChannels.append(currentchannel)

    def on_usernotice(self, c, e):
        #print (e)
        currentchannel = e.target
        for x in e.tags:
            if x['key'] == 'msg-id':
                sysmsgid = x['value']
            if x['key'] == 'display-name':
                chatuser = x['value']
            if x['key'] == 'system-msg':
                sysmsg = re.sub('\r|\n', '', x['value']) #Removes \r and \n because Twitch is stupid and puts a \n mid string.
            if x['key'] == 'msg-param-recipient-display-name':
                subgiftrecipient = x['value']
        
        #Filter channels from terminal output
        if cfg.ChanFilters and currentchannel in cfg.ChanTermFilters:
            pass
        else:   
            print (f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {sysmsg}')
        
        #Log system mesages
        if cfg.LogSystemMessages:
            if 'GLOBAL' in cfg.SysMsgLogChannels or currentchannel in cfg.SysMsgLogChannels:
                self.CheckLogDir('System')
                f = open (f'Logs/System/{currentchannel}_SystemMsgLog_{sysmsgid}.txt', 'a+', encoding='utf-8-sig')
                if cfg.RawSystemMsgs: #Log RAW
                    f.write(f'{self.TimeStamp(cfg.LogTimeZone)} {str(e)}\r\n')
                else: #Log Simplified
                    f.write (f'{self.TimeStamp(cfg.LogTimeZone)} {sysmsg}\r\n')
                f.close()
        
        #------------------------- Sub actions -------------------------
        if chatuser != cfg.username:
            if sysmsgid == 'sub' and cfg.AnnounceNewSubs:
                if currentchannel in cfg.AnnounceNewSubsChanMsg:
                    for x in range(len(cfg.AnnounceNewSubsChanMsg[currentchannel])):
                        tmpNewSubMsg = cfg.AnnounceNewSubsChanMsg[currentchannel][x][0]
                        if cfg.AnnounceNewSubsChanMsg[currentchannel][x][1]:
                            tmpNewSubMsg = f'{tmpNewSubMsg} {chatuser}'
                        c.privmsg(currentchannel, tmpNewSubMsg)
                        time.sleep(2)
            
            #Subtember allowed users to upgrade a gifted sub for $1 to continue for the next month. Considering it a resub for announce triggers
            if (sysmsgid == 'resub' or sysmsgid == 'giftpaidupgrade') and cfg.AnnounceResubs:
                if currentchannel in cfg.AnnounceReSubsChanMsg:
                    for x in range(len(cfg.AnnounceReSubsChanMsg[currentchannel])):
                        tmpReSubMsg = cfg.AnnounceReSubsChanMsg[currentchannel][x][0]
                        if cfg.AnnounceReSubsChanMsg[currentchannel][x][1]:
                            tmpReSubMsg = f'{tmpReSubMsg} {chatuser}'
                        c.privmsg(currentchannel, tmpReSubMsg)
                        time.sleep(2)
            
            if sysmsgid == 'subgift' and cfg.AnnounceGiftSubs:
                if currentchannel in cfg.AnnounceGiftSubsChanMsg:
                    for x in range(len(cfg.AnnounceGiftSubsChanMsg[currentchannel])):
                        tmpGiftSubMsg = cfg.AnnounceGiftSubsChanMsg[currentchannel][x][0]
                        if cfg.AnnounceGiftSubsChanMsg[currentchannel][x][1]:
                            tmpGiftSubMsg = f'{tmpGiftSubMsg} {chatuser}'
                        c.privmsg(currentchannel, tmpGiftSubMsg)
                        time.sleep(2)
                
            if sysmsgid == 'raid' and cfg.AnnounceRaids and currentchannel in cfg.AnnounceRaidChannels:
                c.privmsg(currentchannel, f'{cfg.RaidMsg} {sysmsg} {cfg.RaidMsg}')
            
            #What happens when the cfg.username is gifted a sub
            if sysmsgid == 'subgift' and str.lower(subgiftrecipient) == str.lower(cfg.username):
                c.privmsg(currentchannel, f'{cfg.GiftThanksMsg} {chatuser}')
                f = open (f'Logs/{currentchannel}_GiftedSub.txt', 'a+', encoding='utf-8-sig')
                f.write(f'{self.TimeStamp(cfg.LogTimeZone)} - {sysmsg}\r\n')
                f.write(f'{self.TimeStamp(cfg.LogTimeZone)} - {cfg.username}: {cfg.GiftThanksMsg} {chatuser}\r\n')
                f.close()
        
    def on_clearchat(self, c, e):
        #Shows when a user is banned
        #type: clearchat, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['USERBANNED'], tags: [{'key': 'ban-duration', 'value': '10'}, {'key': 'ban-reason', 'value': 'Accented language detected, English only please! [warning] – ohbot'}, {'key': 'room-id', 'value': 'XXXXXXXX'}, {'key': 'target-msg-id', 'value': 'XXXXXXXXXXXXXXXXXXX'}, {'key': 'target-user-id', 'value': 'XXXXX'}, {'key': 'tmi-sent-ts', 'value': 'XXXXXXXXXXXXX'}]
        #type: clearchat, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['USERBANNED'], tags: [{'key': 'ban-reason', 'value': None}, {'key': 'room-id', 'value': 'XXXXXXXXXX'}, {'key': 'target-user-id', 'value': 'XXXXX'}, {'key': 'tmi-sent-ts', 'value': 'XXXXXXXXXXXXX'}]
        #print (e)
        
        currentchannel = e.target
        user = e.arguments[0]
        banduration = None
        banreason = None

        for x in e.tags:
            if x['key'] == 'ban-duration':
                banduration = x['value']
            if x['key'] == 'ban-reason':
                banreason = x['value']

        if banduration:
            if banreason:
                banmsg = f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {user} timeout for {banduration} seconds. {banreason}'
            else:
                banmsg = f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {user} timeout for {banduration} seconds.'
        else:
            if banreason:
                banmsg = f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {user} is banned. {banreason}'
            else:
                banmsg = f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {user} is banned.'

        if cfg.ChanFilters and e.target in cfg.ChanTermFilters:
            pass
        else:
            print (f'CLEARCHAT-{banmsg}')

        if cfg.LogClearchat:
            self.CheckLogDir('clearchat')
            f = open (f'Logs/clearchat/{currentchannel}_clearchat.txt', 'a+', encoding='utf-8-sig')
            f.write(f'{banmsg}\r\n')
            f.close()

    
    def on_globaluserstate(self, c, e):
        #Not sure if this is real or not
        print (e)
    
    def on_roomstate(self, c, e):
        #Shows current chat settings for channel
        #type: roomstate, source: tmi.twitch.tv, target: #CHANNEL, arguments: [], tags: [{'key': 'broadcaster-lang', 'value': None}, {'key': 'emote-only', 'value': '0'}, {'key': 'followers-only', 'value': '2'}, {'key': 'r9k', 'value': '0'}, {'key': 'rituals', 'value': '0'}, {'key': 'room-id', 'value': 'XXXXXXXX'}, {'key': 'slow', 'value': '0'}, {'key': 'subs-only', 'value': '0'}]
        #print (e)
        pass
    
    def on_mode(self, c, e):
        #Shows +/- mod permissions
        #print (e)

        if cfg.ChanFilters and e.target in cfg.ChanTermFilters:
            pass
        else:
            currentchannel = e.target
            modstatus = e.arguments
            if modstatus[0] == '+o':
                print(f'MODE-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} +o {modstatus[1]} (mod).')
            elif modstatus[0] == '-o':
                print(f'MODE-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} -o {modstatus[1]} (demod).')
            else:
                print(f'MODE-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} {modstatus}')

    def on_join(self, c, e):
        #User joins the channel
        #print (e)

        currentchannel = e.target
        chatuser = e.source.split('!')[0]

        if cfg.ChanFilters and currentchannel in cfg.ChanTermFilters:
            pass
        else:
            if cfg.AnnounceUserJoins and chatuser in (uname for uname in cfg.AnnounceUserJoinList):
                print(f'JOIN-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {chatuser} has joined.')
            elif cfg.AnnounceUserJoins and 'GLOBAL' in (uname for uname in cfg.AnnounceUserJoinList):
                print(f'JOIN-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {chatuser} has joined.')
    
    def on_part(self, c, e):
        #User parts or leaves channel
        #print (e)
        
        currentchannel = e.target
        chatuser = e.source.split('!')[0]

        if cfg.ChanFilters and currentchannel in cfg.ChanTermFilters:
            pass
        else:
            if cfg.AnnounceUserParts and chatuser in (uname for uname in cfg.AnnounceUserPartList):
                print(f'PART-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {chatuser} has left.')
            elif cfg.AnnounceUserParts and 'GLOBAL' in (uname for uname in cfg.AnnounceUserPartList):
                print(f'PART-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {chatuser} has left.')
    
    def on_hosttarget(self, c, e):
        #Shows hosting info
        #type: hosttarget, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['channelbeinghosted -'], tags: []
        #print (e)

        if cfg.ChanFilters and e.target in cfg.ChanTermFilters:
            pass
        else:
            currentchannel = e.target
            targetchannel = e.arguments[0].split(' ')[0]
            print (f'HOSTTARGET-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} is hosting {targetchannel}.')

    
    def on_privmsg(self, c, e):
        #Not sure if this is real or not
        print (e)
    
    def on_privnotice(self, c, e):
        #Not sure if this is real or not
        print (e)
    
    def on_pubnotice(self, c, e):
        #Shows hosting message
        #Shows other channel options: slow mode, emote mode, etc.
        #type: pubnotice, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['Now hosting User.'], tags: [{'key': 'msg-id', 'value': 'host_on'}]
        #type: pubnotice, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['Exited host mode.'], tags: [{'key': 'msg-id', 'value': 'host_off'}]
        #type: pubnotice, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['This room is now in subscribers-only mode.'], tags: [{'key': 'msg-id', 'value': 'subs_on'}]
        #type: pubnotice, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['USER has been timed out for 2 seconds.'], tags: [{'key': 'msg-id', 'value': 'timeout_success'}]
        #print (e)

        currentchannel = e.target
        noticemsg = e.arguments[0]

        if cfg.ChanFilters and e.target in cfg.ChanTermFilters:
            pass
        else:           
            print (f'PUBNOTICE-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {noticemsg}')
            
        if cfg.LogPubnotice:
            self.CheckLogDir('pubnotice')
            f = open (f'Logs/pubnotice/{currentchannel}_pubnotice.txt', 'a+', encoding='utf-8-sig')
            f.write(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {noticemsg}\r\n')
            f.close()

    def on_whisper(self, c, e):
        #Received twitch direct messages
        #type: whisper, source: USER!USER@USER.tmi.twitch.tv, target: mr_protocol, arguments: ['THEMESSAGE'], tags: [{'key': 'badges', 'value': None}, {'key': 'color', 'value': None}, {'key': 'display-name', 'value': 'USERNAME'}, {'key': 'emotes', 'value': None}, {'key': 'message-id', 'value': 'XX'}, {'key': 'thread-id', 'value': 'XXXXXX_XXXXXXXX'}, {'key': 'turbo', 'value': '0'}, {'key': 'user-id', 'value': 'XXXXXXXX'}, {'key': 'user-type', 'value': None}]
        #print (e)

        whisper = e.arguments[0]
        for x in e.tags:
            if x['key'] == 'display-name':
                chatuser = x['value']
        print (f'WHISPER-{self.TimeStamp(cfg.LogTimeZone)} Direct Message - {chatuser}: {whisper}')

def main():
    bot = TwitchBot(cfg.username, cfg.token, cfg.channels)
    bot.start()
if __name__ == "__main__":
    main()
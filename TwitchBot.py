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
import threading
import scriptconfig as cfg

#--------------------------------------------------------------------------
#---------------------------------- MAGIC ---------------------------------
#--------------------------------------------------------------------------

class InputWatcher(threading.Thread):
    def __init__(self):
        super().__init__()
        self.callback = None
    
    def register_callback(self, func):
        self.callback = func

    def run(self):
        time.sleep(1)
        while True:
            input_command = input()
            if self.callback != None:
                self.callback(input_command)

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, token, channels, input_handler):
        input_handler.register_callback(self.BotCommands)
        # Create IRC bot connection
        self.token = token
        server = 'irc.chat.twitch.tv'
        port = 6667
        os.system('cls' if os.name == 'nt' else 'clear')
        self.CheckChannels()
        system(f'title TwitchBot @ {self.TimeStamp(cfg.LogTimeZone)}  - {cfg.username} in channel(s): {cfg.channels}')
        self.ClearLogs()
        print(f'{self.TimeStamp(cfg.LogTimeZone)}\r\nConnecting to {server} on port {port} as {username}...\r\n')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+token)], username, username)
        self.sub_epoch = 0
        if cfg.EnableChatTriggers:
            self.chat_epoch = 0
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
        if cfg.EnableChatTracking:
            self.dbChatters = {}
            self.ChattersStartTime = self.TimeStamp(0)
        keep_alive_thread = threading.Thread(target=self.KeepMeAlive)
        keep_alive_thread.daemon = True
        keep_alive_thread.start()

    def KeepMeAlive(self):
        while True:
            time.sleep(60*10)
            self.connection.ping(':tmi.twitch.tv')

    def BotCommands(self, cmd):
        cmd = str.lower(cmd)
        if cmd == '!enable':
            cfg.EnableBotCommands = 1
            print(f'Commands Enabled')

        if cfg.EnableBotCommands:
            try:
                if cmd in {"!commands", "!help"}:
                    print(f'!addmod, !addtrig, !bot, !chanfilteron, !chanfilteroff, !chantrig, !commands, !help, !showchatters, !repeatercount, !repeateroff, !repeateron, !uchatters, !ucount\r\n')

                elif '!uchatters' in cmd:
                    splitcmd = cmd.split(' ')
                    if len(splitcmd) == 1:
                        print(f'Usage: !uchatters #channel\r\n')
                    else:
                        print(f'There are {len(self.dbChatters[splitcmd[1]])} chatters since {self.ChattersStartTime}. in {splitcmd[1]}')
                        print(f'Current Time: {self.TimeStamp(0)}\r\n')

                elif '!bot' in cmd:
                    splitcmd = cmd.split(' ')
                    if len(splitcmd) == 1:
                        print(f'Usage: !bot #channel\r\n')
                    else:
                        self.connection.privmsg(splitcmd[1], f'Beep Bop Boop Beep... I\'m not a bot, I\'m a real man!')

                elif '!ucount' in cmd:
                    splitcmd = cmd.split(' ')
                    if len(splitcmd) == 1:
                        print(f'Usage: !ucount #channel username\r\n')
                    else:
                        currentchannel = splitcmd[1]
                        ucountuser = splitcmd[2]
                        try:
                            print(f'The user {ucountuser} has {self.dbChatters[currentchannel][ucountuser]} messages since {self.ChattersStartTime}.')
                            print(f'Current Time: {self.TimeStamp(0)}\r\n')
                        except:
                            print(f'User not found\r\n')
                
                elif '!addmod' in cmd:
                    splitcmd = cmd.split(' ',1)
                    if len(splitcmd) == 1:
                        print(f'Add mod trigger usage: !addmod #channel/GLOBAL,txt_trigger,timeout/ban 2m reason\r\n')
                    else:
                        try:
                            trigger = splitcmd[1].split(',')
                            cfg.ModTriggers[trigger[0]].append((trigger[1],trigger[2],None,1))
                            print(f'Added ModTrigger {trigger}\r\n')
                        except:
                            trigger = splitcmd[1].split(',')
                            cfg.ModTriggers[trigger[0]] = [(trigger[1],trigger[2],None,1)]
                            print(f'Added ModTrigger {trigger}\r\n')
                
                elif '!addtrig' in cmd:
                    splitcmd = cmd.split(' ',1)
                    if len(splitcmd) == 1:
                        print(f'Add chat trigger usage: !addtrig #channel/GLOBAL,txt_trigger,response,0/1 tag user\r\n')
                    else:
                        try:
                            trigger = splitcmd[1].split(',')
                            cfg.ChatTriggers[trigger[0]].append((trigger[1],trigger[2],trigger[3]))
                            print(f'Added {trigger}\r\n')
                        except:
                            trigger = splitcmd[1].split(',')
                            cfg.ChatTriggers[trigger[0]] = [(trigger[1],trigger[2],trigger[3])]
                            print(f'Added {trigger}\r\n')
                
                elif cmd == '!chanfilteron':
                    cfg.ChanFilters = 1
                    print(f'ChanFilters Enabled\r\n')
                
                elif cmd == '!chanfilteroff':
                    cfg.ChanFilters = 0
                    print(f'ChanFilters Disabled\r\n')
                
                elif cmd == '!repeateron':
                    cfg.EnableKeywordRepeater = 1
                    print(f'Enabled keyword repeater. Count trigger: {cfg.KeywordRepeaterCount}\r\n')
                
                elif cmd == '!repeateroff':
                    cfg.EnableKeywordRepeater = 0
                    print(f'Disabled keyword repeater.\r\n')

                elif '!repeatercount' in cmd:
                    splitcmd = cmd.split(' ')
                    if len(splitcmd) == 1:
                        print(f'Usage: !repeatercount #')
                    else:
                        cfg.KeywordRepeaterCount = splitcmd[1]
                        print(f'Keyword repeater count set to: {splitcmd[1]}\r\n')
                
                elif '!showchatters' in cmd:
                    splitcmd = cmd.split(' ')
                    if len(splitcmd) == 1:
                        print(f'Shows number of messages and chatters of #channel. Highest to lowest sort.')
                        print(f'Usage: !showchatters #channel\r\n')
                    else:
                        currentchannel = splitcmd[1]
                        sorted_d = sorted(((value, key) for (key,value) in self.dbChatters[currentchannel].items()), reverse=True)
                        print(f'Chatters in {currentchannel}: {sorted_d}\r\n')

                else:
                    print(f'No Command...\r\n')
            except:
                print(f'Something went wrong...\r\n')
    
    def TimeStamp(self, tzone):
        if tzone:
            tstamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            tstamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + '-UTC'
        return f'{tstamp}'

    #Check for valid channels starting with #, and doesn't end with a comma
    def CheckChannels(self):
        if cfg.channels.endswith(','):
            print()
            print('Do not end channel list with a comma.\r\n')
            exit()
        ckchannels = cfg.channels.split(',')
        for chan in ckchannels:
            if chan.startswith('#'):
                pass
            else:
                print()
                print('Channels misconfigured, make sure there are # prepending the channel name. \r\n')
                print(chan)
                exit()

    def ClearLogs(self):
        print('Do you want to clear all the logs (Y/N)? (Default: N)')
        try:
            for i in range(0,5):
                os.system('cls' if os.name == 'nt' else 'clear')
                print('Do you want to clear all the logs (Y/N)? (Default: N) (Timeout: ' + str((5 - i)) + ')')
                time.sleep(1)
            print('No input - Using Default - Not Clearing Logs')
        except KeyboardInterrupt:
            clearalllogs = input()
            if str.lower(clearalllogs) == 'y':
                try:
                    shutil.rmtree('Logs')
                    time.sleep(1.5)
                    os.makedirs('Logs')
                except:
                    os.makedirs('Logs')
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def CheckLogDir(self, logpath):
        if not os.path.exists(f'Logs/{logpath}/'):
            try:
                os.makedirs(f'Logs/{logpath}/')
            except OSError as error:
                if error.errno != errno.EEXIST:
                    raise

    def on_welcome(self, c, e):
        print(f'Joining {cfg.channels}\r\n')
        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(cfg.channels)

    def on_pubmsg(self, c, e):
        #print(e)
        self.ChatTextParsing(e)
        
    def ChatTextParsing(self, edata):
        e = edata
        themsg = e.arguments[0]
        currentchannel = e.target
        isamod = False
        isavip = False
        isasub = False
        #Used for debugging.
        #print(e)
        
        #Chat log with usernames and Moderator status.
        for x in e.tags:
            if x['key'] == 'display-name':
                chatuser = x['value']
            if x['key'] == 'subscriber':
                if x['value'] == '1':
                    isasub = True
            if x['key'] == 'mod':
                if x['value'] == '1':
                    isamod = True
            if x['key'] == 'badges':
                if 'vip' in str(x['value']):
                    isavip = True
                else:
                    isavip = False

        chatheader = ' - '
        if str.lower(chatuser) in currentchannel:
            chatheader = chatheader + '!HOST!-'
        if isamod:
            chatheader = chatheader + '!MOD!-'
        if isavip:
            chatheader = chatheader + '!VIP!-'        
        if isasub:
            chatheader = chatheader + '!SUB!-'

        #Terminal Chat Log - Prepend Host/Mod status to accounts in chat.
        #Filter channels using ChanTermFilters to hide channel(s) chat from terminal
        if cfg.ChanFilters and currentchannel in cfg.ChanTermFilters:
            pass
        else:  
            print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel}{chatheader}{chatuser}: {themsg}')
        
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
                        self.connection.privmsg(currentchannel, themsg)
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
                            self.connection.privmsg(currentchannel, themsg)
                            print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} {cfg.username}: {themsg}\r\n')

        #Tracking Chatters Info
        if cfg.EnableChatTracking:
            if currentchannel in self.dbChatters:
                if str.lower(chatuser) in self.dbChatters[currentchannel]:
                    self.dbChatters[currentchannel][str.lower(chatuser)] += 1
                else:
                    self.dbChatters[currentchannel][str.lower(chatuser)] = 1
            else:
                self.dbChatters[currentchannel] = {str.lower(chatuser): 1}

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
                            if time.time() - self.chat_epoch >= 90: #A little anti-spam for triggered words
                                self.chat_epoch = time.time()
                                self.connection.privmsg(currentchannel, cresponse)
                                print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {cfg.username}: {cresponse}')
                                f = open (f'Logs/ChatTriggers/{currentchannel}_ChatTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                f.write(f'{self.TimeStamp(cfg.LogTimeZone)} SENT: {chatheader}{cfg.username}: {cresponse}\r\n')
                                f.close()
      
        #Mod Triggers - uses the lcase themsg and splits words via spaces
        if cfg.EnableModTriggers:
            #Skip parsing and triggers if the user is a mod/host, VIP, or in safelist, also if user is a sub
            if isamod:
                pass
            elif cfg.DontTriggerVIP and isavip:
                pass
            elif str.lower(chatuser) in cfg.SafelistUsers:
                pass
            elif cfg.DontTriggerSubs and isasub:
                pass
            else:
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
                                        self.connection.privmsg(currentchannel, f'{txtreponse}')
                                        print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - !MOD!-{cfg.username}: {txtreponse}')
                                    try:
                                        splitresponse = mresponse.split(' ')
                                        modoptions = ''
                                        for x in splitresponse[1:]:
                                            modoptions = f'{modoptions} {x}'
                                        self.connection.privmsg(currentchannel, f'{splitresponse[0]} {chatuser}{modoptions}')
                                        print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - !MOD!-{cfg.username}: {splitresponse[0]} {chatuser}{modoptions}')
                                        f = open (f'Logs/ModTriggers/{currentchannel}_ModTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                        f.write(f'{self.TimeStamp(cfg.LogTimeZone)} TRIGGER EVENT: {chatheader}{chatuser}: {themsg}\r\n')
                                        f.write(f'{self.TimeStamp(cfg.LogTimeZone)} SENT: !MOD!-{cfg.username}: {splitresponse[0]} {chatuser}{modoptions}\r\n')
                                        f.close()
                                    except:
                                        self.connection.privmsg(currentchannel, f'{mresponse} {chatuser}')
                                        print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - !MOD!-{cfg.username}: {mresponse} {chatuser}')
                                        f = open (f'Logs/ModTriggers/{currentchannel}_ModTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                        f.write(f'{self.TimeStamp(cfg.LogTimeZone)} TRIGGER EVENT: {chatheader}{chatuser}: {themsg}\r\n')
                                        f.write(f'{self.TimeStamp(cfg.LogTimeZone)} SENT: !MOD!-{cfg.username}: {mresponse} {chatuser}\r\n')
                                        f.close()
    
    def on_userstate(self, c, e):
        #print(e)
        currentchannel = e.target
        #Detects if cfg.username is a mod in a joined channel and adds it to a list
        for x in e.tags:
            if x['key'] == 'mod':
                if x['value'] == '1':
                    self.dbModChannels.append(currentchannel)
                if str.lower(cfg.username) in currentchannel:
                    self.dbModChannels.append(currentchannel)

    def on_usernotice(self, c, e):
        #print(e)
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
            print(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {sysmsg}')
        
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
        if time.time() - self.sub_epoch >= 5: #A little anti-spam
            if chatuser != cfg.username:
                if sysmsgid == 'sub' and cfg.AnnounceNewSubs:
                    if currentchannel in cfg.AnnounceNewSubsChanMsg:
                        for x in range(len(cfg.AnnounceNewSubsChanMsg[currentchannel])):
                            tmpNewSubMsg = cfg.AnnounceNewSubsChanMsg[currentchannel][x][0]
                            if cfg.AnnounceNewSubsChanMsg[currentchannel][x][1]:
                                tmpNewSubMsg = f'{tmpNewSubMsg} {chatuser}'
                            c.privmsg(currentchannel, tmpNewSubMsg)
                            self.sub_epoch = time.time()
                            if currentchannel not in self.dbModChannels:
                                time.sleep(1.5)
                
                #Subtember allowed users to upgrade a gifted sub for $1 to continue for the next month. Considering it a resub for announce triggers
                if (sysmsgid == 'resub' or sysmsgid == 'giftpaidupgrade') and cfg.AnnounceResubs:
                    if currentchannel in cfg.AnnounceReSubsChanMsg:
                        for x in range(len(cfg.AnnounceReSubsChanMsg[currentchannel])):
                            tmpReSubMsg = cfg.AnnounceReSubsChanMsg[currentchannel][x][0]
                            if cfg.AnnounceReSubsChanMsg[currentchannel][x][1]:
                                tmpReSubMsg = f'{tmpReSubMsg} {chatuser}'
                            c.privmsg(currentchannel, tmpReSubMsg)
                            self.sub_epoch = time.time()
                            if currentchannel not in self.dbModChannels:
                                time.sleep(1.5)
                
                if sysmsgid == 'subgift' and cfg.AnnounceGiftSubs:
                    if currentchannel in cfg.AnnounceGiftSubsChanMsg:
                        for x in range(len(cfg.AnnounceGiftSubsChanMsg[currentchannel])):
                            tmpGiftSubMsg = cfg.AnnounceGiftSubsChanMsg[currentchannel][x][0]
                            if cfg.AnnounceGiftSubsChanMsg[currentchannel][x][1]:
                                tmpGiftSubMsg = f'{tmpGiftSubMsg} {chatuser}'
                            c.privmsg(currentchannel, tmpGiftSubMsg)
                            self.sub_epoch = time.time()
                            if currentchannel not in self.dbModChannels:
                                time.sleep(1.5)
                    
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
        #print(e)
        try:
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
                print(f'CLEARCHAT-{banmsg}')

            if cfg.LogClearchat:
                self.CheckLogDir('clearchat')
                f = open (f'Logs/clearchat/{currentchannel}_clearchat.txt', 'a+', encoding='utf-8-sig')
                f.write(f'{banmsg}\r\n')
                f.close()
        except:
            print(f'Something went wrong on_clearchat:\r\nError:\r\n{e}')

    def on_globaluserstate(self, c, e):
        #Not sure if this is real or not
        print(e)
    
    def on_roomstate(self, c, e):
        #Shows current chat settings for channel
        #type: roomstate, source: tmi.twitch.tv, target: #CHANNEL, arguments: [], tags: [{'key': 'broadcaster-lang', 'value': None}, {'key': 'emote-only', 'value': '0'}, {'key': 'followers-only', 'value': '2'}, {'key': 'r9k', 'value': '0'}, {'key': 'rituals', 'value': '0'}, {'key': 'room-id', 'value': 'XXXXXXXX'}, {'key': 'slow', 'value': '0'}, {'key': 'subs-only', 'value': '0'}]
        #print(e)
        pass
    
    def on_mode(self, c, e):
        #Shows +/- mod permissions
        #print(e)
        
        if cfg.AnnounceModeChanges:
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
        #print(e)

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
        #print(e)
        
        currentchannel = e.target
        chatuser = e.source.split('!')[0]

        if cfg.ChanFilters and currentchannel in cfg.ChanTermFilters:
            pass
        else:
            if cfg.AnnounceUserParts and chatuser in (uname for uname in cfg.AnnounceUserPartList):
                print(f'PART-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {chatuser} has left.')
            elif cfg.AnnounceUserParts and 'GLOBAL' in (uname for uname in cfg.AnnounceUserPartList):
                print(f'PART-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {chatuser} has left.')
    
    def on_action(self, c, e):
        #When a user types /me in the chat and sends a message.
        #type: action, source: mr_protocol!mr_protocol@mr_protocol.tmi.twitch.tv, target: #mr_protocol, arguments: ['testing 12345'], tags: [{'key': 'badges', 'value': 'broadcaster/1,premium/1'}, {'key': 'color', 'value': '#00FF7F'}, {'key': 'display-name', 'value': 'Mr_Protocol'}, {'key': 'emotes', 'value': None}, {'key': 'flags', 'value': None}, {'key': 'id', 'value': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'}, {'key': 'mod', 'value': '0'}, {'key': 'room-id', 'value': 'XXXXXXX'}, {'key': 'subscriber', 'value': '0'}, {'key': 'tmi-sent-ts', 'value': 'XXXXXXXXXXX'}, {'key': 'turbo', 'value': '0'}, {'key': 'user-id', 'value': 'XXXXXXXX'}, {'key': 'user-type', 'value': None}]
        #Used for debugging
        #print(e)     
        self.ChatTextParsing(e)

    def on_hosttarget(self, c, e):
        #Shows hosting info
        #type: hosttarget, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['channelbeinghosted -'], tags: []
        #print(e)

        if cfg.ChanFilters and e.target in cfg.ChanTermFilters:
            pass
        else:
            currentchannel = e.target
            targetchannel = e.arguments[0].split(' ')[0]
            print(f'HOSTTARGET-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} is hosting {targetchannel}.')

    def on_privmsg(self, c, e):
        #type: privmsg, source: jtv!jtv@jtv.tmi.twitch.tv, target: mr_protocol, arguments: ['CutePuppy1337 is now hosting you.'], tags: []
        print(e)
        
        hostmsg = e.arguments
        print(f'{self.TimeStamp(cfg.LogTimeZone)} {hostmsg}')
    
    def on_privnotice(self, c, e):
        #Not sure if this is real or not
        print(e)
    
    def on_pubnotice(self, c, e):
        #Shows hosting message
        #Shows other channel options: slow mode, emote mode, etc.
        #type: pubnotice, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['Now hosting User.'], tags: [{'key': 'msg-id', 'value': 'host_on'}]
        #type: pubnotice, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['Exited host mode.'], tags: [{'key': 'msg-id', 'value': 'host_off'}]
        #type: pubnotice, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['This room is now in subscribers-only mode.'], tags: [{'key': 'msg-id', 'value': 'subs_on'}]
        #type: pubnotice, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['USER has been timed out for 2 seconds.'], tags: [{'key': 'msg-id', 'value': 'timeout_success'}]
        #print(e)

        currentchannel = e.target
        noticemsg = e.arguments[0]

        if cfg.ChanFilters and e.target in cfg.ChanTermFilters:
            pass
        else:           
            print(f'PUBNOTICE-{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {noticemsg}')
            
        if cfg.LogPubnotice:
            self.CheckLogDir('pubnotice')
            f = open (f'Logs/pubnotice/{currentchannel}_pubnotice.txt', 'a+', encoding='utf-8-sig')
            f.write(f'{self.TimeStamp(cfg.LogTimeZone)} {currentchannel} - {noticemsg}\r\n')
            f.close()

    def on_whisper(self, c, e):
        #Received twitch direct messages
        #type: whisper, source: USER!USER@USER.tmi.twitch.tv, target: mr_protocol, arguments: ['THEMESSAGE'], tags: [{'key': 'badges', 'value': None}, {'key': 'color', 'value': None}, {'key': 'display-name', 'value': 'USERNAME'}, {'key': 'emotes', 'value': None}, {'key': 'message-id', 'value': 'XX'}, {'key': 'thread-id', 'value': 'XXXXXX_XXXXXXXX'}, {'key': 'turbo', 'value': '0'}, {'key': 'user-id', 'value': 'XXXXXXXX'}, {'key': 'user-type', 'value': None}]
        #print(e)

        whisper = e.arguments[0]
        for x in e.tags:
            if x['key'] == 'display-name':
                chatuser = x['value']
        print(f'WHISPER-{self.TimeStamp(cfg.LogTimeZone)} Direct Message - {chatuser}: {whisper}')

def tbot():
    input_watcher = InputWatcher()
    input_watcher.start()
    bot = TwitchBot(cfg.username, cfg.token, cfg.channels, input_watcher)
    bot.start()

if __name__ == "__main__":
    tbot()



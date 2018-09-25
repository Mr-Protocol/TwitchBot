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
        system(f'title TwitchBot @ {self.TimeStamp()}  - {cfg.username} in channel(s): {cfg.channels}')
        self.PrintTriggers()
        self.ClearLogs()
        self.DisplayOptions()
        print (f'{self.TimeStamp()}\r\nConnecting to {server} on port {port} as {username}...\r\n')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+token)], username, username)
        self.epoch = 0
        self.dbModChannels = []
        if cfg.EnableKeywordRepeater:
            self.RepeaterEpoch = 0
            self.dbRepeaterKeyword = {}
            splitchans = cfg.channels.split(',')
            for x in splitchans:
                self.dbRepeaterKeyword.update({x: ('', 0)})
    
    def TimeStamp(self):
        if cfg.LogTimeZone:
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
        print (e)
        
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
            print (f'{self.TimeStamp()} {currentchannel}{chatheader}{chatuser}: {themsg}')
        
        #Chat Highlights Log - Will log messages that contain username
        if cfg.LogHighlights and str.lower(cfg.username) in str.lower(themsg):
            self.CheckLogDir('Chat')
            f = open (f'Logs/Chat/{currentchannel}_HighlightsLog.txt', 'a+', encoding='utf-8-sig')
            f.write(f'{self.TimeStamp()} {currentchannel}{chatheader}{chatuser}: {themsg}\r\n')
            f.close()
        
        #Chat Logging To File
        if cfg.LogChatMessages:
            if 'GLOBAL' in cfg.ChatLogChannels or currentchannel in cfg.ChatLogChannels:
                self.CheckLogDir('Chat')
                f = open (f'Logs/Chat/{currentchannel}_ChatLog.txt', 'a+', encoding='utf-8-sig')
                f.write(f'{self.TimeStamp()} {currentchannel}{chatheader}{chatuser}: {themsg}\r\n')
                f.close()
        
        #ASCII ART - Log potential messages for future mod triggers
        if cfg.LogAscii:
            for x in cfg.LogAsciiSet:
                if x in themsg:
                    self.CheckLogDir('Chat')
                    f = open (f'Logs/Chat/{currentchannel}_ASCII.txt', 'a+', encoding='utf-8-sig')
                    f.write(f'{self.TimeStamp()} {currentchannel}{chatheader}{chatuser}: {themsg}\r\n')
                    f.close()
                    break
        
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
        
        #Skip parsing and triggers if the user is a mod/host or in safelist, also if user is a sub
        if isamod == '1':
            pass
        elif str.lower(chatuser) in cfg.SafelistUsers:
            pass
        elif cfg.DontTriggerSubs and isasub == '1':
            pass
        else:        
            #Chat Triggers - uses lcase themsg directly
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
                            f.write(f'{self.TimeStamp()} TRIGGER EVENT: {currentchannel}{chatheader}{chatuser}: {themsg}\r\n')
                            f.close()
                            if time.time() - self.epoch >= 90: #A little anti-spam for triggered words
                                self.epoch = time.time()
                                c.privmsg(currentchannel, cresponse)
                                print(f'{self.TimeStamp()} {currentchannel} - {cfg.username}: {cresponse}')
                                f = open (f'Logs/ChatTriggers/{currentchannel}_ChatTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                f.write(f'{self.TimeStamp()} SENT: {chatheader}{cfg.username}: {cresponse}\r\n')
                                f.close()
           
            #Mod Triggers - uses the lcase themsg and splits words via spaces
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
                                    print(f'{self.TimeStamp()} {currentchannel} - !MOD!-{cfg.username}: {txtreponse}')
                                try:
                                    splitresponse = mresponse.split(' ')
                                    modoptions = ''
                                    for x in splitresponse[1:]:
                                        modoptions = f'{modoptions} {x}'
                                    c.privmsg(currentchannel, f'{splitresponse[0]} {chatuser}{modoptions}')
                                    print(f'{self.TimeStamp()} {currentchannel} - !MOD!-{cfg.username}: {splitresponse[0]} {chatuser}{modoptions}')
                                    f = open (f'Logs/ModTriggers/{currentchannel}_ModTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                    f.write(f'{self.TimeStamp()} TRIGGER EVENT: {chatheader}{chatuser}: {themsg}\r\n')
                                    f.write(f'{self.TimeStamp()} SENT: !MOD!-{cfg.username}: {splitresponse[0]} {chatuser}{modoptions}\r\n')
                                    f.close()
                                except:
                                    c.privmsg(currentchannel, f'{mresponse} {chatuser}')
                                    print(f'{self.TimeStamp()} {currentchannel} - !MOD!-{cfg.username}: {mresponse} {chatuser}')
                                    f = open (f'Logs/ModTriggers/{currentchannel}_ModTriggerLog.txt', 'a+', encoding='utf-8-sig')
                                    f.write(f'{self.TimeStamp()} TRIGGER EVENT: {chatheader}{chatuser}: {themsg}\r\n')
                                    f.write(f'{self.TimeStamp()} SENT: !MOD!-{cfg.username}: {mresponse} {chatuser}\r\n')
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
        if currentchannel in cfg.ChanTermFilters:
            pass
        else:   
            print (f'{self.TimeStamp()} {currentchannel} - {sysmsg}')
        
        #Log system mesages
        if cfg.LogSystemMessages:
            if 'GLOBAL' in cfg.SysMsgLogChannels or currentchannel in cfg.SysMsgLogChannels:
                self.CheckLogDir('System')
                f = open (f'Logs/System/{currentchannel}_SystemMsgLog_{sysmsgid}.txt', 'a+', encoding='utf-8-sig')
                if cfg.RawSystemMsgs: #Log RAW
                    f.write(f'{self.TimeStamp()} {str(e)}\r\n')
                else: #Log Simplified
                    f.write (f'{self.TimeStamp()} {sysmsg}\r\n')
                f.close()
        
        #------------------------- Sub actions -------------------------
        if chatuser != cfg.username:
            if sysmsgid == 'sub' and cfg.AnnounceNewSubs:
                if currentchannel in cfg.AnnounceNewSubsChanMsg:
                    tmpNewSubMsg = cfg.AnnounceNewSubsChanMsg[currentchannel][0][0]
                    if cfg.AnnounceNewSubsChanMsg[currentchannel][0][1]:
                        tmpNewSubMsg = f'{tmpNewSubMsg} {chatuser}'
                    c.privmsg(currentchannel, tmpNewSubMsg)
            
            #Subtember allowed users to upgrade a gifted sub for $1 to continue for the next month. Considering it a resub for announce triggers
            if (sysmsgid == 'resub' or sysmsgid == 'giftpaidupgrade') and cfg.AnnounceResubs:
                if currentchannel in cfg.AnnounceReSubsChanMsg:
                    tmpReSubMsg = cfg.AnnounceReSubsChanMsg[currentchannel][0][0]
                    if cfg.AnnounceReSubsChanMsg[currentchannel][0][1]:
                        tmpReSubMsg = f'{tmpReSubMsg} {chatuser}'
                    c.privmsg(currentchannel, tmpReSubMsg)
            
            if sysmsgid == 'subgift' and cfg.AnnounceGiftSubs:
                if currentchannel in cfg.AnnounceGiftSubsChanMsg:
                    tmpGiftSubMsg = cfg.AnnounceGiftSubsChanMsg[currentchannel][0][0]
                    if cfg.AnnounceGiftSubsChanMsg[currentchannel][0][1]:
                        tmpGiftSubMsg = f'{tmpGiftSubMsg} {chatuser}'
                    c.privmsg(currentchannel, tmpGiftSubMsg)            
                
            if sysmsgid == 'raid' and cfg.AnnounceRaids and currentchannel in cfg.AnnounceRaidChannels:
                c.privmsg(currentchannel, f'{cfg.RaidMsg} {sysmsg} {cfg.RaidMsg}')
            
            #What happens when the cfg.username is gifted a sub
            if sysmsgid == 'subgift' and str.lower(subgiftrecipient) == str.lower(cfg.username):
                c.privmsg(currentchannel, f'{cfg.GiftThanksMsg} {chatuser}')
                f = open (f'Logs/{currentchannel}_GiftedSub.txt', 'a+', encoding='utf-8-sig')
                f.write(f'{self.TimeStamp()} - {sysmsg}\r\n')
                f.write(f'{self.TimeStamp()} - {cfg.username}: {cfg.GiftThanksMsg} {chatuser}\r\n')
                f.close()
        
    def on_clearchat(self, c, e):
        #works
        print (e)
    
    def on_globaluserstate(self, c, e):
        print (e)
    
    def notice(self, c, e):
        print (e)
    
    def on_roomstate(self, c, e):
        print (e)
    
    def on_mode(self, c, e):
        #works
        print (e)

    def on_names(self, c, e):
        print (e)

    def on_join(self, c, e):
        #print (e)
        pass
    
    def on_part(self, c, e):
        #print (e)
        pass
    
    def on_hosttarget(self, c, e):
        print (e)
    
    def on_privmsg(self, c, e):
        print (e)

def main():
    bot = TwitchBot(cfg.username, cfg.token, cfg.channels)
    bot.start()
if __name__ == "__main__":
    main()
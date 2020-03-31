# --------------------------------------------------------------------------
# ---------------------------------- INFO ----------------------------------
# --------------------------------------------------------------------------
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
import threading, _thread
import scriptconfig as cfg
import importlib
import ssl

# --------------------------------------------------------------------------
# ---------------------------------- MAGIC ---------------------------------
# --------------------------------------------------------------------------


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
        self.starttime = time.time()
        self.chatheartbeattime = time.time()
        if input_handler:
            input_handler.register_callback(self.botcommands)
        # Create IRC bot connection
        self.token = token
        self.ClientID = cfg.APIClientID
        self.username = username
        self.configchannels = channels
        server = "irc.chat.twitch.tv"
        port = 6697
        self.checkconfig()
        self.AJChannels = []
        self.JoinedChannelsList = []
        if cfg.FollowerAutoJoin:
            auto_join_follow_thread = threading.Thread(target=self.ajchannels_sync)
            auto_join_follow_thread.daemon = True
            auto_join_follow_thread.start()
        system(f"title TwitchBot @ {self.timestamp()} - {username}")
        print(f"{self.timestamp()}\r\nConnecting to {server} on port {port} as {username}...\r\n")
        factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, "oauth:" + token)], username, username,connect_factory = factory)
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
        if cfg.EnableChatTracking:
            self.dbChatters = {}
            self.ChattersStartTime = self.timestamp(0)
        if cfg.AutoJoinHosts and cfg.LogAutoJoinHostChannels:
            if os.path.exists("Logs/Auto Join Hosts/AutoJoinHostChannels.txt"):
                os.remove("Logs/Auto Join Hosts/AutoJoinHostChannels.txt")
            else:
                print(f"No previous Logs/Auto Join Hosts/AutoJoinHostChannels.txt to delete.\r\n")
        keep_alive_thread = threading.Thread(target=self.keepmealive)
        keep_alive_thread.daemon = True
        keep_alive_thread.start()
        chatheartbeat_thread = threading.Thread(target=self.chatheartbeat)
        chatheartbeat_thread.daemon = True
        chatheartbeat_thread.start()
        ReloadConfig_thread = threading.Thread(target=self.reloadconfigfile)
        ReloadConfig_thread.daemon = True
        ReloadConfig_thread.start()
        self.checklogdir("StartLog")
        f = open(f"Logs/StartLog/StartLog.txt", "a+", encoding="utf-8-sig",)
        f.write(f"{self.timestamp()} - Started - \r\n")
        f.close()
        print(f"- STARTED - {self.timestamp()}\r\n")
        self.newapiheader = {
                    "Authorization": "Bearer " + self.token,
                    "Client-ID:": self.ClientID
                    }

    def keepmealive(self):
        while True:
            try:
                time.sleep(60 * 5)  # 5 min
                print(f"--- PING (Keep Alive) ---")
                self.connection.ping("tmi.twitch.tv")
            except Exception as e:
                self.checklogdir("Error")
                f = open(f"Logs/Error/Error.txt", "a+", encoding="utf-8-sig",)
                f.write(f"{self.timestamp()} - KEEPALIVE ERROR - \r\n")
                f.write(f"{e}\r\n")
                f.close()
                time.sleep(60)
                os.execl(sys.executable, sys.executable, * sys.argv) # Restarts the program.

    # If it doesn't receive a chat message in 1 hour, restart program.
    # Randomly chat will just stop being shown/logged. Not sure why.
    def chatheartbeat(self):
        while True:
            try:
                time.sleep(60 * 60) # 1 hour
                print(f"Checking heartbeat...")
                if (time.time() - self.chatheartbeattime) >= 3600:
                    print(f"{self.timestamp()} - Chat Heartbeat Fail...")
                    self.checklogdir("Error")
                    f = open(f"Logs/Error/Error.txt", "a+", encoding="utf-8-sig",)
                    f.write(f"{self.timestamp()} - Chat Heartbeat Fail...\r\n")
                    f.close()
                    os.execl(sys.executable, sys.executable, * sys.argv)
            except Exception as e:
                print(f"{self.timestamp()} - Chat Heartbeat Fail...")
                self.checklogdir("Error")
                f = open(f"Logs/Error/Error.txt", "a+", encoding="utf-8-sig",)
                f.write(f"{self.timestamp()} - CHATHEARTBEAT ERROR - \r\n")
                f.write(f"{e}\r\n")
                f.close()
                print()

    def ajchannels_sync(self):
        if cfg.APIClientID:
            while True:
                time.sleep(60 * 60 * 2)  # 2 hours
                print(f"Checking followers for updates to auto join...\r\n")
                following = self.apigetfollowerslist(self.username)
                for x in following:
                    if x not in self.JoinedChannelsList:
                        print(f"Found new channel: {x}")
                        self.joinchannel(x)

                # Check the channels variable in config file for new.
                if len(cfg.Channels) != 0:
                    for x in cfg.Channels:
                        if x not in self.JoinedChannelsList:
                            print(f"Found new channel: {x}")
                            self.joinchannel(x)

                else:
                    print(f"Config channels list is empty.\r\n")
        else:
            print(f"No apiclientid in config.")

    def reloadconfigfile(self):
        while True:
            time.sleep(60 * 10)  # 10 min
            importlib.reload(cfg)
            self.checkconfig

    def apigetchannelid(self, channel):
        try:
            if len(str(self.ClientID)) > 2:
                url = "https://api.twitch.tv/helix/users?login=" + channel
                r = requests.get(url, headers=str(self.newapiheader)).json()
                if not r["data"]:
                    print(f"Could not get data for {channel}. User is probably banned.")
                else:
                    channelid = r["data"][0]["id"]
                    return channelid
            else:
                print(f"Get Channel ID - No apiclientid in config.")
        except:
            print(f"Error in apigetchannelid.")

    def apigetuserinfo(self, username):
        if len(str(self.ClientID)) > 2:
            url = "https://api.twitch.tv/kraken/users?login=" + username
            headers = {
                "Client-ID": self.ClientID,
                "Accept": "application/vnd.twitchtv.v5+json",
            }
            r = requests.get(url, headers=headers).json()
            return r
        else:
            print(f"Get User Info - No apiclientid in config.")
    
    def apinewgetuserinfo(self, username):
        if len(self.ClientID) > 2:
            url = "https://api.twitch.tv/helix/users?login=" + username
            r = requests.get(url, headers=str(self.newapiheader)).json()
            return r
        else:
            print(f"Get User Info - apinewgetuser failed.")

    def apigetfollowerslist(self, username, ignorejoinlist = None):
        if len(str(self.ClientID)) > 2:
            followinglist = []
            url = (
                "https://api.twitch.tv/helix/users/follows?from_id="
                + self.apigetchannelid(str.lower(username))
                + "&first=100"
            )
            r = requests.get(url, headers=self.newapiheader).json()
            while len(r["data"]) > 0:
                cursorpage = r["pagination"]["cursor"]
                for x in range(len(r["data"])):
                    followinglist.append("#" + str.lower(r["data"][x]["to_name"]))
                url += "&after=" + cursorpage
                r = requests.get(url, headers=self.newapiheader).json()
            if ignorejoinlist == None:
                if cfg.FollowerAutoJoin and (time.time() - self.starttime < 5):
                    self.AJChannels = followinglist.copy()
                    print(f"Created Auto Join Channel List.\r\n")
            return followinglist
        else:
            print(f"Get Followers List - No apiclientid in config.")

    # Extra chat channels that used to exist until Oct 2019. Commenting out to avoid excessive API usage.
    """ def apiJoinExtraChannels(self, channel_id):
        if cfg.apiclientid:
            if channel_id:
                try:
                    url = "https://api.twitch.tv/kraken/chat/" + channel_id + "/rooms"
                    headers = {
                        "Client-ID": cfg.apiclientid,
                        "Authorization": "OAuth " + self.token,
                        "Accept": "application/vnd.twitchtv.v5+json",
                    }
                    r = requests.get(url, headers=headers).json()
                    if r["_total"] == 0:
                        pass
                    else:
                        for x in range(r["_total"]):
                            time.sleep(0.5)
                            self.joinchannel(
                                "#chatrooms:" + channel_id + ":" + r["rooms"][x]["_id"]
                            )
                except:
                    print("Join Extra Channels - Error - Join Extra Channels")
            else:
                print(f"Skipping apiJoinExtraChannels.")
        else:
            print(f"No apiclientid in config.") """

    def joinchannel(self, channel): # channel name must start with #
        lchannel = str.lower(channel)
        if lchannel not in self.JoinedChannelsList:
            print(f"Attempting to join: {lchannel}")
            self.connection.join(lchannel)
            self.JoinedChannelsList.append(lchannel)
            time.sleep(1)
        """ if "#chatrooms:" in channel: # Used to be used for extra channels, no longer needed as of Oct 2019.
            time.sleep(0.5)
        else:
            self.apiJoinExtraChannels(self.apigetchannelid(channel[1:])) """

    def joinchannellist(self, channel_list):
        for x in channel_list:
            self.joinchannel(x)
            # JOINs are rate-limited to 50 JOINs/commands per 15 seconds. Additional JOINs sent after this will cause an unsuccessful login.
        print("")
    
    def sendmsg(self, channel, message):
        self.connection.privmsg(channel, message)

    def botcommands(self, cmd):
        cmd = str.lower(cmd)
        if cmd == "!enable":
            cfg.EnableBotCommands = 1
            print(f"Commands Enabled")

        if cfg.EnableBotCommands:  # Terminal commands
            try:
                if cmd in {"!commands", "!help"}:
                    print(
                        f"!addmod, !addtrig, !banlist, !bot, !chanfilteron, !chanfilteroff, !chanid, !chantrig, !commands, !getuserfollows, !getuserinfo, !help, !modlist, !reloadconfig, !repeatercount, !repeateroff, !repeateron, !showchatters, !uchatters, !ucount\r\n"
                    )

                elif "!uchatters" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) == 1:
                        print(f"Usage: !uchatters #channel\r\n")
                    else:
                        print(f"There are {len(self.dbChatters[splitcmd[1]])} chatters since {self.ChattersStartTime}. in {splitcmd[1]}")
                        print(f"Current Time: {self.timestamp(0)}\r\n")

                elif "!banlist" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) != 3:
                        print(f"Usage: Create a banlist.txt in the root path of script. One account per line in lowercase. !banlist banlist.txt #channel\r\n")
                    else:
                        try:
                            print(f"Trying bans.")
                            f = open(splitcmd[1],"r")
                            for x in f:
                                print(f"---- Banning {x} in {splitcmd[2]}.")
                                buser = str.lower(str.rstrip(x))
                                bchan = str.lower(str.rstrip(splitcmd[2]))

                                self.sendmsg(bchan, "/ban " + buser + " Suspected spam bot.")
                                time.sleep(.5) #Do not set any lower. Will flood and disconnect bot
                            f.close()
                        except Exception as e:
                            print(f"Something went wrong.\r\n{e}")

                elif "!bot" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) == 1:
                        print(f"Usage: !bot #channel\r\n")
                    else:
                        self.sendmsg(
                            splitcmd[1],
                            f"Beep Bop Boop Beep... I'm not a bot, I'm a real man!",
                        )

                elif "!ucount" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) == 1:
                        print(f"Usage: !ucount #channel username\r\n")
                    else:
                        currentchannel = splitcmd[1]
                        ucountuser = splitcmd[2]
                        try:
                            print(
                                f"The user {ucountuser} has {self.dbChatters[currentchannel][ucountuser]} messages since {self.ChattersStartTime}."
                            )
                            print(f"Current Time: {self.timestamp(0)}\r\n")
                        except:
                            print(f"User not found\r\n")

                elif "!addmod" in cmd:
                    splitcmd = cmd.split(" ", 1)
                    if len(splitcmd) == 1:
                        print(
                            f"Add mod trigger usage: !addmod #channel/GLOBAL,txt_trigger,timeout/ban 2m reason\r\n"
                        )
                    else:
                        try:
                            trigger = splitcmd[1].split(",")
                            cfg.ModTriggers[trigger[0]].append(
                                (trigger[1], trigger[2], None, 1)
                            )
                            print(f"Added ModTrigger {trigger}\r\n")
                        except:
                            trigger = splitcmd[1].split(",")
                            cfg.ModTriggers[trigger[0]] = [
                                (trigger[1], trigger[2], None, 1)
                            ]
                            print(f"Added ModTrigger {trigger}\r\n")

                elif "!addtrig" in cmd:
                    splitcmd = cmd.split(" ", 1)
                    if len(splitcmd) == 1:
                        print(
                            f"Add chat trigger usage: !addtrig #channel/GLOBAL,txt_trigger,response,0/1 tag user\r\n"
                        )
                    else:
                        try:
                            trigger = splitcmd[1].split(",")
                            cfg.ChatTriggers[trigger[0]].append(
                                (trigger[1], trigger[2], trigger[3])
                            )
                            print(f"Added {trigger}\r\n")
                        except:
                            trigger = splitcmd[1].split(",")
                            cfg.ChatTriggers[trigger[0]] = [
                                (trigger[1], trigger[2], trigger[3])
                            ]
                            print(f"Added {trigger}\r\n")

                elif cmd == "!chanfilteron":
                    cfg.ChanFilters = 1
                    print(f"ChanFilters Enabled\r\n")

                elif cmd == "!chanfilteroff":
                    cfg.ChanFilters = 0
                    print(f"ChanFilters Disabled\r\n")

                elif "!chanid" in cmd:
                    splitcmd = cmd.split(" ", 1)
                    if len(splitcmd) == 1:
                        print(f"Get channel id. !chanid channel")
                    else:
                        print(f"{self.apigetchannelid(splitcmd[1])}")

                elif cmd == "!repeateron":
                    cfg.EnableKeywordRepeater = 1
                    print(
                        f"Enabled keyword repeater. Count trigger: {cfg.KeywordRepeaterCount}\r\n"
                    )

                elif cmd == "!repeateroff":
                    cfg.EnableKeywordRepeater = 0
                    print(f"Disabled keyword repeater.\r\n")

                elif "!repeatercount" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) == 1:
                        print(f"Usage: !repeatercount #")
                    else:
                        cfg.KeywordRepeaterCount = splitcmd[1]
                        print(f"Keyword repeater count set to: {splitcmd[1]}\r\n")

                elif "!showchatters" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) == 1:
                        print(
                            f"Shows number of messages and chatters of #channel. Highest to lowest sort."
                        )
                        print(f"Usage: !showchatters #channel\r\n")
                    else:
                        currentchannel = splitcmd[1]
                        sorted_d = sorted(
                            (
                                (value, key)
                                for (key, value) in self.dbChatters[
                                    currentchannel
                                ].items()
                            ),
                            reverse=True,
                        )
                        print(f"Chatters in {currentchannel}: {sorted_d}\r\n")

                elif cmd == "!modlist":
                    print(f"{self.dbModChannels}")

                elif cmd == "!reloadconfig":
                    importlib.reload(cfg)
                    self.checkconfig()

                elif "!getuserfollows" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) == 1:
                        print (
                            f"Writes out the follower list to a file."
                        )
                        print(f"Usage: !getuserfollows mr_protocol\r\n")
                    else:
                        self.checklogdir("FollowList")
                        f = open(f"Logs/FollowList/{splitcmd[1]}.txt", "a+", encoding="utf-8-sig")
                        for x in self.apigetfollowerslist(splitcmd[1],1):
                            f.write(x + '\r\n')
                        f.close()
                        print(f"Done creating follow list. Location: Logs/FollowList/{splitcmd[1]}.txt\r\n")

                elif "!getuserinfo" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) == 1:
                        print (
                            f"Gets both old and new user info via API."
                        )
                        print(f"Usage: !getuserinfo mr_protocol\r\n")
                    else:
                        old = self.apigetuserinfo(splitcmd[1])
                        new = self.apinewgetuserinfo(splitcmd[1])
                        print(f"Old API Info:\r\n{old}\r\nNew API Info:\r\n{new}")
                else:
                    print(f"No Command...\r\n")
            except:
                print(f"Something went wrong...\r\n")

    def timestamp(self, tzone = cfg.LogTimeZone):
        if tzone:
            tstamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            tstamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + "-UTC"
        return f"{tstamp}"

    # Checks config file for basic Chat and Mod trigger errors.
    def checktriggers(self,triggerlist):
        try:
            if triggerlist == cfg.ChatTriggers:
                c = 3
                listname = "Chat Triggers"
            if triggerlist == cfg.ModTriggers:
                c = 4
                listname = "Mod Triggers"
            for x in triggerlist:
                for y in range(len(triggerlist[x])):
                    if len(triggerlist[x][y]) == c:
                        pass
                    else:
                        print(f'Error in config file - {listname}.\r\n {x} - {triggerlist[x][y]}')
                        exit()
        except:
            print(f'Something is broken in config file - {listname}.\r\n')
            exit()

    # Check for valid channels starting with #, and doesn't end with a comma
    def checkconfig(self):
        for chan in self.configchannels:
            if chan.startswith("#"):
                pass
            else:
                print()
                print(
                    "Channels misconfigured, make sure there are # prepending the channel name. \r\n"
                )
                print(chan)
                exit()
        if self.username == "":
            print(f"Error: No username defined")
            exit()
        if self.token == "":
            print(f"Error: No OAUTH token defined")
            exit()
        if cfg.FollowerAutoJoin:
            if cfg.APIClientID == "":
                print(f"Error: FollowerAutoJoin enabled without APIClientID")
                exit()
        self.checktriggers(cfg.ChatTriggers)
        self.checktriggers(cfg.ModTriggers)

    def checklogdir(self, logpath):
        if not os.path.exists(f"Logs/{logpath}/"):
            try:
                os.makedirs(f"Logs/{logpath}/")
            except OSError as error:
                if error.errno != errno.EEXIST:
                    raise

    def chatlogmessage(self, currentchannel, message):
        if cfg.EnableLogChatMessages:
            if "GLOBAL" in cfg.ChatLogChannels or currentchannel in cfg.ChatLogChannels:
                self.checklogdir("Chat")
                logchan = re.sub(":", "_", currentchannel)
                f = open(
                    f"Logs/Chat/{logchan}_ChatLog.txt",
                    "a+",
                    encoding="utf-8-sig",
                )
                f.write(f"{message}\r\n")
                f.close()

    def chattextparsing(self, edata):
        self.chatheartbeattime = time.time() # Update time for chat heartbeat
        e = edata
        themsg = e.arguments[0]
        currentchannel = e.target
        logchan = re.sub(":", "_", currentchannel)
        isamod = False
        isavip = False
        isasub = False
        # Used for debugging.
        # print(e)

        # Chat log with usernames and Moderator status.
        for x in e.tags:
            if x["key"] == "display-name":
                chatuser = x["value"]
            if x["key"] == "subscriber":
                if x["value"] == "1":
                    isasub = True
            if x["key"] == "mod":
                if x["value"] == "1":
                    isamod = True
            if x["key"] == "badges":
                if "vip" in str(x["value"]):
                    isavip = True
                else:
                    isavip = False

        if str.lower(chatuser) == str.lower(self.username) and isamod: # Add channel to bot's channel mod list
            if currentchannel not in self.dbModChannels:
                self.dbModChannels.append(currentchannel)
        
        if str.lower(chatuser) == str.lower(self.username) and not isamod: # Remove channel from bot's channel mod list
            if currentchannel in self.dbModChannels:
                self.dbModChannels.remove(currentchannel)

        chatheader = " - "
        if str.lower(chatuser) in currentchannel:
            chatheader = chatheader + "!HOST!-"
        if isamod:
            chatheader = chatheader + "!MOD!-"
        if isavip:
            chatheader = chatheader + "!VIP!-"
        if isasub:
            chatheader = chatheader + "!SUB!-"

        # Terminal Chat Log - Prepend Host/Mod status to accounts in chat.
        # Filter channels using ChanTermFilters to hide channel(s) chat from terminal
        if cfg.ChanFilters and currentchannel not in cfg.ChanTermFilters:
            pass
        else:
            print(
                f"{self.timestamp()} {currentchannel}{chatheader}{chatuser}: {themsg}"
            )

        # Chat Highlights Log - Will log messages that contain username
        if cfg.LogHighlights and str.lower(self.username) in str.lower(themsg):
            self.checklogdir("Highlights")
            f = open(
                f"Logs/Highlights/{logchan}_HighlightsLog.txt",
                "a+",
                encoding="utf-8-sig",
            )
            f.write(
                f"{self.timestamp()} {currentchannel}{chatheader}{chatuser}: {themsg}\r\n"
            )
            f.close()

        # Chat Logging To File
        self.chatlogmessage(
            currentchannel,
            self.timestamp()
            + " "
            + currentchannel
            + chatheader
            + chatuser
            + ": "
            + themsg,
        )

        # ASCII ART - Log potential messages for future mod triggers
        if cfg.LogAscii:
            if any(x in cfg.LogAsciiSet for x in themsg):
                self.checklogdir("ASCII")
                f = open(
                    f"Logs/ASCII/{logchan}_ASCII.txt", "a+", encoding="utf-8-sig"
                )
                f.write(
                    f"{self.timestamp()} {currentchannel}{chatheader}{chatuser}: {themsg}\r\n"
                )
                f.close()

        # Repeater Mode aka Giveaway Mode
        if cfg.EnableKeywordRepeater:  # Counting keyword
            if currentchannel in self.dbRepeaterKeyword:
                pass
            else:
                self.dbRepeaterKeyword.update({currentchannel: ("", 0)})            
            
            if self.dbRepeaterKeyword[currentchannel][0] == themsg:
                self.dbRepeaterKeyword.update(
                    {
                        currentchannel: (
                            themsg,
                            self.dbRepeaterKeyword[currentchannel][1] + 1,
                        )
                    }
                )
                if self.dbRepeaterKeyword[currentchannel][1] >= cfg.KeywordRepeaterCount:
                    if time.time() - self.RepeaterEpoch >= 30:  # A little anti-spam
                        self.sendmsg(currentchannel, themsg)
                        self.dbRepeaterKeyword.update({currentchannel: ("", 0)})
                        self.RepeaterEpoch = time.time()
            else:  # New keyword
                self.dbRepeaterKeyword.update({currentchannel: (themsg, 0)})

        # CopyPasta Mode
        if cfg.EnableCopyPasta:
            if currentchannel in cfg.CopyPastaTriggers:
                for x in range(len(cfg.CopyPastaTriggers[currentchannel])):
                    if str.lower(cfg.CopyPastaTriggers[currentchannel][x]) in str.lower(
                        themsg
                    ):
                        if time.time() - self.epochCopyPasta >= 90:
                            self.epochCopyPasta = time.time()
                            self.sendmsg(currentchannel, themsg)
                            print(f"{self.timestamp()} {currentchannel} {self.username}: {themsg}\r\n")

        # Tracking Chatters Info
        if cfg.EnableChatTracking:
            if currentchannel in self.dbChatters:
                if str.lower(chatuser) in self.dbChatters[currentchannel]:
                    self.dbChatters[currentchannel][str.lower(chatuser)] += 1
                else:
                    self.dbChatters[currentchannel][str.lower(chatuser)] = 1
            else:
                self.dbChatters[currentchannel] = {str.lower(chatuser): 1}

        # Chat Triggers - uses lcase themsg directly
        if cfg.EnableChatTriggers:
            for ChanAndGlobal in cfg.ChatTriggers:
                if currentchannel == ChanAndGlobal or ChanAndGlobal == "GLOBAL":
                    for x in range(len(cfg.ChatTriggers[ChanAndGlobal])):
                        if str.lower(cfg.ChatTriggers[ChanAndGlobal][x][0]) in str.lower(themsg):
                            cresponse = cfg.ChatTriggers[ChanAndGlobal][x][1]
                            if cfg.ChatTriggers[ChanAndGlobal][x][2]:
                                cresponse = f"{cresponse} {chatuser}"
                            if cfg.AutomatedRespondEnabled:
                                cresponse = f"{cresponse} {cfg.AutomatedResponseMsg}"
                            # Log it
                            self.checklogdir("ChatTriggers")
                            f = open(
                                f"Logs/ChatTriggers/{logchan}_ChatTriggerLog.txt",
                                "a+",
                                encoding="utf-8-sig",
                            )
                            f.write(f"{self.timestamp()} TRIGGER EVENT: {currentchannel}{chatheader}{chatuser}: {themsg}\r\n")
                            f.close()
                            if currentchannel in self.dbModChannels or (time.time() - self.chat_epoch >= 30):  # A little anti-spam for triggered words
                                if currentchannel not in self.dbModChannels:
                                    self.chat_epoch = time.time()
                                if str.lower(self.username) == str.lower(chatuser):
                                    time.sleep(1.5)
                                self.sendmsg(currentchannel, cresponse)
                                print(f"{self.timestamp()} {currentchannel} - {self.username}: {cresponse}")
                                f = open(
                                    f"Logs/ChatTriggers/{logchan}_ChatTriggerLog.txt",
                                    "a+",
                                    encoding="utf-8-sig",
                                )
                                f.write(f"{self.timestamp()} SENT: {chatheader}{self.username}: {cresponse}\r\n")
                                f.close()

        # Mod Triggers - uses the lcase themsg and splits words via spaces
        if cfg.EnableModTriggers:
            # Skip parsing and triggers if the user is a mod/host, VIP, or in safelist, also if user is a sub
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
                        if currentchannel == ChanAndGlobal or ChanAndGlobal == "GLOBAL":
                            for x in range(len(cfg.ModTriggers[ChanAndGlobal])):
                                if str.lower(cfg.ModTriggers[ChanAndGlobal][x][0]) in str.lower(themsg):
                                    mresponse = cfg.ModTriggers[ChanAndGlobal][x][1]
                                    self.checklogdir("ModTriggers")
                                    # Handle mod text response
                                    if cfg.ModTriggers[ChanAndGlobal][x][2]:
                                        txtreponse = cfg.ModTriggers[ChanAndGlobal][x][2]
                                        if cfg.ModTriggers[ChanAndGlobal][x][3]:
                                            txtreponse = f"{txtreponse} {chatuser}"
                                        self.sendmsg(currentchannel, f"{txtreponse}")
                                        print(f"{self.timestamp()} {currentchannel} - !MOD!-{self.username}: {txtreponse}")
                                    try:
                                        splitresponse = mresponse.split(" ")
                                        modoptions = ""
                                        for x in splitresponse[1:]:
                                            modoptions = f"{modoptions} {x}"
                                        self.sendmsg(currentchannel, f"{splitresponse[0]} {chatuser}{modoptions}",)
                                        print(f"{self.timestamp()} {currentchannel} - !MOD!-{self.username}: {splitresponse[0]} {chatuser}{modoptions}")
                                        f = open(
                                            f"Logs/ModTriggers/{logchan}_ModTriggerLog.txt",
                                            "a+",
                                            encoding="utf-8-sig",
                                        )
                                        f.write(f"{self.timestamp()} TRIGGER EVENT: {chatheader}{chatuser}: {themsg}\r\n")
                                        f.write(f"{self.timestamp()} SENT: !MOD!-{self.username}: {splitresponse[0]} {chatuser}{modoptions}\r\n")
                                        f.close()
                                    except:
                                        self.sendmsg(currentchannel, f"{mresponse} {chatuser}")
                                        print(f"{self.timestamp()} {currentchannel} - !MOD!-{self.username}: {mresponse} {chatuser}")
                                        f = open(
                                            f"Logs/ModTriggers/{logchan}_ModTriggerLog.txt",
                                            "a+",
                                            encoding="utf-8-sig",
                                        )
                                        f.write(f"{self.timestamp()} TRIGGER EVENT: {chatheader}{chatuser}: {themsg}\r\n")
                                        f.write(f"{self.timestamp()} SENT: !MOD!-{self.username}: {mresponse} {chatuser}\r\n")
                                        f.close()

    def on_welcome(self, c, e):
        # You must request specific capabilities before you can use them
        c.cap("REQ", ":twitch.tv/membership")
        c.cap("REQ", ":twitch.tv/tags")
        c.cap("REQ", ":twitch.tv/commands")

        # joins channels you are following if enabled
        if cfg.FollowerAutoJoin:
            print(f"Joining all followed channels.\r\n")
            self.joinchannellist(self.apigetfollowerslist(self.username))

        # joins specified channels
        if len(self.configchannels) > 0:
            print(f"Joining list of channels.")
            self.joinchannellist(self.configchannels)

    def on_pubmsg(self, c, e):
        # print(e)
        self.chattextparsing(e)

    def on_userstate(self, c, e):
        # print(e)
        currentchannel = e.target
        # Detects if self.username is a mod in a joined channel and adds it to a list
        for x in e.tags:
            if x["key"] == "mod":
                if x["value"] == "1":
                    if currentchannel not in self.dbModChannels:
                        self.dbModChannels.append(currentchannel)
                if (str.lower(self.username) in currentchannel):  # Add your own channel to mod list
                    if currentchannel not in self.dbModChannels:
                        self.dbModChannels.append(currentchannel)

    def on_usernotice(self, c, e):
        # print(e)
        currentchannel = e.target
        logchan = re.sub(":", "_", currentchannel)
        for x in e.tags:
            if x["key"] == "msg-id":
                sysmsgid = x["value"]
            if x["key"] == "display-name":
                chatuser = x["value"]
            if x["key"] == "system-msg":
                sysmsg = re.sub(
                    "\r|\n", "", x["value"]
                )  # Removes \r and \n because Twitch is stupid and puts a \n mid string.
            if x["key"] == "msg-param-recipient-display-name":
                subgiftrecipient = x["value"]

        # Filter channels from terminal output
        if cfg.ChanFilters and currentchannel not in cfg.ChanTermFilters:
            pass
        else:
            print(f"{self.timestamp()} {currentchannel} - {sysmsg}")

        # Log system mesages
        if cfg.LogSystemMessages:
            if (
                "GLOBAL" in cfg.SysMsgLogChannels
                or currentchannel in cfg.SysMsgLogChannels
            ):
                self.checklogdir("System")
                f = open(
                    f"Logs/System/{logchan}_SystemMsgLog_{sysmsgid}.txt",
                    "a+",
                    encoding="utf-8-sig",
                )
                if cfg.RawSystemMsgs:  # Log RAW
                    f.write(f"{self.timestamp()} {str(e)}\r\n")
                else:  # Log Simplified
                    f.write(f"{self.timestamp()} {sysmsg}\r\n")
                f.close()

        # ------------------------- Sub actions -------------------------
        if time.time() - self.sub_epoch >= 5:  # A little anti-spam
            if chatuser != self.username:
                if sysmsgid == "sub" and cfg.AnnounceNewSubs:
                    if currentchannel in cfg.AnnounceNewSubsChanMsg:
                        for x in range(len(cfg.AnnounceNewSubsChanMsg[currentchannel])):
                            tmpNewSubMsg = cfg.AnnounceNewSubsChanMsg[currentchannel][x][0]
                            if cfg.AnnounceNewSubsChanMsg[currentchannel][x][1]:
                                tmpNewSubMsg = f"{tmpNewSubMsg} {chatuser}"
                            c.privmsg(currentchannel, tmpNewSubMsg)
                            self.sub_epoch = time.time()
                            if currentchannel not in self.dbModChannels:
                                time.sleep(1.5)

                # Subtember allowed users to upgrade a gifted sub for $1 to continue for the next month. Considering it a resub for announce triggers
                if (
                    sysmsgid == "resub" or sysmsgid == "giftpaidupgrade"
                ) and cfg.AnnounceResubs:
                    if currentchannel in cfg.AnnounceReSubsChanMsg:
                        for x in range(len(cfg.AnnounceReSubsChanMsg[currentchannel])):
                            tmpReSubMsg = cfg.AnnounceReSubsChanMsg[currentchannel][x][0]
                            if cfg.AnnounceReSubsChanMsg[currentchannel][x][1]:
                                tmpReSubMsg = f"{tmpReSubMsg} {chatuser}"
                            c.privmsg(currentchannel, tmpReSubMsg)
                            self.sub_epoch = time.time()
                            if currentchannel not in self.dbModChannels:
                                time.sleep(1.5)

                if sysmsgid == "subgift" and cfg.AnnounceGiftSubs:
                    if currentchannel in cfg.AnnounceGiftSubsChanMsg:
                        for x in range(
                            len(cfg.AnnounceGiftSubsChanMsg[currentchannel])
                        ):
                            tmpGiftSubMsg = cfg.AnnounceGiftSubsChanMsg[currentchannel][x][0]
                            if cfg.AnnounceGiftSubsChanMsg[currentchannel][x][1]:
                                tmpGiftSubMsg = f"{tmpGiftSubMsg} {chatuser}"
                            c.privmsg(currentchannel, tmpGiftSubMsg)
                            self.sub_epoch = time.time()
                            if currentchannel not in self.dbModChannels:
                                time.sleep(1.5)

        if (
            sysmsgid == "raid"
            and cfg.AnnounceRaids
            and currentchannel in cfg.AnnounceRaidChannels
        ):
            c.privmsg(currentchannel, f"{cfg.RaidMsg} {sysmsg} {cfg.RaidMsg}")

        # What happens when the self.username is gifted a sub
        if cfg.EnableThankYou:
            if sysmsgid == "subgift" and str.lower(subgiftrecipient) == str.lower(self.username):
                c.privmsg(currentchannel, f"{cfg.GiftThanksMsg} {chatuser}")
                f = open(
                    f"Logs/{logchan}_GiftedSub.txt", "a+", encoding="utf-8-sig"
                )
                f.write(f"{self.timestamp()} - {sysmsg}\r\n")
                f.write(
                    f"{self.timestamp()} - {self.username}: {cfg.GiftThanksMsg} {chatuser}\r\n"
                )
                f.close()

    def on_clearchat(self, c, e):
        # Shows when a user is banned
        # Mod uses /clear chat command
        # print(e)
        if not e.arguments:
            print(f"Mod used /clear on {e.target}")
        else:
            try:
                currentchannel = e.target
                logchan = re.sub(":", "_", currentchannel)
                user = e.arguments[0]
                banduration = None
                banreason = None

                for x in e.tags:
                    if x["key"] == "ban-duration":
                        banduration = x["value"]
                    if x["key"] == "ban-reason":
                        banreason = x["value"]

                if banduration:
                    if banreason:
                        banmsg = f"{self.timestamp()} {currentchannel} - {user} timeout for {banduration} seconds. {banreason}"
                    else:
                        banmsg = f"{self.timestamp()} {currentchannel} - {user} timeout for {banduration} seconds."
                else:
                    if banreason:
                        banmsg = f"{self.timestamp()} {currentchannel} - {user} is banned. {banreason}"
                    else:
                        banmsg = f"{self.timestamp()} {currentchannel} - {user} is banned."

                if cfg.ChanFilters and e.target not in cfg.ChanTermFilters:
                    pass
                else:
                    print(f"CLEARCHAT-{banmsg}")

                if cfg.LogClearchat:
                    self.chatlogmessage(currentchannel,banmsg)
                    self.checklogdir("clearchat")
                    f = open(
                        f"Logs/clearchat/{logchan}_clearchat.txt",
                        "a+",
                        encoding="utf-8-sig",
                    )
                    f.write(f"{banmsg}\r\n")
                    f.close()
            except:
                print(f"Something went wrong on_clearchat:\r\nError:\r\n{e}")

    def on_globaluserstate(self, c, e):
        # Not sure if this is real or not
        print(e)
        self.checklogdir("globaluserstate")
        f = open(
            f"Logs/globaluserstate/dump.txt",
            "a+",
            encoding="utf-8-sig",
        )
        f.write(f"\r\n {e}")
        f.close()

    def on_roomstate(self, c, e):
        # Shows current chat settings for channel
        # type: roomstate, source: tmi.twitch.tv, target: #CHANNEL, arguments: [], tags: [{'key': 'broadcaster-lang', 'value': None}, {'key': 'emote-only', 'value': '0'}, {'key': 'followers-only', 'value': '2'}, {'key': 'r9k', 'value': '0'}, {'key': 'rituals', 'value': '0'}, {'key': 'room-id', 'value': 'XXXXXXXX'}, {'key': 'slow', 'value': '0'}, {'key': 'subs-only', 'value': '0'}]
        # print(e)
        pass

    def on_mode(self, c, e):
        # Shows +/- mod permissions
        # print(e)

        if cfg.AnnounceModeChanges:
            if cfg.ChanFilters and e.target not in cfg.ChanTermFilters:
                pass
            else:
                currentchannel = e.target
                modstatus = e.arguments
                if modstatus[0] == "+o":
                    print(
                        f"MODE-{self.timestamp()} {currentchannel} +o {modstatus[1]} (mod)."
                    )
                    self.chatlogmessage(
                        currentchannel,
                        self.timestamp()
                        + " "
                        + currentchannel
                        + ": "
                        + modstatus[1],
                    )
                elif modstatus[0] == "-o":
                    print(
                        f"MODE-{self.timestamp()} {currentchannel} -o {modstatus[1]} (demod)."
                    )
                    self.chatlogmessage(
                        currentchannel,
                        self.timestamp()
                        + " "
                        + currentchannel
                        + ": "
                        + modstatus[1],
                    )
                else:
                    print(
                        f"MODE-{self.timestamp()} {currentchannel} {modstatus}"
                    )
                    self.chatlogmessage(
                        currentchannel,
                        self.timestamp()
                        + " "
                        + currentchannel
                        + ": "
                        + modstatus,
                    )

    def on_join(self, c, e):
        # User joins the channel
        # print(e)

        currentchannel = e.target
        chatuser = e.source.split("!")[0]

        if cfg.ChatLogJoinPart:
            self.chatlogmessage(
                currentchannel,
                self.timestamp()
                + " "
                + currentchannel
                + " - "
                + chatuser
                + " has joined.",
            )

        if cfg.ChanFilters and currentchannel not in cfg.ChanTermFilters:
            pass
        else:
            if cfg.AnnounceUserJoins and chatuser in (
                uname for uname in cfg.AnnounceUserJoinList
            ):
                print(
                    f"JOIN-{self.timestamp()} {currentchannel} - {chatuser} has joined."
                )
            elif cfg.AnnounceUserJoins and "GLOBAL" in (
                uname for uname in cfg.AnnounceUserJoinList
            ):
                print(
                    f"JOIN-{self.timestamp()} {currentchannel} - {chatuser} has joined."
                )

    def on_part(self, c, e):
        # User parts or leaves channel
        # print(e)

        currentchannel = e.target
        chatuser = e.source.split("!")[0]
        if cfg.ChatLogJoinPart:
            self.chatlogmessage(
                currentchannel,
                self.timestamp()
                + " "
                + currentchannel
                + " - "
                + chatuser
                + " has left.",
            )

        if cfg.ChanFilters and currentchannel not in cfg.ChanTermFilters:
            pass
        else:
            if cfg.AnnounceUserParts and chatuser in (
                uname for uname in cfg.AnnounceUserPartList
            ):
                print(
                    f"PART-{self.timestamp()} {currentchannel} - {chatuser} has left."
                )
            elif cfg.AnnounceUserParts and "GLOBAL" in (
                uname for uname in cfg.AnnounceUserPartList
            ):
                print(
                    f"PART-{self.timestamp()} {currentchannel} - {chatuser} has left."
                )

    def on_action(self, c, e):
        # When a user types /me in the chat and sends a message.
        # type: action, source: mr_protocol!mr_protocol@mr_protocol.tmi.twitch.tv, target: #mr_protocol, arguments: ['testing 12345'], tags: [{'key': 'badges', 'value': 'broadcaster/1,premium/1'}, {'key': 'color', 'value': '#00FF7F'}, {'key': 'display-name', 'value': 'Mr_Protocol'}, {'key': 'emotes', 'value': None}, {'key': 'flags', 'value': None}, {'key': 'id', 'value': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'}, {'key': 'mod', 'value': '0'}, {'key': 'room-id', 'value': 'XXXXXXX'}, {'key': 'subscriber', 'value': '0'}, {'key': 'tmi-sent-ts', 'value': 'XXXXXXXXXXX'}, {'key': 'turbo', 'value': '0'}, {'key': 'user-id', 'value': 'XXXXXXXX'}, {'key': 'user-type', 'value': None}]
        # Used for debugging
        # print(e)
        self.chattextparsing(e)

    def on_hosttarget(self, c, e):
        # Shows hosting info
        # type: hosttarget, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['channelbeinghosted -'], tags: []
        # print(e)
        if cfg.ChanFilters and e.target not in cfg.ChanTermFilters:
            pass
        else:
            currentchannel = e.target
            targetchannel = e.arguments[0].split(" ")[0]
            print(
                f"HOSTTARGET-{self.timestamp()} {currentchannel} is hosting {targetchannel}."
            )

    def on_privmsg(self, c, e):
        # type: privmsg, source: jtv!jtv@jtv.tmi.twitch.tv, target: mr_protocol, arguments: ['CutePuppy1337 is now hosting you.'], tags: []
        print(e)

        hostmsg = e.arguments
        print(f"{self.timestamp()} {hostmsg}")

    def on_privnotice(self, c, e):
        # type: privnotice, source: tmi.twitch.tv, target: l, arguments: ['This channel has been suspended.'], tags: [{'key': 'msg-id', 'value': 'msg_channel_suspended'}]
        print(e)

    def on_pubnotice(self, c, e):
        # Shows hosting message
        # Shows other channel options: slow mode, emote mode, etc.
        # print(e)

        currentchannel = e.target
        logchan = re.sub(":", "_", currentchannel)
        noticemsg = e.arguments[0]

        if cfg.ChanFilters and e.target not in cfg.ChanTermFilters:
            pass
        else:
            print(
                f"PUBNOTICE-{self.timestamp()} {currentchannel} - {noticemsg}"
            )

        if cfg.LogPubnotice:
            self.checklogdir("pubnotice")
            f = open(
                f"Logs/pubnotice/{logchan}_pubnotice.txt",
                "a+",
                encoding="utf-8-sig",
            )
            f.write(
                f"{self.timestamp()} {currentchannel} - {noticemsg}\r\n"
            )
            f.close()
        
        if cfg.AutoJoinHosts and noticemsg[:11] == "Now hosting":
            LAJHChan = "#" + str.lower(noticemsg[12:][:-1]) # Parse the hosted channel from noticemsg, LCase, prefix with #
            if LAJHChan not in self.JoinedChannelsList:
                print(f"Found new channel {LAJHChan}.")
                time.sleep(2)
                self.joinchannel(LAJHChan)
                if cfg.AnnounceAutoJoinHosts:
                    c.privmsg(LAJHChan, f"Hello, {currentchannel[1:]} sent me via hosting.")
                if cfg.LogAutoJoinHosts:
                    self.checklogdir("Auto Join Hosts")
                    f = open(
                        f"Logs/Auto Join Hosts/{logchan}_AutoJoinHosts.txt",
                        "a+",
                        encoding="utf-8-sig",
                    )
                    f.write(f"{self.timestamp()} {LAJHChan} - Auto Joining Hosted Channel via {currentchannel}")
                    f.close
                if cfg.LogAutoJoinHostChannels:
                    self.checklogdir("Auto Join Hosts")
                    f = open(
                        f"Logs/Auto Join Hosts/AutoJoinHostChannels.txt",
                        "a+",
                        encoding="utf-8-sig",
                    )
                    f.write(f"{LAJHChan}\r\n")
                    f.close
            else:
                print(f"Channel {LAJHChan} already joined.")

    def on_whisper(self, c, e):
        # Received twitch direct messages
        # type: whisper, source: USER!USER@USER.tmi.twitch.tv, target: mr_protocol, arguments: ['THEMESSAGE'], tags: [{'key': 'badges', 'value': None}, {'key': 'color', 'value': None}, {'key': 'display-name', 'value': 'USERNAME'}, {'key': 'emotes', 'value': None}, {'key': 'message-id', 'value': 'XX'}, {'key': 'thread-id', 'value': 'XXXXXX_XXXXXXXX'}, {'key': 'turbo', 'value': '0'}, {'key': 'user-id', 'value': 'XXXXXXXX'}, {'key': 'user-type', 'value': None}]
        # print(e)

        whisper = e.arguments[0]
        for x in e.tags:
            if x["key"] == "display-name":
                chatuser = x["value"]
        print(
            f"WHISPER-{self.timestamp()} Direct Message - {chatuser}: {whisper}"
        )


def tbot(uname, utoken, uchannels, input_watcher = None):
    bot = TwitchBot(uname, utoken, uchannels, input_watcher)
    bot.start()
    

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    time.sleep(1)
    input_watcher = InputWatcher()
    input_watcher.start()
    botthread1 = threading.Thread(target=tbot,args=[str.lower(cfg.Username), cfg.Token, cfg.Channels, input_watcher])
    botthread1.start()

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

from datetime import timezone
import sys
import irc.bot
import requests
import time
import datetime
import shutil
import re
import os
import errno
import threading, _thread
import inspect
import importlib
import ssl
import json
import TwitchOAuth as TOA
import scriptconfig as cfg
import sqlite3
import queue


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
        self.chatheartbeattime = int(time.time())
        if input_handler:
            input_handler.register_callback(self.botcommands)
        # Create IRC bot connection
        try:
            with open('JSON/clientdata.json','r') as clientf:
                clientdata = json.load(clientf)
                clientf.close()
        except Exception as e:
            print(e)
        self.token = token
        self.ClientID = clientdata['client_id']
        self.botuserid = clientdata['user_id']
        self.username = username
        self.configchannels = channels
        server = "irc.chat.twitch.tv"
        # Original Port
        # port = 6667
        port = 6697
        self.checkconfig()
        self.AJChannels = []
        self.JoinedChannelsList = []
        if cfg.FollowerAutoJoin:
            auto_join_follow_thread = threading.Thread(target=self.ajchannels_sync)
            auto_join_follow_thread.daemon = True
            auto_join_follow_thread.start()
        # system(f"title TwitchBot @ {self.timestamp()} - {username}")
        print(f"{self.timestamp()}\r\nConnecting to {server} on port {port} as {username}...\r\n")
        context = ssl.create_default_context()
        factory = irc.connection.Factory(wrapper=lambda sock: context.wrap_socket(sock, server_hostname=server))
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, "oauth:" + self.token)], username, username,connect_factory = factory)
        # Original connect command, plaintext connection
        # irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+token)], username, username)
        self.sub_epoch = 0
        if cfg.EnableModTriggers:
            self.dbModChannels = []
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
        self.apiheader = {
                    "Authorization": "Bearer " + self.token,
                    "Client-ID": self.ClientID
                    }
        self.apiheaderpost = {
                    "Authorization": "Bearer " + self.token,
                    "Client-ID": self.ClientID,
                    "Content-Type": "application/json"
                    }

        # Create a queue for user changes
        self.user_change_queue = queue.Queue()

        # Create the database connection and cursor
        self.conn = sqlite3.connect('user_log.db')
        self.c = self.conn.cursor()

        # Create the users table if it doesn't exist
        self.c.execute('''CREATE TABLE IF NOT EXISTS users
                          (timestamp INTEGER, userID TEXT, username TEXT, channel TEXT)''')

        # Commit the table creation and close the cursor
        self.conn.commit()
        self.c.close()

        # Start a separate thread to handle user changes
        threading.Thread(target=self.process_user_changes, daemon=True).start()

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

    def apiheaderupdate(self):
        self.apiheader = {
                    "Authorization": "Bearer " + self.token,
                    "Client-ID": self.ClientID
                    }
        self.apiheaderpost = {
                    "Authorization": "Bearer " + self.token,
                    "Client-ID": self.ClientID,
                    "Content-Type": "application/json"
                    }

    # If it doesn't receive a chat message in 1 hour, restart program.
    # Randomly chat will just stop being shown/logged. Not sure why.
    def chatheartbeat(self):
        while True:
            try:
                time.sleep(60 * 60) # 1 hour
                print(f"Checking token.")
                self.token = TOA.checktoken()
                self.apiheaderupdate()
                print(f"Checking heartbeat...")
                if (int(time.time()) - self.chatheartbeattime) >= 3600:
                    print(f"{self.timestamp()} - Chat Heartbeat Fail...")
                    self.checklogdir("Error")
                    f = open(f"Logs/Error/Error.txt", "a+", encoding="utf-8-sig",)
                    f.write(f"{self.timestamp()} - Chat Heartbeat Fail...\r\n")
                    f.close()
                    os.execl(sys.executable, sys.executable, * sys.argv)
            except Exception as e:
                print(f"{self.timestamp()} - Chat Heartbeat Error...")
                self.checklogdir("Error")
                f = open(f"Logs/Error/Error.txt", "a+", encoding="utf-8-sig",)
                f.write(f"{self.timestamp()} - CHATHEARTBEAT ERROR - \r\n")
                f.write(f"{e}\r\n")
                f.close()
                print()

    def checklogdir(self, logpath):
        if not os.path.exists(f"Logs/{logpath}/"):
            try:
                os.makedirs(f"Logs/{logpath}/")
            except OSError as error:
                if error.errno != errno.EEXIST:
                    raise

    def ajchannels_sync(self):
        while True:
            time.sleep(60 * 60 * 2)  # 2 hours
            print(f"Checking followers for updates to auto join...\r\n")
            following = self.apigetfollowerslist(self.username, self.botuserid)
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

    def convert_event_to_json(self, event):
        json_data = {
            'type': event.type,
            'source': event.source,
            'target': event.target,
            'arguments': event.arguments
        }

        if event.tags:
            if isinstance(event.tags, list):
                for tag in event.tags:
                    json_data[tag['key']] = tag['value']
            elif isinstance(event.tags, dict):
                json_data.update(event.tags)

        return json_data
    
    def reloadconfigfile(self):
        while True:
            time.sleep(60 * 10)  # 10 min
            importlib.reload(cfg)
            self.checkconfig

    def log_user_change(self, userID, username, channel, timestamp, conn):
        # Check if the user already exists in the database
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE userID=? AND username=?", (userID, username))
        if c.fetchone() is not None:
            # User already exists, discard and continue
            return

        # User doesn't exist, insert new user data with timestamp and channel
        c.execute("INSERT INTO users (timestamp, userID, username, channel) VALUES (?, ?, ?, ?)", (timestamp, userID, username, channel))
        conn.commit()

    def process_user_changes(self):
        while True:
            # Retrieve the user change data from the queue
            userID, username, channel, timestamp = self.user_change_queue.get()
            # Create a new SQLite connection for each thread
            with sqlite3.connect('user_log.db') as conn:
                # Log the user change
                self.log_user_change(userID, username, channel, timestamp, conn)

            # Mark the task as done
            self.user_change_queue.task_done()

    def apigetchannelid(self, channel):
        try:
            print(f"Checking token.")
            self.token = TOA.checktoken()
            self.apiheaderupdate()
            if len(str(self.ClientID)) > 2:
                url = "https://api.twitch.tv/helix/users?login=" + channel
                r = requests.get(url, headers=self.apiheader).json()
                if not r["data"]:
                    print(f"Could not get data for {channel}. User is probably banned.")
                    return None
                else:
                    channelid = r["data"][0]["id"]
                    return channelid
            else:
                print(f"Get Channel ID - No apiclientid in config.")
        except Exception as e:
            print(f"Error in apigetchannelid.")
            print(f"{e}")

    def apigetuserinfo(self, username):
        print(f"Checking token.")
        self.token = TOA.checktoken()
        self.apiheaderupdate()
        if len(self.ClientID) > 2:
            url = "https://api.twitch.tv/helix/users?login=" + username
            r = requests.get(url, headers=self.apiheader).json()
            return r
        else:
            print(f"Get User Info - apigetuser failed.")

    def apigetfollowerslist(self, username, user_id, ignorejoinlist = None):
        self.token = TOA.checktoken()
        self.apiheaderupdate()
        if len(str(self.ClientID)) > 2:
            followinglist = []
            url = 'https://api.twitch.tv/helix/channels/followed'
            params = {
                'user_id': self.botuserid,
                'first': '100'
            }
            r = requests.get(url, headers=self.apiheader, params=params).json()
            totalfollow = r['total']

            while len(followinglist) < totalfollow:
                print("Page of followers checked.")
                for x in range(len(r["data"])):
                    followinglist.append("#" + str.lower(r["data"][x]["broadcaster_login"]))
                if "cursor" in r["pagination"]:
                    cursorpage = r["pagination"]["cursor"]
                    nexturl = url + '?user_id=' + self.botuserid + "&after=" + cursorpage
                    time.sleep(1)
                    r = requests.get(nexturl, headers=self.apiheader).json()
            if ignorejoinlist == None:
                if cfg.FollowerAutoJoin and (time.time() - self.starttime < 5):
                    self.AJChannels = followinglist.copy()
                    print(f"Created Auto Join Channel List. Count: {len(self.AJChannels)}\r\n")
            return followinglist
        else:
            print(f"Get Followers List - No apiclientid in config.")

    def apibanuid(self, uid, channelid, reason):
        self.token = TOA.checktoken()
        self.apiheaderupdate()
        try:
            if len(uid) > 5:
                bandata = {"data": {"user_id": str(uid).strip(), "reason": str(reason)}}
                url = (
                    "https://api.twitch.tv/helix/moderation/bans?"
                    + "broadcaster_id=" + str(channelid)
                    + "&moderator_id=" + str(clientlogin['user_id'])
                )
                r = requests.post(url, headers=self.apiheaderpost, json=bandata)
                print("Status Code", r.status_code)
                print("JSON Response ", r.json())
            
            else:
                print(f"UID too short")
        except Exception as e:
            print(f"Error in apibanuid\n {e}")
            pass

    def apibantimeoutuid(self, uid, channelid, dur, reason):
        self.token = TOA.checktoken()
        self.apiheaderupdate()
        try:
            if len(uid) > 5:
                bandata = {"data": {"user_id": str(uid).strip(), "duration": str(dur), "reason": str(reason)}}
                url = (
                    "https://api.twitch.tv/helix/moderation/bans?"
                    + "broadcaster_id=" + str(channelid)
                    + "&moderator_id=" + str(clientlogin['user_id'])
                )
                r = requests.post(url, headers=self.apiheaderpost, json=bandata)
                print("Status Code", r.status_code)
                print("JSON Response ", r.json())
            
            else:
                print(f"UID too short")
        except Exception as e:
            print(f"Error in apibantimeoutuid\n {e}")
            pass

    def joinchannel(self, channel): # channel name must start with #
        lchannel = str.lower(channel)
        if lchannel not in self.JoinedChannelsList:
            print(f"Attempting to join: {lchannel}")
            self.connection.join(lchannel)
            self.JoinedChannelsList.append(lchannel)

    def joinchannellist(self, channel_list):
        for x in channel_list:
            self.joinchannel(x)
            time.sleep(1)
            # JOINs are rate-limited to 20 JOINs/commands per 10 seconds. Additional JOINs sent after this will cause an unsuccessful login.
    
    def sendmsg(self, channel, message):
        self.connection.privmsg(channel, message)
        self.chatlogmessage(channel, f"{self.timestamp()} - {self.username}: {message}")

    def botcommands(self, cmd):

        if cmd == "!enable":
            cfg.EnableBotCommands = 1
            print(f"Commands Enabled")

        if cfg.EnableBotCommands:  # Terminal commands
            try:
                if cmd in {"!commands", "!help"}:
                    print(
                        f"!addmod, !addtrig, !bot, !chanfilteron, !chanfilteroff, !chanid, !chantrig, !commands, !getuserinfo, !help, !modlist, !reloadconfig\r\n"
                    )

                elif "!bot" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) == 1:
                        print(f"Usage: !bot #channel\r\n")
                    else:
                        self.sendmsg(
                            splitcmd[1],
                            f"Beep Bop Boop Beep... I'm not a bot, I'm a real man!",
                        )

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

                elif cmd == "!modlist":
                    print(f"{self.dbModChannels}")

                elif cmd == "!reloadconfig":
                    importlib.reload(cfg)
                    self.checkconfig()

                elif "!getuserinfo" in cmd:
                    splitcmd = cmd.split(" ")
                    if len(splitcmd) == 1:
                        print (
                            f"Gets user info via API."
                        )
                        print(f"Usage: !getuserinfo mr_protocol\r\n")
                    else:
                        new = self.apigetuserinfo(splitcmd[1])
                        print(f"New API Info:\r\n{new}")
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
        self.checktriggers(cfg.ModTriggers)

    def chatlogmessage(self, currentchannel, message):
        if cfg.EnableLogChatMessages:
            if ("GLOBAL" in cfg.ChatLogChannels) or (currentchannel in cfg.ChatLogChannels) or (currentchannel in self.dbModChannels):
                self.checklogdir("Chat")
                logchan = re.sub(":", "_", currentchannel)
                f = open(
                    f"Logs/Chat/{logchan}_ChatLog.txt",
                    "a+",
                    encoding="utf-8-sig",
                )
                f.write(f"{message}\r\n")
                f.close()

    def debuglog(self, edata):
        self.checklogdir("Debug")
        
        # Uses inspect module to get the function that calls this function
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe,2)

        f = open(
            f"Logs/Debug/{calframe[1][3]}_Debug.txt",
            "a+",
            encoding="utf-8-sig",
        )
        f.write(f"{edata}\r\n\r\n")
        f.close()

    def threadautojoin(self):
        # joins channels you are following if enabled
        if cfg.FollowerAutoJoin:
            print(f"Joining all followed channels.\r\n")
            self.joinchannellist(self.apigetfollowerslist(self.username, self.botuserid))

        # joins specified channels
        if len(self.configchannels) > 0:
            print(f"Joining list of channels.")
            self.joinchannellist(self.configchannels)

    def chattextparsing(self, edata):
        self.chatheartbeattime = int(time.time()) # Update time for chat heartbeat
        e = edata
        themsg = e.arguments[0]
        currentchannel = e.target
        logchan = re.sub(":", "_", currentchannel)
        isamod = False
        isavip = False
        isasub = False
        isbroadcaster = False
        
        # Used for debugging.
        if cfg.debug_chattextparsing:
            self.debuglog(edata)

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
            if x["key"] == "user-id":
                chatuserid = x["value"]
            if x["key"] == "room-id":
                roomid = x["value"]
            if x["key"] == "badges":
                if "vip" in str(x["value"]):
                    isavip = True
                else:
                    isavip = False
                if "broadcaster" in str(x["value"]):
                    isbroadcaster = True
                else:
                    isbroadcaster = False

        if str.lower(chatuser) == str.lower(self.username) and isamod: # Add channel to bot's channel mod list
            if currentchannel not in self.dbModChannels:
                self.dbModChannels.append(currentchannel)
        
        if str.lower(chatuser) == str.lower(self.username) and not isamod: # Remove channel from bot's channel mod list
            if currentchannel in self.dbModChannels:
                self.dbModChannels.remove(currentchannel)

        chatheader = " - "
        if isbroadcaster:
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
            + themsg
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

        # Mod Triggers - uses the lcase themsg and splits words via spaces
        # Regular Mod Triggers
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
                                # Matches text to the message
                                if str.lower(cfg.ModTriggers[ChanAndGlobal][x][0]) in str.lower(themsg):
                                    # Defines if it's a /ban or /timeout
                                    mresponse = cfg.ModTriggers[ChanAndGlobal][x][1]
                                    self.checklogdir("ModTriggers")
                                    # Handle mod text response
                                    if cfg.ModTriggers[ChanAndGlobal][x][2]:
                                        # If there is a mod auto reponse y/n
                                        modresponse = cfg.ModTriggers[ChanAndGlobal][x][2]
                                        if cfg.ModTriggers[ChanAndGlobal][x][3]:
                                            # If desired to tag the user 1/0
                                            modresponse = f"{modresponse} {chatuser}"
                                        self.sendmsg(currentchannel, f"{modresponse}")
                                        print(f"{self.timestamp()} {currentchannel} - !MOD!-{self.username}: {modresponse}")
                                    try:
                                        splitresponse = mresponse.split(" ", 1)
                                        print(splitresponse[0])
                                        if 'timeout' in splitresponse[0]:
                                            self.apibantimeoutuid(str(chatuserid), str(roomid), str(splitresponse[1].split(" ",1)[0]), str(splitresponse[1].split(" ",1)[1]))
                                        if 'ban' in splitresponse[0]:
                                            self.apibanuid(str(chatuserid), str(roomid), str(splitresponse[1]))
                                        print(f"{self.timestamp()} {currentchannel} - !MOD!-{self.username}: {splitresponse[0]} {chatuser} {splitresponse[1]}")
                                        f = open(
                                            f"Logs/ModTriggers/{logchan}_ModTriggerLog.txt",
                                            "a+",
                                            encoding="utf-8-sig",
                                        )
                                        f.write(f"{self.timestamp()} TRIGGER EVENT: {chatheader}{chatuser}: {themsg}\r\n")
                                        f.write(f"{self.timestamp()} SENT: !MOD!-{self.username}: {splitresponse[0]} {chatuser} {splitresponse[1]}\r\n")
                                        f.close()
                                    except Exception as e:
                                        print(e)

    def on_welcome(self, c, e):
        # You must request specific capabilities before you can use them
        c.cap("REQ", ":twitch.tv/membership twitch.tv/tags twitch.tv/commands")
        # c.cap("REQ", ":twitch.tv/membership")
        # c.cap("REQ", ":twitch.tv/tags")
        # c.cap("REQ", ":twitch.tv/commands")

        # Used for debugging.
        if cfg.debug_on_welcome:
            self.debuglog(e)

        autojoin_thread = threading.Thread(target=self.threadautojoin)
        autojoin_thread.daemon = True
        autojoin_thread.start()

    def on_pubmsg(self, c, e):
        # Used for debugging.
        # print(e)
        currentchannel = e.target
        self.chattextparsing(e)

        # SQLite for username change tracker
        # Extract relevant data from the event e
        userID = None
        username = None
        for tag in e.tags:
            if tag['key'] == 'user-id':
                userID = tag['value']
            elif tag['key'] == 'display-name':
                username = tag['value']

        channel = e.target
        timestamp = next((tag['value'] for tag in e.tags if tag['key'] == 'tmi-sent-ts'), None)

        # Add user change data to the queue
        self.user_change_queue.put((userID, username, channel, timestamp))

    def on_userstate(self, c, e):
        # Used for debugging.
        if cfg.debug_on_userstate:
            self.debuglog(e)

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
        # Used for debugging.
        if cfg.debug_on_usernotice:
            self.debuglog(e)

        currentchannel = e.target
        logchan = re.sub(":", "_", currentchannel)
        for x in e.tags:
            if x["key"] == "msg-id":
                sysmsgid = x["value"]
            if x["key"] == "display-name":
                chatuser = x["value"]
            if x["key"] == "system-msg":
                sysmsg = x["value"]  # Removes \n because Twitch is stupid and puts a \n mid string. I think they finally fixed this.
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
                            self.sendmsg(currentchannel, tmpNewSubMsg)
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
                            self.sendmsg(currentchannel, tmpReSubMsg)
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
                            self.sendmsg(currentchannel, tmpGiftSubMsg)
                            self.sub_epoch = time.time()
                            if currentchannel not in self.dbModChannels:
                                time.sleep(1.5)

        if (
            sysmsgid == "raid"
            and cfg.AnnounceRaids
            and currentchannel in cfg.AnnounceRaidChannels
        ):
            self.sendmsg(currentchannel, f"{cfg.RaidMsg} {sysmsg} {cfg.RaidMsg}")


        # What happens when the self.username is gifted a sub
        if cfg.EnableThankYou:
            if sysmsgid == "subgift" and str.lower(subgiftrecipient) == str.lower(self.username):
                self.sendmsg(currentchannel, f"{cfg.GiftThanksMsg} {chatuser}")
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

        # Used for debugging.
        if cfg.debug_on_clearchat:
            self.debuglog(e)

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
                
                if user == self.username:
                    self.checklogdir("BOTBANNED")
                    f = open(
                        f"Logs/BOTBANNED/{logchan}_clearchat.txt",
                        "a+",
                        encoding="utf-8-sig",
                    )
                    f.write(f"{banmsg}\r\n")
                    f.close()

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

    def on_clearmsg(self, c, e):
        # Shows when mod deletes single msg
        # print(e)
        if cfg.debug_on_clearmsg:
            self.debuglog(e)

    def on_notice(self, c, e):
        #print(e)
        if cfg.debug_on_notice:
            self.debuglog(e)

    def on_globaluserstate(self, c, e):
        # Not sure if this is real or not
        # Used for debugging.
        if cfg.debug_on_globaluserstate:
            self.debuglog(e)

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
        
        # Used for debugging.
        if cfg.debug_on_roomstate:
            self.debuglog(e)
        pass

    def on_mode(self, c, e):
        # Shows +/- mod permissions
        
        # Used for debugging.
        if cfg.debug_on_mode:
            self.debuglog(e)

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
        currentchannel = e.target
        # User joins the channel
        
        # Used for debugging.
        if cfg.debug_on_join:
            self.debuglog(e)

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
        currentchannel = e.target
        # User parts or leaves channel
        
        # Used for debugging.
        if cfg.debug_on_part:
            self.debuglog(e)

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
        currentchannel = e.target
        # When a user types /me in the chat and sends a message.
        # type: action, source: mr_protocol!mr_protocol@mr_protocol.tmi.twitch.tv, target: #mr_protocol, arguments: ['testing 12345'], tags: [{'key': 'badges', 'value': 'broadcaster/1,premium/1'}, {'key': 'color', 'value': '#00FF7F'}, {'key': 'display-name', 'value': 'Mr_Protocol'}, {'key': 'emotes', 'value': None}, {'key': 'flags', 'value': None}, {'key': 'id', 'value': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'}, {'key': 'mod', 'value': '0'}, {'key': 'room-id', 'value': 'XXXXXXX'}, {'key': 'subscriber', 'value': '0'}, {'key': 'tmi-sent-ts', 'value': 'XXXXXXXXXXX'}, {'key': 'turbo', 'value': '0'}, {'key': 'user-id', 'value': 'XXXXXXXX'}, {'key': 'user-type', 'value': None}]
        
        # Used for debugging.
        if cfg.debug_on_action:
            self.debuglog(e)

        self.chattextparsing(e)

    def on_hosttarget(self, c, e):
        # Shows hosting info
        # type: hosttarget, source: tmi.twitch.tv, target: #CHANNEL, arguments: ['channelbeinghosted -'], tags: []

        # Used for debugging.
        if cfg.debug_on_hosttarget:
            self.debuglog(e)

        if cfg.ChanFilters and e.target not in cfg.ChanTermFilters:
            pass
        else:
            currentchannel = e.target
            targetchannel = e.arguments[0].split(" ")[0]
            print(
                f"HOSTTARGET-{self.timestamp()} {currentchannel} is hosting {targetchannel}."
            )

    def on_privmsg(self, c, e):        
        # Used for debugging.
        if cfg.debug_on_privmsg:
            self.debuglog(e)

        hostmsg = e.arguments
        print(f"{self.timestamp()} {hostmsg}")

    def on_privnotice(self, c, e):
        # Used for debugging.
        if cfg.debug_on_privnotice:
            self.debuglog(e)

    def on_pubnotice(self, c, e):
        # Shows hosting message
        # Shows other channel options: slow mode, emote mode, etc.

        # Used for debugging.
        if cfg.debug_on_pubnotice:
            self.debuglog(e)

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
                    self.sendmsg(LAJHChan, f"Hello, {currentchannel[1:]} sent me via hosting.")
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

        # Used for debugging.
        if cfg.debug_on_whisper:
            self.debuglog(e)

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
    TOA.checkjsonclientdata()
    if os.path.exists('JSON/token.json') == False:
        TOA.gettoken()
    token = TOA.checktoken()
    with open('JSON/clientdata.json','r') as getlogin:
            clientlogin = json.load(getlogin)
            getlogin.close()
    
    input_watcher = InputWatcher()
    input_watcher.start()
    botthread1 = threading.Thread(target=tbot,args=[str.lower(clientlogin['login']), token, cfg.Channels, input_watcher])
    botthread1.start()

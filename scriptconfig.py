#---------------------------------------------------------------------------
#---------------------------------- CONFIG ---------------------------------
#---------------------------------------------------------------------------

# Open JSON/clientdata.json in a text editor and add your Twitch App values for client_id and client_secret.

# Auto Join channels that are followed + extra user rooms (!!!- REQUIRES API CLIENT ID - !!!)
FollowerAutoJoin = 0

# Auto Join channels that are hosted - Worm like auto join. Enable pubnotice logging to log hosts.
# This will probably cause the script to be DoS'd by Twitch with all the data it sends back.
AutoJoinHosts = 0

# Streamer name/channels here
# Example: Channels = ['#mr_protocol']
# Example: Channels = ['#mr_protocol', '#shroud', '#drdisrespectlive']
Channels = []

# Enable ChanFilters. Shows only filtered channels to terminal output.
ChanFilters = 1

# Enable ChanFilters. Only show filtered channels to terminal output.
# ChanTermFilters = ['#mr_protocol', '#shroud']
ChanTermFilters = []

#---------------------------------------------------------------------------
#------------------------------- Announcements -----------------------------
#---------------------------------------------------------------------------

# Announce new subs in chat.
AnnounceNewSubs = 0

# Announce new subs channels and messages.
# AnnounceNewSubsChanMsg = {'#mr_protocol':[('New Sub Hype!', 1)]} 1 = tag user, 0 = don't tag user
AnnounceNewSubsChanMsg = {
    '#mr_protocol':[
        ('New Sub Hype!', 1)
    ],
    '#thisisjustaplaceholder':[
        ('!newsub', 1)
    ]
}

# Announce resubs
AnnounceResubs = 0

# Announce resubs channels and messages.
# AnnounceReSubsChanMsg = {'#mr_protocol':[('Re-Sub Hype!', 1)], '#shroud':[('Welcome Back with the resub!',1)]} 1 = tag user, 0 = don't tag user
AnnounceReSubsChanMsg = {
    '#mr_protocol':[
        ('Re-Sub Hype!', 1)
    ],
    '#thisisjustaplaceholderchannel':[
        ('Welcome Back with the resub!', 1)
    ]
}

# Announce gifted subs
AnnounceGiftSubs = 0

# Announce gift subs channels and messages.
# AnnounceGiftSubsChanMsg = {'#mr_protocol':[('New Sub Hype!',1)]} 1 = tag gifted user, 0 = don't tag
AnnounceGiftSubsChanMsg = {
    '#mr_protocol':[
        ('Gifted Sub Hype!', 1)
    ],
    '#thisisjustaplaceholderchannel':[
        ('!newsub', 0)
    ]
}

# Turn on/off thanking user that gifts you a sub
EnableThankYou = 0

# Thank you message if someone gifts you a sub
GiftThanksMsg = 'Thanks for the gifted sub!'

# Announce Raids
AnnounceRaids = 0

# Announce raid message puts this text around (beginning and end) the system message of who raided and how many
RaidMsg = 'twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid twitchRaid'

# Announce yourself when joining a hosted channel with AutoJoinHosts enabled.
AnnounceAutoJoinHosts = 0

# Announce raid message channels
# AnnounceRaidChannels = ['#mr_protocol']
AnnounceRaidChannels = []

# Announce User Join Alerts
# Very bursty, pretty much useless.
AnnounceUserJoins = 0

# Announce User Join List
# Add users to be alerted of joining channel.
# Use 'GLOBAL' to show all
AnnounceUserJoinList = ['GLOBAL']

# Announce User Part/Leave Alerts
AnnounceUserParts = 0

# Announce User Part/Leave List
# Add users to be alerted of leaving channel.
# Use 'GLOBAL' to show all
AnnounceUserPartList = ['GLOBAL']

# Show or hide user mode changes
AnnounceModeChanges = 0

#---------------------------------------------------------------------------
#------------------------------ Chat Triggers ------------------------------
#---------------------------------------------------------------------------

# Mod Triggers are automatically logged.

# Chat/Mod trigger safelist
# SafelistUsers = ['mr_protocol','anotheruser','user3']
SafelistUsers = ['mr_protocol']

# Don't Trigger on VIPs
DontTriggerVIP = 0

# Don't trigger on subscribers of channel
DontTriggerSubs = 0

# Mod Triggers - ('Trigger','mod action','Text response',1/0)
# If the mod action is /timeout you can leave blank for default timeout or specify a number of seconds
# If no text response is desired, put None without quotes
# The 1/0 means put either a 1 or 0 to tag the chat user in the txt response. 1=tag 0=no tag

# Usage: "/timeout <login> [duration in seconds] [reason]" - Temporarily prevent a user from chatting.
# Duration (optional, default=10 minutes) must be a positive integer in seconds; maximum duration is 2 weeks.
# Combinations like 1d2h are also allowed.

# Usage: "/ban <username> [reason]" - Permanently prevent a user from chatting. Reason is optional and will be shown to the target user and other moderators. Use "unban" to remove a ban.

#Enable Mod Triggers
EnableModTriggers = 0

# Example
# ModTriggers = {
#     '#mr_protocol':[
#         ('trigger word','/timeout 1 [Reason text]',None,1)
#     ]

ModTriggers = {
    '#mr_protocol':[
        ('thisisjustaplaceholder','/timeout 1 (Automated)',None,1)
    ],
    '#placeholder':[
        ('thisisjustaplaceholder','/timeout 1 (Automated)',None,1)
    ],
    '#placeholder2':[
        ('thisisjustaplaceholder','/timeout 1 (Automated)',None,1)
    ],
    # GLOBAL apply to all channels where username has mod.
    'GLOBAL':[
        ('█','/timeout 120 ASCII Art Char (Automated)',None,1) # most common ASCII Art Character
    ]
}

# Enable Bot Commands
# Turns on terminal commands !enable or !commands or !help
EnableBotCommands = 0

#---------------------------------------------------------------------------
#----------------------------------- Logs ----------------------------------
#---------------------------------------------------------------------------

# Chat Triggers and Mod Triggers are automatically logged.

# Log timestamp timezone. 1=Local, 0=UTC
LogTimeZone = 1

# Log chat username highlights (Global)
LogHighlights = 1

# Log all chat messages and join/leave messages
EnableLogChatMessages = 0

# Chat Log only these channels. Automatically logs channels with mod
# ChatLogChannels = ['#shroud', '#drdisrespectlive']
# ChatLogChannels = ['GLOBAL'] #Logs all joined channels
ChatLogChannels = []

# Log join/part(leave) information in chat logs
ChatLogJoinPart = 0

# Log ASCII Art
LogAscii = 1
# Containing chars
LogAsciiSet = set('▄▀█▒▐░⚫🔴⚪┈▔▃▏┳┊')

# Send system messages to log file.
LogSystemMessages = 0

# Log raw system message or simplified. 1=raw 0=simplified
RawSystemMsgs = 0

# Log System messages from these channels
# SysMsgLogChannels = ['#mr_protocol', '#shroud']
# SysMsgLogChannel = ['GLOBAL'] #Logs all joined channels
SysMsgLogChannels = ['GLOBAL']

# Log pubnotice messages
LogPubnotice = 0

# Log clearchat messages
LogClearchat = 0

# Log Auto Join Hosts
LogAutoJoinHosts = 0

# Log Auto Join Channels - Logs the channels joined in a list
LogAutoJoinHostChannels = 0

#---------------------------------------------------------------------------
#----------------------------------- Debug ---------------------------------
#---------------------------------------------------------------------------

# This area is used for debugging the data passed to functions in TwitchBot.py
# Probably never have to use this area. Do not touch.

debug_chattextparsing = 0
debug_on_welcome = 0
debug_on_pubmsg = 0
debug_on_userstate = 0
debug_on_usernotice = 0
debug_on_clearchat = 0
debug_on_clearmsg = 0
debug_on_globaluserstate = 0
debug_on_roomstate = 0
debug_on_mode = 0
debug_on_join = 0
debug_on_part = 0
debug_on_action = 0
debug_on_hosttarget = 0
debug_on_privmsg = 0
debug_on_privnotice = 0
debug_on_pubnotice = 0
debug_on_whisper = 0
debug_on_notice = 0
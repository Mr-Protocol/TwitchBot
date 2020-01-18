#---------------------------------------------------------------------------
#---------------------------------- CONFIG ---------------------------------
#---------------------------------------------------------------------------
# Example: Username = 'mr_protocol'
Username = ''

# Enter OAUTH token here without the oauth: in the front. It will be added later in the script.
# To get an OAUTH token: https://twitchapps.com/tmi/ and link to your account.
# Example: Token = 'abc123456defghijklmnop'
Token = ''

# API Client ID - Get this by making an app on https://dev.twitch.tv/console/apps
# APIClientID = 'abcdefghijklmnop12345678'   <--- Example
APIClientID = ''

# Auto Join channels that are followed + extra user rooms (!!!- REQUIRES API CLIENT ID - !!!)
FollowerAutoJoin = 0

# Auto Join channels that are hosted - Worm like auto join. Enable pubnotice logging to log hosts.
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

# Chat Triggers and Mod Triggers are automatically logged.

# Chat/Mod trigger safelist
# SafelistUsers = ['mr_protocol','anotheruser','user3']
SafelistUsers = ['mr_protocol']

# Don't Trigger on VIPs
DontTriggerVIP = 0

# Don't trigger on subscribers of channel
DontTriggerSubs = 0

# Add automated text to the end of triggers message.
AutomatedRespondEnabled = 0

# Automated text to append to normal triggers
AutomatedResponseMsg = '(Automated Response)'

# Enable Chat Triggers
EnableChatTriggers = 0

# Chat Triggers - ('Trigger','response', 1) 1 = tag user, 0 = don't tag user
ChatTriggers = {
    '#mr_protocol':[
        ('Hype!', 'MORE HYPE!', 0),
        ('sometriggerwordhere', 'FeelsBadMan', 0)
    ],
    '#thisisjustaplaceholder':[
        ('Hype!', 'MORE HYPE!', 0),
        ('sometriggerwordhere', 'FeelsBadMan', 0)
    ],
    '#thisisjustaplaceholder2':[
        ('Hype!', 'MORE HYPE!', 0),
        ('sometreiggerwordhere', 'FeelsBadMan', 0)
    ],
    # GLOBAL will try and do the commands in any channel.
    'GLOBAL':[
        ('Thisisjustaplaceholder','MORE HYPE!',1)
    ]
}

# Enable Copy Pasta
EnableCopyPasta = 0

# Copy Pasta mode will repeat a message based on a word/phrase trigger. Whatever the user said that contains the word/phrase will be repeated.
# Copy Pasta Triggers - ('Trigger')
CopyPastaTriggers = {
    '#mr_protocol':[
        ('prime')
    ],
    '#channelnamehere':[
        ('thisisjustaplaceholder')
    ],
    '#channelnamehere2':[
        ('thisisjustaplaceholder')
    ],
    '#channelnamehere3':[
        ('thisisjustaplaceholder'),
        ('thisisjustaplaceholder2')
    ]
}

# Mod Triggers - ('Trigger','mod action','Text response',1/0)
# If the mod action is /timeout you can leave blank for default timeout or specify a number of seconds
# If no text response is desired, put None without quotes
# The 1/0 means put either a 1 or 0 to tag the chat user in the txt response. 1=tag 0=no tag

# Usage: "/timeout <login> [duration][time unit] [reason]" - Temporarily prevent a user from chatting.
# Duration (optional, default=10 minutes) must be a positive integer; time unit (optional, default=s) must be one of s, m, h, d, w; maximum duration is 2 weeks.
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
        ('█','/timeout 2m ASCII Art Char (Automated)',None,1) # most common ASCII Art Character
    ]
}

# Keyword Repeater
# Useful for when you have to type a keyword to enter a giveaway.
# Use a Chat Trigger to setup a response if a message says "You Win"
EnableKeywordRepeater = 0

# Repeat/Send keyword after # of consecutive repeats.
KeywordRepeaterCount = 7

# Enable Bot Commands
# Turns on terminal commands !enable or !commands or !help
EnableBotCommands = 0

# Enable tracking of chatters in channel
# Keeps track of users chatting and how many messages
EnableChatTracking = 0

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

# Chat Log only these channels
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
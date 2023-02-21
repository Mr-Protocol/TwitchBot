'''
Twitch2Database.py takes the IRC return for chat messages from twitch and stores that information in a SQLite Database. 

Written to be used with Mr. Protocol's TwitchBot.py (but in theory could be used with any IRC twitch script)

Author: Justin Tolman, auptyk.x1@gmail.com

'''

import sqlite3
import json

class filter_message_block:

    def __new__(self, raw_block):

      
        #specifies the information to be extracted from the raw_block. Dictionary keys will be variable names in the resulting list output
        important_info = {'message_time': 'tmi-sent-ts', 'user_id':'user-id', 'user_name':'display-name', 'room_id':'room-id', 'is_subscriber':'subscriber','is_mod': 'mod', 'first_message':'first-msg', 'message_guid':'id', 'reply_msg_id': 'reply-parent-msg-id'}
        
        filtered_blocks = {}
        
        #Grab message text and channel name from raw_block
        message_text = raw_block['arguments'][0]
        channel_name = raw_block['target'][1:]
        
        #the tags section of the output is (close to) a json format. The next two lines convert and handle that
        json_tags = json.dumps(raw_block['tags'])
        loaded_tags = json.loads(json_tags)
        
        is_reply = False

        #Iterate through the load_tags json information and look for indications of a reply. 
        if next((d for d in loaded_tags if d['key'] == 'reply-parent-msg-id'), None):
            is_reply = True
        
        for item in loaded_tags: 
            
            #Compare tags to important data and if there is a match move on
            if item['key'] in important_info.values():
                
                #We need to name the result to something meaningful, this generator will get our key name from important info when matched
                name = list(i for i in important_info if important_info[i] == item['key'])[0]

                #create a variable with the name of the matching key from important info, fill it with the value from the raw_block tags
                globals()[name] = item['value']
                
        
        #Create a dictionary based on whether or not it is a reply.
        if is_reply == True:
            filtered_blocks = {'message_text':message_text, 'message_time':message_time, 'user_id':user_id, 'user_name':user_name, 'room_id':room_id, 'channel_name':channel_name, 'is_subscriber':is_subscriber, 'is_mod':is_mod, 'first_message':first_message, 'message_guid':message_guid, 'reply_msg_id':reply_msg_id}
        else:
            filtered_blocks = {'message_text':message_text, 'message_time':message_time, 'user_id':user_id, 'user_name':user_name, 'room_id':room_id, 'channel_name':channel_name, 'is_subscriber':is_subscriber, 'is_mod':is_mod, 'first_message':first_message, 'message_guid':message_guid, 'reply_msg_id':'NULL'}

        return filtered_blocks

class filter_ban_block:
    
    def __new__(self, raw_block):
        
        #specifies the information to be extracted from the raw_block. Dictionary keys will be variable names in the resulting list output
        important_info = {'ban_time': 'tmi-sent-ts', 'user_id':'target-user-id', 'room_id':'room-id', 'ban_duration':'ban-duration'}
        
        filtered_blocks = {}
        
        #Grab user name and channel name from raw_block
        user_name = raw_block['arguments'][0]
        channel_name = raw_block['target'][1:]
        
        #the tags section of the output is (close to) a json format. The next two lines convert and handle that
        json_tags = json.dumps(raw_block['tags'])
        loaded_tags = json.loads(json_tags)
        
        is_perma_ban = True

        #Iterate through the load_tags json information and look for indications of a reply. 
        if next((d for d in loaded_tags if d['key'] == 'ban-duration'), None):
            is_perma_ban = False
        

        for item in loaded_tags: 
            
            #Compare tags to important data and if there is a match move on
            if item['key'] in important_info.values():
                
                #We need to name the result to something meaningful, this generator will get our key name from important info when matched
                name = list(i for i in important_info if important_info[i] == item['key'])[0]
                
                #create a variable with the name of the matching key from important info, fill it with the value from the raw_block tags
                globals()[name] = item['value']
                
        
        #Create a dictionary

        if is_perma_ban:
            filtered_blocks = {'ban_time':ban_time, 'user_id': user_id, 'user_name': user_name, 'room_id':room_id, 'channel_name':channel_name, 'ban_duration':0}
        else:
            filtered_blocks = {'ban_time':ban_time, 'user_id': user_id, 'user_name': user_name, 'room_id':room_id, 'channel_name':channel_name, 'ban_duration':ban_duration}
        
        return filtered_blocks

class filter_delete_block:

    def __new__(self, raw_block):

        important_info = {'user_name': 'login', 'date_deleted': 'tmi-sent-ts', 'message_guid': 'target-msg-id'}

        filtered_blocks = {}

        deleted_message = raw_block['arguments'][0]
        channel_name = raw_block['target'][1:]

        json_tags = json.dumps(raw_block['tags'])
        loaded_tags = json.loads(json_tags)

        for item in loaded_tags:

            if item['key'] in important_info.values():

                name = list(i for i in important_info if important_info[i] == item['key'])[0]
                globals()[name] = item['value']

        filtered_blocks = {'user_name': user_name, 'date_deleted': date_deleted, 'deleted_message': deleted_message, 'channel_name': channel_name, 'message_guid': message_guid}

        return filtered_blocks


class create_database:
    
    def __new__(self, database_location):
        
        try: 
            #table create statements
            messsages_table = 'CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, timestamp INTEGER, message TEXT, user_name TEXT, user_id TEXT, channel INTEGER REFERENCES channels (id),is_subscriber BOOLEAN,is_mod BOOLEAN, is_first_message BOOLEAN, message_guid TEXT, reply_msg_id TEXT, connection_id INTEGER);'
            channel_table = 'CREATE TABLE channels (id INTEGER PRIMARY KEY UNIQUE,channel_id TEXT UNIQUE, channel_name TEXT);'
            user_table = 'CREATE TABLE users (id INTEGER PRIMARY KEY UNIQUE, user_id TEXT, user_name TEXT, first_seen INTEGER, UNIQUE(user_id, user_name));'
            ban_table = 'CREATE TABLE is_banned (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, user_name TEXT, channel INTEGER REFERENCES channels (id), date_banned INTEGER, ban_duration INTEGER);'
            deleted_msg_table ='CREATE TABLE deleted_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, message_guid STRING UNIQUE ON CONFLICT IGNORE, channel_id INT REFERENCES channels (id), user_name STRING, date_deleted INTEGER);'
            connection_stats_table = 'CREATE TABLE connection_stats (id INTEGER PRIMARY KEY AUTOINCREMENT, connection_started INTEGER, connection_ended INTEGER, message_cap_count INTEGER);'

            connection = sqlite3.connect(database_location)
            cursor = connection.cursor()
            
            connection.execute('PRAGMA journal_mode=WAL')
            
            #create the tables
            cursor.execute(messsages_table)
            cursor.execute(channel_table)
            cursor.execute(user_table)
            cursor.execute(ban_table)
            cursor.execute(deleted_msg_table)
            cursor.execute(connection_stats_table)
            connection.commit()
            
            connection.close()
        
            return True
        
        except:
            
            print('Database Creation Failed.')
            return False
    
class populate_messages:

    def __new__(self, database_location, filtered_blocks, connection_id=None):
        
        connect_succeeds = True
        
        #Hopefully we handle the connection to the database peacefully with a try/except
        try: 
            connection = sqlite3.connect(database_location) 
        except: 
            print('Connection to database failed.')
            connect_succeeds = False
        
        if connect_succeeds:
            
            try:
                cursor = connection.cursor()
                
                #Insert the values related to the channel first
                cursor.execute('INSERT OR IGNORE INTO channels (channel_id, channel_name) VALUES (?,?)', (filtered_blocks.get('room_id'), filtered_blocks.get('channel_name')))
                
                #To support the JOIN statement, we need to get the primary key of the associated channel. This will be inserted into the messages table. 
                cursor.execute(f'SELECT id FROM channels WHERE channel_id = {filtered_blocks.get("room_id")}')
                channel_fk_retrieved = cursor.fetchone()[0]
                
                #Insert the information into the messages table
                if connection_id == None:
                    cursor.execute('INSERT INTO messages (timestamp, message, user_name, user_id, channel, is_subscriber, is_mod, is_first_message, message_guid, reply_msg_id, connection_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (filtered_blocks.get('message_time'), filtered_blocks.get('message_text'), filtered_blocks.get('user_name'), filtered_blocks.get('user_id'), channel_fk_retrieved, filtered_blocks.get('is_subscriber'), filtered_blocks.get('is_mod'), filtered_blocks.get('first_message'), filtered_blocks.get('message_guid'), filtered_blocks.get('reply_msg_id'), 'NULL'))
                else:
                    cursor.execute('INSERT INTO messages (timestamp, message, user_name, user_id, channel, is_subscriber, is_mod, is_first_message, message_guid, reply_msg_id, connection_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (filtered_blocks.get('message_time'), filtered_blocks.get('message_text'), filtered_blocks.get('user_name'), filtered_blocks.get('user_id'), channel_fk_retrieved, filtered_blocks.get('is_subscriber'), filtered_blocks.get('is_mod'), filtered_blocks.get('first_message'), filtered_blocks.get('message_guid'), filtered_blocks.get('reply_msg_id'), connection_id))
                #Insert User Information in the the user table to 'track' username changes
                cursor.execute('INSERT OR IGNORE INTO users (user_id, user_name, first_seen) VALUES (?,?,?)', (filtered_blocks.get('user_id'), filtered_blocks.get('user_name'), filtered_blocks.get('message_time')))
                
                connection.commit()
                
                connection.close()
                
                #print('Message Saved.')             
            
            except:
                print('Writing message to database failed. Ensure that the proper dictionary was passed to class.')

class populate_ban: 
    
    def __new__(self, database_location, filtered_blocks):
        
        connect_succeeds = True
        
        #Hopefully we handle the connection to the database peacefully with a try/except
        try: 
            connection = sqlite3.connect(database_location) 
        except: 
            print('Connection to database failed.')
            connect_succeeds = False
        
        if connect_succeeds:
            
            #try:
            cursor = connection.cursor()
            
            #get the inserted channel ID for the FK assignment
            cursor.execute(f'SELECT id FROM channels WHERE channel_id = {filtered_blocks.get("room_id")}')
            
            try:
                channel_fk_retrieved = cursor.fetchone()[0]
                
                cursor.execute('INSERT INTO is_banned (user_id, user_name, channel, date_banned, ban_duration) VALUES (?,?,?,?,?)', (filtered_blocks.get('user_id'), filtered_blocks.get('user_name'), channel_fk_retrieved, filtered_blocks.get('ban_time'), filtered_blocks.get('ban_duration')))                
            
                connection.commit()
                
                connection.close()
            except:
                
                #if the channel doesn't already exist in the channel table, insert the channel there first
                cursor.execute('INSERT OR IGNORE INTO channels (channel_id, channel_name) VALUES (?,?)', (filtered_blocks.get('room_id'), filtered_blocks.get('channel_name')))                
                
                cursor.execute(f'SELECT id FROM channels WHERE channel_id = {filtered_blocks.get("room_id")}')
                channel_fk_retrieved = cursor.fetchone()[0]
                
                cursor.execute('INSERT INTO is_banned (user_id, user_name, channel, date_banned, ban_duration) VALUES (?,?,?,?,?)', (filtered_blocks.get('user_id'), filtered_blocks.get('user_name'), channel_fk_retrieved, filtered_blocks.get('ban_time'), filtered_blocks.get('ban_duration')))
        
                connection.commit()
                
                connection.close()

class populate_deleted_msg:

    def __new__(self, database_location, filtered_blocks):

        connect_succeeds = True

        try:
            connection = sqlite3.connect(database_location)
        except:
            print('Connection to database failed.')
            connect_succeeds = False
        
        if connect_succeeds:

            cursor = connection.cursor()

            cursor.execute(f'SELECT id from channels WHERE channel_name = \"{filtered_blocks.get("channel_name")}\"')

            channel_fk_retrieved = cursor.fetchone()[0]

            cursor.execute('INSERT OR IGNORE INTO deleted_messages (message_guid, channel_id, user_name, date_deleted) VALUES (?,?,?,?)', (filtered_blocks.get('message_guid'), channel_fk_retrieved,  filtered_blocks.get('user_name'), filtered_blocks.get('date_deleted')))

            connection.commit()

            connection.close()
            
class populate_connection_stats:

    #This class requires two timestamps (start time and end time of capture), and the count of messages captured during the session.
    #If you don't want to use this table simply do not call the class. The database will work without it. 

    def __new__(self, database_location, connection_info):
        
        connect_succeeds = True

        try:
            connection = sqlite3.connect(database_location)
        except:
            print('Connection to database failed.')
            connect_succeeds = False
        
        if connect_succeeds:

            cursor = connection.cursor()

            cursor.execute(f'INSERT INTO connection_stats (connection_started, connection_ended, message_cap_count) VALUES (?,?,?)', (connection_info.get("start_date"), connection_info.get("end_date"), connection_info.get("count")))

            connection.commit()

            connection.close()

class get_current_connection:

        def __new__(self, database_location):
        
            connect_succeeds = True

            try:
                connection = sqlite3.connect(database_location)
            except:
                print('Connection to database failed.')
                connect_succeeds = False
            
            if connect_succeeds:

                cursor = connection.cursor()

                cursor.execute('SELECT MAX(connection_stats.id) + 1 FROM connection_stats')

                current_connection = cursor.fetchone()[0]

                connection.close()

                #This handles first time capture on a new database. 
                if current_connection is None:
                    current_connection = 1

                return current_connection
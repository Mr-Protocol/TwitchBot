import json
import requests
import time
import urllib.parse

def checkjsonclientdata():
    try:
        with open('JSON/clientdata.json','r') as clientf:
            clientdata = json.load(clientf)
            clientf.close()
    except Exception as e:
        print(e)
        print(f'Error loading file clientdata.json')
    if clientdata['client_id'] == "":
        print(f'Use a text editor and input client_id in clientdata.json.')
        exit()
    if clientdata['client_secret'] == "":
        print(f'Use a text editor and input client_secret in clientdata.json.')
        exit()

# Check token, update clientdata with unixepxire time, update token, return token
def checktoken():
    try:
        with open('JSON/token.json','r') as tokenf:
            tokendata = json.load(tokenf)
            tokenf.close()
        with open('JSON/clientdata.json','r') as clientf:
            clientdata = json.load(clientf)
            clientf.close()
    except Exception as e:
        print(e)
        print(f'no token.json file.')

    url = "https://id.twitch.tv/oauth2/validate"
    headers={"Authorization": "OAuth " + tokendata['access_token']}
    r = requests.get(url, headers=headers).json()

    if 'status' in r:
        print(f'Invalid Token - delete JSON/token.json and re-link with Twitch account.')
        exit()
    if 'expires_in' in r:
        clientdata['unixexpire'] = int(time.time()) + int(r['expires_in'])
        clientdata['login'] = r['login']
        clientdata['user_id'] = r['user_id']
        try:
            with open ('JSON/clientdata.json','w', encoding='utf-8') as f:
                json.dump(clientdata, f, ensure_ascii=False, indent=4)
                f.close()
        except Exception as e:
            print(e)
    if clientdata['unixexpire'] < int(time.time()):
        print("Refreshing token...")
        return refreshtoken()
    else:
        return tokendata['access_token']


# Link app and Twitch account, gets initial token and permissions
def gettoken():
    try:
        with open('JSON/clientdata.json','r') as d:
            clientdata = json.load(d)
            d.close()
    except Exception as e:
            print(e)

    authorization_url = 'https://id.twitch.tv/oauth2/authorize?client_id=' + clientdata['client_id'] + '&redirect_uri=' + clientdata['redirect_uri'] + '&response_type=code&scope=' + urllib.parse.quote_plus(clientdata['scope'])

    print ('\r\nPlease go to:\r\n%s\r\nAccept authorize access.\r\n' % authorization_url)
    authorization_response = input('Enter the full callback URL redirect to localhost and press Enter:\r\n')

    stepone=str(authorization_response).split('code=')
    steptwo=stepone[1].split('&scope')
    code = steptwo[0]

    url = r'https://id.twitch.tv/oauth2/token?client_id=' + clientdata['client_id'] + r'&client_secret=' + clientdata['client_secret'] + r'&code=' + code + r'&grant_type=authorization_code&redirect_uri=http://localhost'
    r = requests.post(url = url).json()

    with open('JSON/token.json', 'w', encoding='utf-8') as f:
        json.dump(r, f, ensure_ascii=False, indent=4)
        f.close()

# Refresh token
def refreshtoken():
    try:
        with open('JSON/token.json','r') as t:
            tokendata = json.load(t)
            t.close()
        with open('JSON/clientdata.json','r') as d:
            clientdata = json.load(d)
            d.close()
    except Exception as e:
        print(f'Error in refreshtoken()\r\n{e}')

    url = 'https://id.twitch.tv/oauth2/token?grant_type=refresh_token&refresh_token=' + urllib.parse.quote(tokendata['refresh_token'], safe='') + '&client_id=' + clientdata['client_id'] + '&client_secret=' + clientdata['client_secret']

    r = requests.post(url = url)
    data = r.json()
    if 'error' in data:
        print(f"ERROR REFRESHING TOKEN, RESPONSE HAD ERROR.\r\n{data}")
    try:
        tokendata['access_token'] = data['access_token']
        tokendata['refresh_token'] = data['refresh_token']
        with open('JSON/token.json','w', encoding='utf-8') as f:
            json.dump(tokendata, f, ensure_ascii=False, indent=4)
            f.close()
    except Exception as e:
        print(e)

    with open('JSON/token.json','r') as t:
        tokenreturn = json.load(t)
        t.close()
    return tokenreturn['access_token']


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def _get_salt():
    import re, requests
    result = requests.get('https://www.boerse-frankfurt.de/main-es2015.ac96265ebda80215a714.js')
    salt = re.findall('(?<=salt:")\w*', result.text)
    return salt[0]

def _create_header(url):
    ids = _create_ids(url=url)
    headers = {'authority': 'api.boerse-frankfurt.de', 
               'origin': 'https://www.boerse-frankfurt.de',
               'referer': 'https://www.boerse-frankfurt.de/',
               'client-date': '' + ids['timestr'],
               'x-client-traceid': '' + ids['traceid'],
               'x-security': '' + ids['xsecurity']}
            
    return headers

def _create_ids(url):
    from datetime import datetime
    import hashlib
    
    salt="w4ivc1ATTGta6njAZzMbkL3kJwxMfEAKDa3MNr"
    
    timeutc=datetime.utcnow()
    timelocal=datetime.now()
    timestr = timeutc.isoformat(timespec='milliseconds') + 'Z'

    traceidbase = timestr + url + salt
    encoded = traceidbase.encode()
    traceid = hashlib.md5(encoded).hexdigest()

    xsecuritybase = timelocal.strftime("%Y%m%d%H%M") 
    encoded = xsecuritybase.encode()
    xsecurity = hashlib.md5(encoded).hexdigest()
    
    return {'timestr':timestr, 'traceid':traceid, 'xsecurity':xsecurity}

# Functions for retrieving DATA

def _get_data_url(function: str, params:dict):
    import urllib
    baseurl = "https://api.boerse-frankfurt.de/v1/data/"
    p_string = urllib.parse.urlencode(params)
    return baseurl + function + '?' + p_string

def _data_request(function: str, params: dict):
    import requests, json
    
    url = _get_data_url(function, params)
    header = _create_header(url)
    header['accept'] = 'application/json, text/plain, */*'
    req = requests.get(url, headers=header, timeout=(3.5, 15))
    data = json.loads(req.text)
    
    return data

# Functions for retrieving SEARCH requests

def _get_search_url(function: str, params:dict):
    import urllib
    baseurl = "https://api.boerse-frankfurt.de/v1/search/"
    p_string = urllib.parse.urlencode(params)
    return baseurl + function + ('?' + p_string if p_string != '' else '')

def _search_request(function: str, params: dict):
    import requests, json
    
    url = _get_search_url(function, {})
    header = _create_header(url)
    header['accept'] = 'application/json, text/plain, */*'
    header['content-type'] = 'application/json; charset=UTF-8'
    req = requests.post(url, headers=header, timeout=(3.5, 15), json=params)
    data = json.loads(req.text)
    
    return data

# Functions for STREAM requests

def _stream_request(function: str, params: dict):
    import sseclient, requests
    
    url = _get_data_url(function, params)
    header = _create_header(url)
    header['accept'] = 'text/event-stream'
    header['cache-control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    
    socket = requests.get(url, stream=True, headers=header, timeout=(3.5, 5))
    client = sseclient.SSEClient(socket)
    
    return client

def _read_chunked(request:callable, function:str, args:dict, CHUNK_SIZE:int=1000, 
                  identifiers:dict={'data':'data', 'numberElements':'totalCount'}):
    
    if 'limit' in args:
        limit = args['limit']
    else:
        limit = 0
    if 'offset' in args:
        offset = args['offset']
    else:
        offset = 0
    
    if limit > 0:
        maxCount = limit + offset
    else:
        maxCount = offset + CHUNK_SIZE + 1 #Initialwert, wird überschrieben
    
    result_list = []
    position = offset
    #i = 0
    
    while position < maxCount:
        print('read from position', position, 'size', CHUNK_SIZE)
        args['offset'] = position
        args['limit'] = min(CHUNK_SIZE, maxCount - position)
        
        data = request(function, args)
        
        if limit == 0:
            maxCount = data[identifiers['numberElements']]
        
        result_list += data[identifiers['data']]
        
        #i += 1
        position += CHUNK_SIZE

    return result_list, data[identifiers['numberElements']]

def _get_name(name_dict):
    name = name_dict['originalValue']
    if 'translations' in name_dict:
        if 'de' in name_dict['translations']:
            name = name_dict['translations']['de']
        if 'others' in name_dict['translations']:
            name = name_dict['translations']['others']
    
    return name
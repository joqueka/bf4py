#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class BF4PyConnector():
    def __init__(self, salt: str=None):
        import requests, re
        
        self.session = requests.Session()
        
        self.session.headers.update({'authority': 'api.boerse-frankfurt.de', 
                                     'origin': 'https://www.boerse-frankfurt.de',
                                     'referer': 'https://www.boerse-frankfurt.de/',})
        
        if salt is None:
            # Step 1: Get Homepage and extract main-es2015 Javascript file
            response = self.session.get('https://www.boerse-frankfurt.de/')
            if response.status_code != 200:
                raise Exception('Could not connect to boerse-frankfurt.de')
            file = re.findall('(?<=src=")main\.\w*\.js', response.text)
            if len(file) != 1:
                raise Exception('Could not find ECMA Script name')
            
            # Step 2: Get Javascript file and extract salt
            response = self.session.get('https://www.boerse-frankfurt.de/'+file[0])
            if response.status_code != 200:
                raise Exception('Could not connect to boerse-frankfurt.de')
            salt_list = re.findall('(?<=salt:")\w*', response.text)
            if len(salt_list) != 1:
                raise Exception('Could not find tracing-salt')
            self.salt = salt_list[0]
        else:
            self.salt = salt
   
    def __del__(self):
        self.session.close()
   
    def _create_ids(self, url):
        import hashlib
        from datetime import datetime
        timeutc = datetime.utcnow()
        timelocal = datetime.now()
        timestr = timeutc.isoformat(timespec='milliseconds') + 'Z'

        traceidbase = timestr + url + self.salt
        encoded = traceidbase.encode()
        traceid = hashlib.md5(encoded).hexdigest()

        xsecuritybase = timelocal.strftime("%Y%m%d%H%M") 
        encoded = xsecuritybase.encode()
        xsecurity = hashlib.md5(encoded).hexdigest()
        
        return {'client-date':timestr, 'x-client-traceid':traceid, 'x-security':xsecurity}
    
    
    
    def _get_data_url(self, function: str, params:dict):
        import urllib
        baseurl = "https://api.boerse-frankfurt.de/v1/data/"
        p_string = urllib.parse.urlencode(params)
        return baseurl + function + '?' + p_string

    
    def data_request(self, function: str, params: dict):
        import json
        
        url = self._get_data_url(function, params)
        header = self._create_ids(url)
        header['accept'] = 'application/json, text/plain, */*'
        req = self.session.get(url, headers=header, timeout=(3.5, 15))
        
        if req.text is None:
            raise Exception('Boerse Frankfurt returned no data, check parameters, especially period!')
        
        data = json.loads(req.text)
        
        if 'messages' in data:
            raise Exception('Boerse Frankfurt did not process request:', *data['messages'])
        
        return data
    
    def _get_search_url(self, function: str, params:dict):
        import urllib
        baseurl = "https://api.boerse-frankfurt.de/v1/search/"
        p_string = urllib.parse.urlencode(params)
        return baseurl + function + ('?' + p_string if p_string != '' else '')

    def search_request(self, function: str, params: dict):
        import json
        
        url = self._get_search_url(function, {})
        header = self._create_ids(url)
        header['accept'] = 'application/json, text/plain, */*'
        header['content-type'] = 'application/json; charset=UTF-8'
        req = self.session.post(url, headers=header, timeout=(3.5, 15), json=params)
        data = json.loads(req.text)
        
        return data

    # Functions for STREAM requests

    def stream_request(self, function: str, params: dict):
        import sseclient, requests
        
        url = self._get_data_url(function, params)
        header = self._create_ids(url)
        header['accept'] = 'text/event-stream'
        header['cache-control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        
        socket = requests.get(url, stream=True, headers=header, timeout=(3.5, 5))
        client = sseclient.SSEClient(socket)
        
        return client
    

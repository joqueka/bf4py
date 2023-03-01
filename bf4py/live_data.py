#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading, json

from .connector import BF4PyConnector

class LiveData():
    def __init__(self, connector: BF4PyConnector = None, default_isin: str = None):
        self.default_isin = default_isin
        self.streaming_clients = []
        
        if connector is None:
            self.connector = BF4PyConnector()
        else:
            self.connector = connector
        
    
    def __del__(self):
        for client in self.streaming_clients:
            client.close()

    def price_information(self, isin:str=None, callback:callable=print, mic:str='XETR', cache_data=False):
        """
        This function streams latest available price information of one instrument.
    
        Parameters
        ----------
        isin : str
            Desired isin.
        callback : callable, optional
            Callback function to evaluate received data. It will get one argument containing JSON data. The default is print.
        mic : str, optional
            Provide appropriate exchange if symbol is not in XETRA. The default is 'XETR'.
    
        Returns
        -------
        client : BFStreamClient
            return parameterized BFStreamClient. Use BFStreamClient.open_stream() to start receiving data.
    
        """
        return self._generate_client('price_information', isin, callback, mic, cache_data)

    
    def bid_ask_overview(self, isin:str=None, callback:callable=print, mic:str='XETR', cache_data=False):
        """
        This function streams top ten bid and ask quotes for given instrument.
    
        Parameters
        ----------
        isin : str
            Desired isin.
        callback : callable, optional
            Callback function to evaluate received data. It will get one argument containing JSON data. The default is print.
        mic : str, optional
            Provide appropriate exchange if symbol is not in XETRA. The default is 'XETR'.
    
        Returns
        -------
        client : BFStreamClient
            return parameterized BFStreamClient. Use BFStreamClient.open_stream() to start receiving data.
    
        """
        return self._generate_client('bid_ask_overview', isin, callback, mic, cache_data)

    
    def live_quotes(self, isin:str=None, callback:callable=print, mic:str='XETR', cache_data=False):
        """
        This function streams latest price quotes from bid and ask side.
    
        Parameters
        ----------
        isin : str
            Desired isin.
        callback : callable, optional
            Callback function to evaluate received data. It will get one argument containing JSON data. The default is print.
        mic : str, optional
            Provide appropriate exchange if symbol is not in XETRA. The default is 'XETR'.
    
        Returns
        -------
        client : BFStreamClient
            return parameterized BFStreamClient. Use BFStreamClient.open_stream() to start receiving data.
    
        """
        return self._generate_client('quote_box', isin, callback, mic, cache_data)

    
    
    def _generate_client(self, function, isin, callback, mic, cache_data):
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
        
        params = {'isin': isin,
                  'mic': mic}
        
        client = BFStreamClient(function, params, callback=callback, connector=self.connector, cache_data=cache_data)
        self.streaming_clients.append(client)
        return client


class BFStreamClient():
    def __init__(self, function: str, params: dict, callback:callable=None, connector: BF4PyConnector = None, cache_data=False):
        self.active = False
        self.stop = False
        self.endpoint = function
        self.params = params
        self.callback = callback
        self.receiver_thread = None
        self.cache_data = cache_data
        self.data = []
        
        if connector is None:
            self.connector = BF4PyConnector()
        else:
            self.connector = connector
    
    def __del__(self):
        self.close()
    
    def open_stream(self):
        if not self.active and self.receiver_thread is None:
            self.data = []
            self.stop = False
            thread = threading.Thread(target = self.receive_data, name='bf4py.BFStreamClient_'+self.endpoint+'_'+self.params['isin'])
            thread.daemon = True
            thread.start()
            self.receiver_thread = thread
            self.active = True
    
    def receive_data(self):
        self.client = self.connector.stream_request(self.endpoint, self.params)
        try:
            for event in self.client.events():
                if self.stop:
                    break
                if event.event == 'message':
                    try:
                        data = json.loads(event.data)
                        if self.cache_data:
                            self.data.append(data)
                        else:
                            self.data = [data]
                        
                        if self.callback is not None:
                            self.callback(data)
                    except:
                        continue
        except:
            print('bf4py Stream Client unintentionally stopped for', self.params['isin'])
        #self.client.close()
        self.active = False
        
    def close(self):
        if self.receiver_thread is not None: 
            self.stop = True
            self.receiver_thread.join()
            self.receiver_thread = None
            self.active = False

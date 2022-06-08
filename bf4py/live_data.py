#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ._utils import _stream_request
import threading, json


def price_information(isin:str, callback:callable=print, mic:str='XETR'):
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
    params = {'isin': isin,
              'mic': mic}
    
    client = BFStreamClient('price_information', params, callback=callback)
    return client

def bid_ask_overview(isin:str, callback:callable=print, mic:str='XETR'):
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
    params = {'isin': isin,
              'mic': mic}
    
    client = BFStreamClient('bid_ask_overview', params, callback=callback)
    return client

def live_quotes(isin:str, callback:callable=print, mic:str='XETR'):
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
    params = {'isin': isin,
              'mic': mic}
    
    client = BFStreamClient('quote_box', params, callback=callback)
    return client
    

class BFStreamClient():
    def __init__(self, function: str, params: dict, callback:callable=None):
        self.active = False
        self.stop = False
        self.endpoint = function
        self.params = params
        self.callback = callback
                    
    def open_stream(self):
        self.data = []
        thread = threading.Thread(target = self.receive_data, name='bf4py.BFStreamClient_'+self.endpoint+'_'+self.params['isin'])
        thread.daemon = True
        thread.start()
        self.receiver_thread = thread
        self.active = True
    
    def receive_data(self):
        self.client = _stream_request(self.endpoint, self.params)
        try:
            for event in self.client.events():
                if self.stop:
                    break
                if event.event == 'message':
                    try:
                        data = json.loads(event.data)
                        self.data.append(data)
                        if self.callback is not None:
                            self.callback(data)
                    except:
                        continue
        except:
            print('bf4py Stream Client stopped for', self.params['isin'])
        self.client.close()
        self.active = False
        
    def close(self):
        self.stop = True
        self.receiver_thread.join()
        self.receiver_thread = None

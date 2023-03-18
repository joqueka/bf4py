#!/usr/bin/env python3
# -*- coding: utf-8 -*-



from datetime import datetime, timezone
from .connector import BF4PyConnector

class Equities():
    def __init__(self, connector: BF4PyConnector = None, default_isin = None):
        self.default_isin = default_isin
        
        if connector is None:
            self.connector = BF4PyConnector()
        else:
            self.connector = connector
    
    def equity_details(self, isin:str = None):
        """
        Get basic data about specific equity (by ISIN).
    
        Parameters
        ----------
        isin : str
            Desired ISIN.
    
        Returns
        -------
        data : TYPE
            Dict with data.
    
        """
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
            
        params = {'isin': isin}
        
        data = self.connector.data_request('equity_master_data', params)
        
        return data
    
    
    def key_data(self, isin:str = None):
        """
        Get key/technical data about specific equity (by ISIN).
    
        Parameters
        ----------
        isin : str
            Desired ISIN.
    
        Returns
        -------
        data : TYPE
            Dict with data.
    
        """
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
            
        params = {'isin': isin}
        
        data = self.connector.data_request('equity_key_data', params)
        
        return data
    
    
    
    def bid_ask_history(self, start: datetime, end: datetime=datetime.now(), isin:str = None):
        """
        Get best bid/ask price history of specific equity (by ISIN). This usually works for about the last two weeks.
    
        Parameters
        ----------
        isin : str
            Desired ISIN.
        start : datetime
            Startng date. Should not be more than two weeks ago
        end : datetime
            End date.
    
        Returns
        -------
        ba_history : TYPE
            List of dicts with bid/ask data.
    
        """
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
            
        #Initializing
        ba_history = []
        i = 0
        CHUNK_SIZE = 1000
        maxCount = CHUNK_SIZE + 1
        
        params = {'limit': CHUNK_SIZE,
                  'offset': 0,
                  'isin': isin,
                  'mic': 'XETR',
                  'from': start.astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
                  'to': end.astimezone(timezone.utc).isoformat().replace('+00:00','Z')}
        
        while i * CHUNK_SIZE < maxCount:
            params['offset'] = i * CHUNK_SIZE
            
            data = self.connector.data_request('bid_ask_history', params)
            
            maxCount = data['totalCount']
            ba_history += data['data']
            
            i += 1
            
        return ba_history
    
    def times_sales(self, start: datetime, end: datetime=None, isin: str = None):
        """
        Get time/sales history of specific equity (by ISIN) from XETRA. This usually works for about the last two weeks.
    
        Parameters
        ----------
        isin : str
            Desired ISIN.
        start : datetime
            Startng date. Should not be more than two weeks ago
        end : datetime
            End date.
    
        Returns
        -------
        ts_list : TYPE
            List of dicts with time/sales data.
    
        """
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
        
        if end is None:
            end = datetime.now()
        
        ts_list = []
        i = 0
        CHUNK_SIZE = 10000
        maxCount = CHUNK_SIZE + 1
        
        params = {'isin': isin,
                  'limit': CHUNK_SIZE,
                  'offset': 0,
                  'mic': 'XETR',
                  'minDateTime': start.astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
                  'maxDateTime': end.astimezone(timezone.utc).isoformat().replace('+00:00','Z')}
        
        while i * CHUNK_SIZE < maxCount:
            params['offset'] = i * CHUNK_SIZE
            
            data = self.connector.data_request('tick_data', params)
            
            maxCount = data['totalCount']
            ts_list += data['ticks']
            
            i += 1
        return ts_list
    
    def related_indices(self, isin:str = None):
        """
        Get list of indices in which equity is listed.
    
        Parameters
        ----------
        isin : str
            Desired ISIN.
    
        Returns
        -------
        data : TYPE
            List of dicts with basic information about related indices.
    
        """
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
            
        params = {'isin': isin}
        
        data = self.connector.data_request('related_indices', params)
        
        return data
        
    # def equity_search(limit: int = 25, search_params:dict = None):
        
    #     params = {'limit': limit}
    #     if search_params:
    #         params.update(search_params)
        
    #     #data = _read_chunked(_search_request, 'equity_search', params)
    #     data = _search_request('equity_search', params)
        
    #     return data
    

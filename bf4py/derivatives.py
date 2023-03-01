#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from datetime import date, datetime, timezone, time

from .connector import BF4PyConnector

class Derivatives():
    def __init__(self, connector: BF4PyConnector = None, default_isin = None, default_mic = 'XETR'):
        self.default_isin = default_isin
        self.default_mic = default_mic
        
        if connector is None:
            self.connector = BF4PyConnector()
        else:
            self.connector = connector


    def trade_history(self, search_date:date):
        """
        Returns the times/sales list of every traded derivative for given day. 
        Works for a wide range of dates, however details on instruments get less the more you move to history.
    
        Parameters
        ----------
        search_date : date
            Date for which derivative trades should be received.
    
        Returns
        -------
        tradelist : TYPE
            A list of dicts with details about trade and instrument.
    
        """
        CHUNK_SIZE = 1000
        i = 0
        maxCount = CHUNK_SIZE + 1
        
        params = {'from': datetime.combine(search_date, time(8,0,0)).astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
                  'to': datetime.combine(search_date, time(22,0,0)).astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
                  'limit': CHUNK_SIZE,
                  'offset': 0,
                  'includePricesWithoutTurnover': False}
        
        tradelist = []
        
        while i * CHUNK_SIZE < maxCount:
            params['offset'] = i * CHUNK_SIZE
            
            data = self.connector.data_request('derivatives_trade_history', params)
            
            maxCount = data['totalElements']
            tradelist += data['data']
            
            i += 1
        
        return tradelist
    
    def instrument_data(self, isin:str = None, mic:str = None):
        """
        Returns all information about given derivative ISIN.
    
        Parameters
        ----------
        isin : str
            ISIN ov valid derivative.
    
        Returns
        -------
        data : TYPE
            Dict with information.
    
        """
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
        if mic is None:
            mic = self.default_mic
        assert mic is not None, 'No mic (Exchange) given'
            
        params = {'isin': isin,
                  'mic': mic}
        
        data = self.connector.data_request('derivatives_master_data', params)
        
        return data
    
    
    def search_criteria(self):
        """
        Returns all multi-option criteria lists for derivatives search (not implemented yet)
    
        Returns
        -------
        data : TYPE
            Dict.
    
        """
        params = {'lang': 'de',
                  'offset': 0,
                  'limit': 0,
                  'types': []}
        
        data = self.connector.search_request('derivative_search_criteria_data', params)
        
        return data
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import date

from .connector import BF4PyConnector

class General():
    def __init__(self, connector: BF4PyConnector = None, default_isin = None):
        self.default_isin = default_isin
        
        if connector is None:
            self.connector = BF4PyConnector()
        else:
            self.connector = connector
    
    def eod_data(self, min_date: date, max_date: date=date.today(), isin: str = None, mic:str='XETR'):
        """
        Function for retrieving OHLC data including volume by pieces and cash amount (Euro) for selected date range.
        
        Parameters
        ----------
        isin : str
            Desired ISIN.
        mic : str
            Exchange where instrument is listed (see instrument_information(isin) for available mic strings)
        min_date : date, optional
            Must be set to desired date, at least yesterday, because API returns no elements if min_date == max_date == today.
        max_date : date, optional
            The default is date.today().
    
        Returns
        -------
        TYPE
            Returns list of dicts with trading data. Elements are OHLC, date and turnover in Euro and Pieces.
    
        """
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
        
        date_delta = max_date - min_date
        params = {'isin' : isin,
                  'mic': mic,
                  'minDate': min_date.strftime("%Y-%m-%d"),
                  'maxDate': max_date.strftime("%Y-%m-%d"),
                  'limit': date_delta.days,
                  'cleanSplit': False,
                  'cleanPayout': False,
                  'cleanSubscription': False}
        
        data = self.connector.data_request('price_history', params)
        
        return data['data']
    
    def data_sheet_header(self, isin:str = None):
        """
        Function for retrieving basic information about an instrument.
    
        Parameters
        ----------
        isin : str
            Desired ISIN.
    
        Returns
        -------
        data : TYPE
            Returns dict with basic information about given ISIN.
    
        """
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
            
        params = {'isin': isin}
        
        data = self.connector.data_request('data_sheet_header', params)
        
        return data
    
    
    def instrument_information(self, isin:str = None):
        """
        Function for retrieving extended trading information about selected instrument.
    
        Parameters
        ----------
        isin : str
            Desired ISIN.
    
        Returns
        -------
        data : TYPE
            Returns dict with trading data about given ISIN.
    
        """
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
            
        params = {'isin': isin}
        
        data = self.connector.data_request('instrument_information', params)
        
        return data
    
    def index_instruments(self, isin: str = 'DE0008469008'):
        """
        Function for retrieving all instruments in given index isin.
    
        Parameters
        ----------
        isin : str, optional
            Desired Index ISIN. The default is 'DE0008469008' (DAX).
    
        Returns
        -------
        instrument_list : TYPE
            List of dicts for every instrument in index. Every dict has values name, isin, wkn
    
        """
        params = {'indices' : [isin],
                  'lang': 'de',
                  'offset': 0,
                  'limit': 1000,
                  'sorting': 'NAME',
                  'sortOrder': 'ASC'}
        
        data = self.connector.search_request('equity_search', params)
        
        #Reorganize data
        instrument_list = []
        for e in data['data']:
            i = {'name': self._get_name(e['name']),
                 'isin': e['isin'],
                 'wkn': e['wkn']
                }
            instrument_list.append(i)
        
        return instrument_list
    
    def _get_name(self, name_dict):
        name = name_dict['originalValue']
        if 'translations' in name_dict:
            if 'de' in name_dict['translations']:
                name = name_dict['translations']['de']
            if 'others' in name_dict['translations']:
                name = name_dict['translations']['others']
        
        return name

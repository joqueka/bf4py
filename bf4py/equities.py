#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ._utils import _data_request, _search_request
from datetime import datetime, timezone


def equity_details(isin:str):
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
    params = {'isin': isin}
    
    data = _data_request('equity_master_data', params)
    
    return data


def key_data(isin:str):
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
    params = {'isin': isin}
    
    data = _data_request('equity_key_data', params)
    
    return data



def bid_ask_history(isin:str, start: datetime, end: datetime):
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
        
        data = _data_request('bid_ask_history', params)
        
        maxCount = data['totalCount']
        ba_history += data['data']
        
        i += 1
        
    return ba_history

def times_sales(isin: str, start: datetime, end: datetime):
    """
    Get time/sales history of specific equity (by ISIN). This usually works for about the last two weeks.

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
    ts_list = []
    i = 0
    CHUNK_SIZE = 10000
    maxCount = CHUNK_SIZE + 1
    
    params = {'isin': isin,
              'limit': CHUNK_SIZE,
              'offset': 0,
              'mic': 'XETR',
              'from': start.isoformat() + 'Z',
              'to': end.isoformat() + 'Z'}
    
    while i * CHUNK_SIZE < maxCount:
        params['offset'] = i * CHUNK_SIZE
        
        data = _data_request('tick_data', params)
        
        maxCount = data['totalCount']
        ts_list += data['ticks']
        
        i += 1
        
    return ts_list

def related_indices(isin:str):
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
    params = {'isin': isin}
    
    data = _data_request('related_indices', params)
    
    return data
    
# def equity_search(limit: int = 25, search_params:dict = None):
    
#     params = {'limit': limit}
#     if search_params:
#         params.update(search_params)
    
#     #data = _read_chunked(_search_request, 'equity_search', params)
#     data = _search_request('equity_search', params)
    
#     return data


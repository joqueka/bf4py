#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from ._utils import _data_request, _search_request
from datetime import date, datetime, timezone, time


def trade_history(search_date:date):
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
        
        data = _data_request('derivatives_trade_history', params)
        
        maxCount = data['totalElements']
        tradelist += data['data']
        
        i += 1
    
    return tradelist

def instrument_data(isin:str):
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
    params = {'isin': isin}
    
    data = _data_request('derivatives_master_data', params)
    
    return data

def search_criteria():
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
    
    data = _search_request('derivative_search_criteria_data', params)
    
    return data
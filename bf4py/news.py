#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__all__ = ['news_by_category',
            'news_by_isin',
            'news_by_id']

from ._utils import _data_request
from datetime import datetime

def news_by_id(news_id: str):
    """
    Retrieving detail information about specific news-id.

    Parameters
    ----------
    news_id : str
        Desired news id.

    Returns
    -------
    data : TYPE
        Dict with news details.

    """
    params = {'id': news_id}
    data = _data_request('news', params)
    
    return data

def news_by_category(news_type: str ='ALL', limit: int=0, end_date: datetime = None):
    """
    Retrieve a list of news for all or a specific category.

    Parameters
    ----------
    news_type : str, optional
        Desired category or all categories. The default is 'ALL'.
    limit : int, optional
        Maximum count of news to get. The default is 0 (=unlimited).
    end_date : datetime, optional
        Earliest date up to which news should be loaded. The default is None (=unlimited).

    Returns
    -------
    news_list : TYPE
        List of dicts with basic information about news, including id, time, headline and source.

    """
    assert news_type in ['ALL',
                         'EQUITY_MARKET_REPORT',
                         'BOERSE_FRANKFURT_NEWS_ALL',
                         'COMPANY_NEWS',
                         'BOERSE_FRANKFURT_KOLUMNEN',
                         'EQUITY_AD_HOC',
                         'EQUITY_ALL',
                         'BOND',
                         'BOERSE_FRANKFURT_NEWS_ETP',
                         'FUND',
                         'BOERSE_FRANKFURT_NEWS_DERIVATIVES',
                         'COMMODITY',
                         'CURRENCY']
                         
    news_list = []
    i = 0
    CHUNK_SIZE = 1000
    if limit == 0:
        maxCount = CHUNK_SIZE + 1
    else:
        maxCount = limit
    flag = True
    c = 0
    
    while i * CHUNK_SIZE < maxCount and flag:
        params = {'withPaging': True,
                  'lang': 'de',
                  'offset': i * CHUNK_SIZE,
                  'limit': CHUNK_SIZE,
                  'newsType': news_type}
        data = _data_request('category_news', params)
        i += 1
        
        if limit == 0:
            maxCount = data['totalCount']
        
        for n in data['data']:
            #Check if either user given limit or end-date are reached
            if end_date is not None:
                if datetime.fromisoformat(n['time']).replace(tzinfo=None) < end_date:
                    flag = False
                    break
            if limit > 0:
                if c >= limit:
                    flag = False
                    break
                
            news_list.append(n)
            c += 1
    
    return news_list

def news_by_isin(isin:str, limit:int=0, end_date: datetime = None):
    """
    Retrieve all news related to a specific ISIN.

    Parameters
    ----------
    isin : str
        Desired ISIN.
    limit : int, optional
        Maximum count of news to get. The default is 0 (=unlimited).
    end_date : datetime, optional
        Earliest date up to which news should be loaded. The default is None (=unlimited).

    Returns
    -------
    news_list : TYPE
        List of dicts with basic information about news, consisting of id, time and headline.

    """   
    news_list = []
    i = 0
    CHUNK_SIZE = 1000
    if limit == 0:
        maxCount = CHUNK_SIZE + 1
    else:
        maxCount = limit
    flag = True
    c = 0
    
    while i * CHUNK_SIZE < maxCount and flag:
        params = {'withPaging': True,
                  'lang': 'de',
                  'offset': i * CHUNK_SIZE,
                  'limit': CHUNK_SIZE,
                  'isin': isin,
                  'newsType': 'ALL'}
        data = _data_request('instrument_news', params)
        i += 1
        
        if limit == 0:
            maxCount = data['totalCount']
        
        for n in data['data']:
            #Check if either user given limit or end-date are reached
            if end_date is not None:
                if datetime.fromisoformat(n['time']).replace(tzinfo=None) < end_date:
                    flag = False
                    break
            if limit > 0:
                if c >= limit:
                    flag = False
                    break
                
            news_list.append(n)
            c += 1
    
    return news_list
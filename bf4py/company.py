#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ._utils import _data_request

def upcoming_events(isin:str, limit:int = 100):
    """
    Get all upcoming events for given company (by ISIN)

    Parameters
    ----------
    isin : str
        Desired company ISIN. ISIN must be of type EQUITY or BOND, see instrument_information() -> instrumentTypeKey
    limit : int, optional
        Maximum count of events. The default is 100.

    Returns
    -------
    TYPE
        List of dicts.

    """
    params = {'isin': isin,
              'limit': limit}
    
    return _data_request('upcoming_events', params)

def about(isin:str): 
    """
    Get company description.

    Parameters
    ----------
    isin : str
        Desired company ISIN. ISIN must be of type EQUITY or BOND, see instrument_information() -> instrumentTypeKey

    Returns
    -------
    TYPE
        Dict with description.

    """
    params = {'isin': isin}
    
    return _data_request('about_the_company', params)

def contact_information(isin:str):
    """
    Get contact information for specific company

    Parameters
    ----------
    isin : str
        Desired company ISIN. ISIN must be of type EQUITY or BOND, see instrument_information() -> instrumentTypeKey

    Returns
    -------
    TYPE
        Dict with contact information.

    """
    params = {'isin': isin}
    
    return _data_request('contact_information', params)

def company_information(isin:str):
    """
    Get basic information about specific company

    Parameters
    ----------
    isin : str
        Desired company ISIN. ISIN must be of type EQUITY or BOND, see instrument_information() -> instrumentTypeKey

    Returns
    -------
    TYPE
        Dict with detailed information.

    """
    params = {'isin': isin}
    
    return _data_request('corporate_information', params)

def ipo_details(isin:str):
    """
    Get details about company's IPO. This information is not always available!

    Parameters
    ----------
    isin : str
        Desired company ISIN. ISIN must be of type EQUITY or BOND, see instrument_information() -> instrumentTypeKey

    Returns
    -------
    TYPE
        Dict with IPO details.

    """
    params = {'isin': isin}
    
    return _data_request('ipo_company_data', params)
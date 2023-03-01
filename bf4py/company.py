#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .connector import BF4PyConnector

class Company():
    def __init__(self, connector: BF4PyConnector = None, default_isin = None):
        self.default_isin = default_isin
        
        if connector is None:
            self.connector = BF4PyConnector()
        else:
            self.connector = connector
    
    def upcoming_events(self, isin:str = None, limit:int = 100):
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
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
            
        params = {'isin': isin,
                  'limit': limit}
        
        return self.connector.data_request('upcoming_events', params)
    
    def about(self, isin:str = None): 
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
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
        
        params = {'isin': isin}
        
        return self.connector.data_request('about_the_company', params)
    
    def contact_information(self, isin:str = None):
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
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
        
        params = {'isin': isin}
        
        return self.connector.data_request('contact_information', params)
    
    def company_information(self, isin:str = None):
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
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
        
        params = {'isin': isin}
        
        return self.connector.data_request('corporate_information', params)
    
    def ipo_details(self, isin:str = None):
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
        if isin is None:
            isin = self.default_isin
        assert isin is not None, 'No ISIN given'
        
        params = {'isin': isin}
        
        return self.connector.data_request('ipo_company_data', params)
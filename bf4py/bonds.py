#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .connector import BF4PyConnector
from datetime import date, datetime, timezone, time

class Bonds():
    def __init__(self, connector: BF4PyConnector = None, default_isin = None):
        self.default_isin = default_isin
        
        if connector is None:
            self.connector = BF4PyConnector()
        else:
            self.connector = connector

    
    def bond_data(self, isin:str = None, mic:str = None):
        """
        Returns all information about given bond ISIN.
    
        Parameters
        ----------
        isin : str
            ISIN of valid bond.
    
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
        
        data = self.connector.data_request('master_data_bond', params)
        
        return data
    
    
    def search_criteria(self):
        """
        Returns all multi-option criteria lists for bond search
    
        Returns
        -------
        data : TYPE
            Dict.
    
        """
        params = {'lang': 'de'}
        
        data = self.connector.search_get_request('bond_search_criteria_data', params)
        
        return data
    
    @staticmethod
    def search_parameter_template():
        """
        Returns an empty template for searching bonds. Possible parameter values for list parameters can be obtained using search_criteria()

        Returns
        -------
        params : dict
            Search-parameter template.

        """
        params = {  
                      "greenBond": None, #boolean
                      "newIssue": None, #boolean
                      "callableByIssuer": None, #boolean
                      "subordinated": None, #boolean
                      "indexed": None, #boolean
                      "market": None, #string
                      "issuers": [], #list of string
                      "issuerTypes": [], #list of string
                      "bondTypes": [], #list of string
                      "countries": [], #list of string
                      "minimumInvestment": None, #int
                      "currencies": [], #list of string
                      "segments": [], #list of string
                      "interestTypes": [], #list of string
                      "termToMaturityMin": None, #int
                      "termToMaturityMax": None, #int
                      "couponMin": None, #int
                      "couponMax": None, #int
                      "yieldMin": None, #int
                      "yieldMax": None, #int
                      "durationMin": None, #float
                      "durationMax": None, #int
                      "modifiedDurationMin": None, #float
                      "modifiedDurationMax": None, #int
                      "accruedInterestMin": None, #int
                      "accruedInterestMax": None, #int
                      "maturityDateMin": None, #int (year)
                      "maturityDateMax": None, #int (year)
                      "turnoverPrevDayMin": None, #int
                      "turnoverPrevDayMax": None, #int
                      "issueVolumeMin": None, #int
                      "issueVolumeMax": None, #int
                      "lang": "de",
                      "offset": 0,
                      "limit": 25,
                      "sorting": "NAME",
                      "sortOrder": "DESC"
                    }
        
        return params
    
    
    def search(self, params):
        """
        Searches for bonds using specified parameters.

        Parameters
        ----------
        params : dict
            Dict with parameters for bond search. Use search_parameter_template() to get a params template.
            Note that providing a parameter that is not intended for the bond type may lead to empty results.

        Returns
        -------
        bonds_list : list of dicts
            Returns a list of bonds matching the search criterias.

        """
        CHUNK_SIZE = 1000
        i = 0
        maxCount = CHUNK_SIZE + 1
        params['limit'] = CHUNK_SIZE
        
        bonds_list = []
        
        while i * CHUNK_SIZE < maxCount:
            params['offset'] = i * CHUNK_SIZE
            
            data = self.connector.search_request('bond_search', params)
            
            maxCount = data['recordsTotal']
            bonds_list += data['data']
            
            i += 1
        
        return bonds_list
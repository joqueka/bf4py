#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from .equities import Equities
from .news import News
from .derivatives import Derivatives
from .general import General
from .company import Company
from .live_data import LiveData

from .connector import BF4PyConnector


class BF4Py():
    def __init__(self, default_isin=None, default_mic=None):
        self.default_isin = default_isin
        self.default_mic = default_mic
        
        self.connector = BF4PyConnector()
        
        self.equities = Equities(self.connector, self.default_isin)
        self.news = News(self.connector, self.default_isin)
        self.company = Company(self.connector, self.default_isin)
        self.derivatives = Derivatives(self.connector, self.default_isin)
        self.general = General(self.connector, self.default_isin)
        self.live_data = LiveData(self.connector, self.default_isin)


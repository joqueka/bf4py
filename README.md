# bf4py
*A Python Package for retrieving data from boerse-frankfurt.de*

## Description

This package uses an undocumented API to retrieve data that is available on [www.boerse-frankfurt.de](https://www.boerse-frankfurt.de) (no web-scraping!). It can be used by everyone who is interested in the german stock market as an alternative to available packages like [yfinance](https://github.com/ranaroussi/yfinance) which provides data for the US stock market.

So far functions for retrieving basic data are available, especially for **equities**, **company information** and **news**. Some more for **bonds**, **funds**, **commodities** and **derivatives** will come in future depending on demand, since most of the data from the website is provided via API.

### Important notice
Data is usually delayed by 15Min by the provider and some data like bid/ask history are available only for short periods of history.

## Documentation

Functions are encapsuled in submodules. See docstrings for details about parameters. Return values are always dicts with self-describing keys, so just try out.

### bf4py.general

	.eod_data(...)
	.data_sheet_header(...)
	.instrument_information(...)
	.index_instruments(...)

### bf4py.equities

	.equity_details(...)
	.key_data(...)
	.bid_ask_history(...)
	.times_sales(...)
	.related_indices(...)
	.price_history(...)
	
### bf4py.company

	.about(...)
	.upcoming_events(...)
	.contact_information(...)
	.company_information(...)
	.ipo_details(...)

### bf4py.news

	.news_by_category(...)
	.news_by_isin(...)
	.news_by_id(...)

## Example

	import bf4py
	from datetime import datetime, timedelta

Get some basic data about a stock:

	isin = 'DE0008404005' # Allianz SE
	bf4py.general.data_sheet_header(isin)

Yields in:

	{'participationCertificate': False,
	 'isin': 'DE0008404005',
	 'wkn': '840400',
	 'instrumentName': {'originalValue': 'ALLIANZ SE NA O.N.',
	  'translations': {'others': 'Allianz SE'}},
	 'exchangeSymbol': 'ALV',
	 'instrumentTypeKey': 'equity',
	 'underlyingValueList': None,
	 'issuer': None,
	 'companyIcon': 'https://erscontent.deutsche-boerse.com/erscontentXML/logo/995.jpg',
	 'isParticipationCertificate': False}

Get the *times and sales* list of that stock on XETRA:
	
	start_date = datetime.now() - timedelta(days=1)
	end_date = datetime.now()
	
	ts = bf4py.equities.times_sales(isin, start_date, end_date)

Result is a list of dicts where each dict is an executed trade:

	[{'time': '2022-02-18T17:37:22+01:00',
	 'price': 214.1,
	 'turnover': 567076.0,
	 'turnoverInEuro': 121410971.6}, ...]



## Requirements

 	urllib
 	hashlib
  	requests
  	json


## Misc
Börse Frankfurt, Allianz and XETRA are registered brand names of their respective owners. I'm not connected in any way to one of the mentioned companys. Beyond that, I give no guarantee for the future functioning of the package as this depends on the technical framework of the provider.

Furthermore I'm not a developer, I'm just interested in exploring data. If you have an idea for improvement just let me know.
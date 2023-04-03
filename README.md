# bf4py
*A Python Package for retrieving data from boerse-frankfurt.de*

**New methods:** Now you can search derivatives using specified parameters.

**Latest update:** A lot of improvements were made under the hood. It's now object oriented resulting in better perfomance since http-sessions are reused for consecutive calls. Functions are now capsuled in classes but calls stay the same. However you must adapt function parameters since `isin` is not a positional argument anymore but an optional keyword-argument.

## Description

This package uses an undocumented API to retrieve data that is available on [www.boerse-frankfurt.de](https://www.boerse-frankfurt.de) (no web-scraping!). It can be used by everyone who is interested in the german stock market as an alternative to available packages like [yfinance](https://github.com/ranaroussi/yfinance) which provides data for the US stock market.

So far functions for retrieving basic data are available, especially for **equities**, **company information** and **news**. Some more for **bonds**, **funds**, **commodities** and **derivatives** will come in future depending on demand, since most of the data from the website is provided via API.

### Important notice
Data is usually delayed by 15Min by the provider and some data like bid/ask history are available only for short periods of history.

## API Reference

Functions are encapsuled in submodules. See docstrings for details about parameters. Return values are always dicts with self-describing keys, so just try out.

### bf4py.BF4Py() - *NEW* :rotating_light:
This new class holds the https connection and provides functions via submodules like the previous version. Furthermore a default isin can be set, if not you have to provide it with every function call as before.

	bf4py = BF4Py(default_isin='...', default_mic='...')


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
	.get_categories()

### bf4py.derivatives

	.trade_history(...)
	.instrument_data(...)
	.search_parameter_template()
	.search_derivatives(...)
	
### bf4py.live_data 
	.price_information(...)
	.live_quotes(...)
	.bid_ask_overview(...)

## Examples

	from bf4py import BF4Py
	from datetime import datetime, timedelta
	
	bf4py = BF4Py(default_isin='DE0005190003') # Default BMW

Get some basic data about *BMW* stock:

	bf4py.general.data_sheet_header() # Get info for BMW

Yields in:

	{'participationCertificate': False,
	 'isin': 'DE0005190003',
	 'wkn': '519000',
	 'instrumentName': {'originalValue': 'BAY.MOTOREN WERKE AG ST',
	  'translations': {'others': 'BMW AG St'}},
	 'exchangeSymbol': 'BMW',
	 'instrumentTypeKey': 'equity',
	 'underlyingValueList': None,
	 'issuer': None,
	 'companyIcon': 'https://erscontent.deutsche-boerse.com/erscontentXML/logo/204.jpg',
	 'isParticipationCertificate': False}

If you want to get data about another instrument just provide the ISIN:


	bf4py.general.data_sheet_header(isin='DE0005190003') # Get info for Mercedes Benz

Get the *daily OHLC data* of default stock on XETRA for one year:
	
	end_date = date.today()
	start_date = end_date - timedelta(days=365)
	
	history = bf4py.general.eod_data(start_date, end_date)
	
Returns:
	
	[{'date': '2022-03-29',
	  'open': 217.3,
	  'close': 218.55,
	  'high': 220.45,
	  'low': 216.4,
	  'turnoverPieces': 1242298,
	  'turnoverEuro': 271453308.35
	 }, ...]

Get the *times and sales* list of that stock on XETRA:
	
	start_date = datetime.now() - timedelta(days=1)
	end_date = datetime.now()
	
	ts = bf4py.equities.times_sales(start_date, end_date)

Result is a list of dicts where each dict is an executed trade:

	[{'time': '2022-02-18T17:37:22+01:00',
	 'price': 214.1,
	 'turnover': 567076.0,
	 'turnoverInEuro': 121410971.6}, ...]

**Get live-data**

For getting live data just create an receiver-client and start streaming:
	
	client = bf4py.live_data.live_quotes(isin) 	client.open_stream()

Print output will be like:

	{'isin': 'DE0008404005', 'bidLimit': 191.76, 'askLimit': 191.8, 'bidSize': 1135.0, 'askSize': 109.0, 'lastPrice': 191.78, 'timestampLastPrice': '2022-06-08T15:06:07+02:00', 'changeToPrevDayAbsolute': -4.38, 'changeToPrevDayInPercent': -2.2328711257, 'spreadAbsolute': 0.04, 'spreadRelative': 0.0208594076, 'timestamp': '2022-06-08T15:06:12+02:00', 'nominal': False, 'tradingStatus': 'CONTINUOUS'}

Finally stop transmission

	client.close()

Notes:

 - By default received data is sent to `print()` function but you can provide your own callback function for data evaluation
 - Received data can be stored in `client.data`, use flag `cache_data=True`
 - Cached data is cleared with every call of `.open_stream()`
 - Sometimes it will need some seconds to start receiving data continuously
 - Now **you can reuse** a client after a connection was closed by intend or error
 - You can check client's status by `client.active`


## Requirements

 	urllib
 	hashlib
  	requests
  	json
  	sseclient


## Misc
Börse Frankfurt, Allianz and XETRA are registered brand names of their respective owners. I'm not connected in any way to one of the mentioned companys. Beyond that, I give no guarantee for the future functioning of the package as this depends on the technical framework of the provider.

Furthermore I'm not a developer, I'm just interested in exploring data. If you have an idea for improvement just let me know.
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for the bf4py library.

Tests are organized into two categories:
  - Unit tests: Use mocks to avoid network calls (run always)
  - Integration tests: Require a live internet connection (skipped by default)

To run integration tests, set the environment variable:
    BF4PY_INTEGRATION_TESTS=1

Example:
    BF4PY_INTEGRATION_TESTS=1 python -m pytest unit_tests.py -v
"""

import os
import sys
import json
import unittest
import hashlib
import threading
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, PropertyMock, call

# ---------------------------------------------------------------------------
# Helper: decide whether integration tests should run
# ---------------------------------------------------------------------------
RUN_INTEGRATION = os.environ.get("BF4PY_INTEGRATION_TESTS", "0") == "1"
skip_integration = unittest.skipUnless(RUN_INTEGRATION,
                                       "Set BF4PY_INTEGRATION_TESTS=1 to run")

# ISINs used throughout the tests
BMW_ISIN   = "DE0005190003"   # BMW AG – standard equity on XETRA
SAP_ISIN   = "DE0007164600"   # SAP SE
DAX_ISIN   = "DE0008469008"   # DAX index
BOND_ISIN  = "DE0001102572"   # German federal bond (Bund)
DERIV_ISIN = "DE000HX5BH76"   # Example derivative (Hypovereinsbank warrant)
XETR_MIC   = "XETR"
XFRA_MIC   = "XFRA"


# ===========================================================================
# 1. BF4PyConnector
# ===========================================================================

class TestBF4PyConnector(unittest.TestCase):
    """Tests for the connector that handles API authentication and HTTP."""

    def _make_connector(self, salt="testsalt123"):
        """Create a BF4PyConnector without network calls by providing a salt."""
        from bf4py.connector import BF4PyConnector
        return BF4PyConnector(salt=salt)

    # --- Initialisation ------------------------------------------------

    def test_init_with_explicit_salt(self):
        """Connector stores the given salt and creates a requests.Session."""
        import requests
        from bf4py.connector import BF4PyConnector
        conn = BF4PyConnector(salt="mysalt")
        self.assertEqual(conn.salt, "mysalt")
        self.assertIsInstance(conn.session, requests.Session)

    def test_init_without_salt_fetches_from_web(self):
        """Without salt the constructor makes two HTTP requests to boerse-frankfurt.de."""
        from bf4py.connector import BF4PyConnector
        mock_homepage = MagicMock()
        mock_homepage.status_code = 200
        mock_homepage.text = '<script src="main.abc123.js"></script>'

        mock_jsfile = MagicMock()
        mock_jsfile.status_code = 200
        mock_jsfile.text = 'some js ... salt:"extractedsalt" ... more js'

        with patch("requests.Session") as MockSession:
            instance = MockSession.return_value
            instance.get.side_effect = [mock_homepage, mock_jsfile]
            conn = BF4PyConnector()
            self.assertEqual(conn.salt, "extractedsalt")

    def test_init_no_salt_homepage_error_raises(self):
        """If the homepage request fails, an exception is raised."""
        from bf4py.connector import BF4PyConnector
        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch("requests.Session") as MockSession:
            instance = MockSession.return_value
            instance.get.return_value = mock_response
            with self.assertRaises(Exception):
                BF4PyConnector()

    def test_init_no_salt_js_error_raises(self):
        """If the JS file request fails, an exception is raised."""
        from bf4py.connector import BF4PyConnector
        mock_homepage = MagicMock(status_code=200,
                                  text='src="main.abc.js"')
        mock_js = MagicMock(status_code=500, text="")

        with patch("requests.Session") as MockSession:
            instance = MockSession.return_value
            instance.get.side_effect = [mock_homepage, mock_js]
            with self.assertRaises(Exception):
                BF4PyConnector()

    def test_init_no_ecma_script_found_raises(self):
        """If the JS filename can't be found in the homepage, an exception is raised."""
        from bf4py.connector import BF4PyConnector
        mock_homepage = MagicMock(status_code=200, text="<html>no script here</html>")

        with patch("requests.Session") as MockSession:
            instance = MockSession.return_value
            instance.get.return_value = mock_homepage
            with self.assertRaises(Exception):
                BF4PyConnector()

    # --- _create_ids ---------------------------------------------------

    def test_create_ids_returns_required_keys(self):
        """_create_ids must return a dict with the three header keys."""
        conn = self._make_connector()
        ids = conn._create_ids("https://api.boerse-frankfurt.de/v1/data/test")
        self.assertIn("client-date", ids)
        self.assertIn("x-client-traceid", ids)
        self.assertIn("x-security", ids)

    def test_create_ids_traceid_is_md5(self):
        """x-client-traceid must be a valid 32-char hex string (MD5)."""
        conn = self._make_connector()
        ids = conn._create_ids("https://api.boerse-frankfurt.de/v1/data/test")
        traceid = ids["x-client-traceid"]
        self.assertEqual(len(traceid), 32)
        # All characters must be hex digits
        int(traceid, 16)

    def test_create_ids_xsecurity_is_md5(self):
        """x-security must be a valid 32-char hex string (MD5)."""
        conn = self._make_connector()
        ids = conn._create_ids("https://api.boerse-frankfurt.de/v1/data/test")
        xsecurity = ids["x-security"]
        self.assertEqual(len(xsecurity), 32)
        int(xsecurity, 16)

    def test_create_ids_client_date_format(self):
        """client-date must end with 'Z' and contain 'T' (ISO 8601 UTC)."""
        conn = self._make_connector()
        ids = conn._create_ids("https://api.boerse-frankfurt.de/v1/data/test")
        client_date = ids["client-date"]
        self.assertTrue(client_date.endswith("Z"))
        self.assertIn("T", client_date)

    def test_create_ids_different_urls_give_different_traceids(self):
        """Different URLs should produce different trace IDs."""
        conn = self._make_connector()
        ids1 = conn._create_ids("https://api.boerse-frankfurt.de/v1/data/endpoint_a")
        ids2 = conn._create_ids("https://api.boerse-frankfurt.de/v1/data/endpoint_b")
        # Very unlikely to be equal
        self.assertNotEqual(ids1["x-client-traceid"], ids2["x-client-traceid"])

    # --- URL builders --------------------------------------------------

    def test_get_data_url_structure(self):
        """_get_data_url must build a correct query string URL."""
        conn = self._make_connector()
        url = conn._get_data_url("price_history", {"isin": "DE0005190003", "mic": "XETR"})
        self.assertTrue(url.startswith("https://api.boerse-frankfurt.de/v1/data/price_history?"))
        self.assertIn("isin=DE0005190003", url)
        self.assertIn("mic=XETR", url)

    def test_get_search_url_structure(self):
        """_get_search_url must build a correct URL."""
        conn = self._make_connector()
        url = conn._get_search_url("equity_search", {})
        self.assertIn("https://api.boerse-frankfurt.de/v1/search/equity_search", url)

    def test_get_search_url_with_params(self):
        """_get_search_url with params appends a query string."""
        conn = self._make_connector()
        url = conn._get_search_url("equity_search", {"lang": "de"})
        self.assertIn("lang=de", url)

    # --- data_request --------------------------------------------------

    def test_data_request_returns_parsed_json(self):
        """data_request must return the parsed JSON body from the API."""
        conn = self._make_connector()
        mock_resp = MagicMock()
        mock_resp.text = json.dumps({"key": "value"})
        conn.session.get = MagicMock(return_value=mock_resp)

        result = conn.data_request("some_endpoint", {"isin": BMW_ISIN})
        self.assertEqual(result, {"key": "value"})

    def test_data_request_raises_on_messages_key(self):
        """data_request must raise if the API response contains a 'messages' key."""
        conn = self._make_connector()
        mock_resp = MagicMock()
        mock_resp.text = json.dumps({"messages": ["Error occurred"]})
        conn.session.get = MagicMock(return_value=mock_resp)

        with self.assertRaises(Exception):
            conn.data_request("some_endpoint", {})

    # --- search_request ------------------------------------------------

    def test_search_request_uses_post(self):
        """search_request must issue a POST request to the search URL."""
        conn = self._make_connector()
        mock_resp = MagicMock()
        mock_resp.text = json.dumps({"data": [], "recordsTotal": 0})
        conn.session.post = MagicMock(return_value=mock_resp)

        result = conn.search_request("bond_search", {"lang": "de"})
        self.assertTrue(conn.session.post.called)
        self.assertEqual(result, {"data": [], "recordsTotal": 0})


# ===========================================================================
# 2. BF4Py – Main class
# ===========================================================================

class TestBF4Py(unittest.TestCase):
    """Tests for the BF4Py orchestrator class."""

    def _bf4py(self, isin=None, mic=None):
        from bf4py import BF4Py
        with patch("bf4py.connector.BF4PyConnector.__init__", return_value=None):
            with patch("bf4py.connector.BF4PyConnector.__del__", return_value=None):
                bf = BF4Py.__new__(BF4Py)
                bf.default_isin = isin
                bf.default_mic = mic
                bf.connector = MagicMock()
                from bf4py.equities import Equities
                from bf4py.news import News
                from bf4py.company import Company
                from bf4py.derivatives import Derivatives
                from bf4py.general import General
                from bf4py.live_data import LiveData
                bf.equities = Equities(connector=bf.connector, default_isin=isin)
                bf.news = News(connector=bf.connector, default_isin=isin)
                bf.company = Company(connector=bf.connector, default_isin=isin)
                bf.derivatives = Derivatives(connector=bf.connector, default_isin=isin)
                bf.general = General(connector=bf.connector, default_isin=isin)
                bf.live_data = LiveData(connector=bf.connector, default_isin=isin)
                return bf

    def test_submodules_are_initialized(self):
        """BF4Py must expose all six sub-modules after construction."""
        from bf4py.equities import Equities
        from bf4py.news import News
        from bf4py.company import Company
        from bf4py.derivatives import Derivatives
        from bf4py.general import General
        from bf4py.live_data import LiveData

        bf = self._bf4py(isin=BMW_ISIN)
        self.assertIsInstance(bf.equities, Equities)
        self.assertIsInstance(bf.news, News)
        self.assertIsInstance(bf.company, Company)
        self.assertIsInstance(bf.derivatives, Derivatives)
        self.assertIsInstance(bf.general, General)
        self.assertIsInstance(bf.live_data, LiveData)

    def test_default_isin_propagated(self):
        """BF4Py must propagate the default_isin to every sub-module."""
        bf = self._bf4py(isin=BMW_ISIN)
        for module in (bf.equities, bf.news, bf.company,
                       bf.derivatives, bf.general, bf.live_data):
            self.assertEqual(module.default_isin, BMW_ISIN)

    def test_no_default_isin(self):
        """BF4Py must accept None as default_isin."""
        bf = self._bf4py()
        self.assertIsNone(bf.default_isin)


# ===========================================================================
# 3. General module
# ===========================================================================

class TestGeneral(unittest.TestCase):

    def setUp(self):
        from bf4py.general import General
        self.mock_connector = MagicMock()
        self.gen = General(connector=self.mock_connector, default_isin=BMW_ISIN)

    # --- eod_data ------------------------------------------------------

    def test_eod_data_calls_price_history(self):
        """eod_data must call data_request with 'price_history'."""
        self.mock_connector.data_request.return_value = {"data": []}
        min_date = date.today() - timedelta(days=30)
        max_date = date.today()
        result = self.gen.eod_data(min_date, max_date)
        self.mock_connector.data_request.assert_called_once()
        args = self.mock_connector.data_request.call_args
        self.assertEqual(args[0][0], "price_history")

    def test_eod_data_passes_isin(self):
        """eod_data must include the correct ISIN in the params."""
        self.mock_connector.data_request.return_value = {"data": []}
        min_date = date.today() - timedelta(days=10)
        result = self.gen.eod_data(min_date, isin=SAP_ISIN)
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["isin"], SAP_ISIN)

    def test_eod_data_uses_default_isin(self):
        """eod_data must fall back to default_isin when isin is not supplied."""
        self.mock_connector.data_request.return_value = {"data": []}
        min_date = date.today() - timedelta(days=5)
        self.gen.eod_data(min_date)
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["isin"], BMW_ISIN)

    def test_eod_data_no_isin_raises(self):
        """eod_data must raise AssertionError when no ISIN is available."""
        from bf4py.general import General
        gen_no_isin = General(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            gen_no_isin.eod_data(date.today() - timedelta(days=5))

    def test_eod_data_date_params_formatted(self):
        """eod_data must send minDate/maxDate in YYYY-MM-DD format."""
        self.mock_connector.data_request.return_value = {"data": []}
        min_date = date(2024, 1, 15)
        max_date = date(2024, 6, 30)
        self.gen.eod_data(min_date, max_date)
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["minDate"], "2024-01-15")
        self.assertEqual(params["maxDate"], "2024-06-30")

    def test_eod_data_returns_data_list(self):
        """eod_data must return only the 'data' field from the API response."""
        expected = [{"date": "2024-01-15", "open": 100}]
        self.mock_connector.data_request.return_value = {"data": expected}
        min_date = date.today() - timedelta(days=10)
        result = self.gen.eod_data(min_date)
        self.assertEqual(result, expected)

    # --- data_sheet_header ---------------------------------------------

    def test_data_sheet_header_calls_correct_endpoint(self):
        """data_sheet_header must call data_request with 'data_sheet_header'."""
        self.mock_connector.data_request.return_value = {"isin": BMW_ISIN}
        result = self.gen.data_sheet_header()
        self.mock_connector.data_request.assert_called_once()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "data_sheet_header")

    def test_data_sheet_header_no_isin_raises(self):
        """data_sheet_header must raise AssertionError if no ISIN is available."""
        from bf4py.general import General
        gen = General(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            gen.data_sheet_header()

    def test_data_sheet_header_explicit_isin(self):
        """data_sheet_header must use the explicitly passed ISIN."""
        self.mock_connector.data_request.return_value = {}
        self.gen.data_sheet_header(isin=SAP_ISIN)
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["isin"], SAP_ISIN)

    # --- instrument_information ----------------------------------------

    def test_instrument_information_endpoint(self):
        """instrument_information must use the 'instrument_information' endpoint."""
        self.mock_connector.data_request.return_value = {}
        self.gen.instrument_information()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "instrument_information")

    def test_instrument_information_no_isin_raises(self):
        """instrument_information must raise AssertionError if no ISIN is available."""
        from bf4py.general import General
        gen = General(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            gen.instrument_information()

    # --- index_instruments ---------------------------------------------

    def test_index_instruments_default_dax(self):
        """index_instruments must use the DAX ISIN by default."""
        self.mock_connector.search_request.return_value = {"data": []}
        self.gen.index_instruments()
        params = self.mock_connector.search_request.call_args[0][1]
        self.assertIn(DAX_ISIN, params["indices"])

    def test_index_instruments_custom_isin(self):
        """index_instruments must accept a custom index ISIN."""
        self.mock_connector.search_request.return_value = {"data": []}
        custom_index = "DE0008469008"
        self.gen.index_instruments(isin=custom_index)
        params = self.mock_connector.search_request.call_args[0][1]
        self.assertIn(custom_index, params["indices"])

    def test_index_instruments_returns_list_of_dicts(self):
        """index_instruments must return a list with name/isin/wkn for each entry."""
        api_response = {
            "data": [
                {
                    "name": {"originalValue": "Allianz SE",
                             "translations": {"de": "Allianz SE"}},
                    "isin": "DE0008404005",
                    "wkn": "840400"
                }
            ]
        }
        self.mock_connector.search_request.return_value = api_response
        result = self.gen.index_instruments()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["isin"], "DE0008404005")
        self.assertIn("name", result[0])
        self.assertIn("wkn", result[0])

    # --- _get_name helper ----------------------------------------------

    def test_get_name_uses_original_value(self):
        """_get_name must return originalValue when no translations are present."""
        name_dict = {"originalValue": "Test Corp"}
        self.assertEqual(self.gen._get_name(name_dict), "Test Corp")

    def test_get_name_uses_de_translation(self):
        """_get_name must prefer the German translation."""
        name_dict = {"originalValue": "Test Corp",
                     "translations": {"de": "Test GmbH"}}
        self.assertEqual(self.gen._get_name(name_dict), "Test GmbH")

    def test_get_name_uses_others_translation(self):
        """_get_name must use 'others' translation over 'de'."""
        name_dict = {"originalValue": "Test Corp",
                     "translations": {"de": "Test GmbH", "others": "Test Others"}}
        self.assertEqual(self.gen._get_name(name_dict), "Test Others")


# ===========================================================================
# 4. Equities module
# ===========================================================================

class TestEquities(unittest.TestCase):

    def setUp(self):
        from bf4py.equities import Equities
        self.mock_connector = MagicMock()
        self.eq = Equities(connector=self.mock_connector, default_isin=BMW_ISIN)

    # --- equity_details ------------------------------------------------

    def test_equity_details_endpoint(self):
        """equity_details must call 'equity_master_data'."""
        self.mock_connector.data_request.return_value = {}
        self.eq.equity_details()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "equity_master_data")

    def test_equity_details_no_isin_raises(self):
        from bf4py.equities import Equities
        eq = Equities(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            eq.equity_details()

    def test_equity_details_explicit_isin(self):
        self.mock_connector.data_request.return_value = {}
        self.eq.equity_details(isin=SAP_ISIN)
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["isin"], SAP_ISIN)

    # --- key_data ------------------------------------------------------

    def test_key_data_endpoint(self):
        """key_data must call 'equity_key_data'."""
        self.mock_connector.data_request.return_value = {}
        self.eq.key_data()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "equity_key_data")

    def test_key_data_no_isin_raises(self):
        from bf4py.equities import Equities
        eq = Equities(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            eq.key_data()

    # --- bid_ask_history -----------------------------------------------

    def test_bid_ask_history_single_chunk(self):
        """bid_ask_history must aggregate data and stop when totalCount is reached."""
        api_response = {"totalCount": 2, "data": [{"bid": 1.0}, {"ask": 1.1}]}
        self.mock_connector.data_request.return_value = api_response

        start = datetime.now(timezone.utc) - timedelta(hours=2)
        end   = datetime.now(timezone.utc)
        result = self.eq.bid_ask_history(start, end)

        self.assertEqual(len(result), 2)
        self.mock_connector.data_request.assert_called_once()

    def test_bid_ask_history_pagination(self):
        """bid_ask_history must page through results when totalCount > CHUNK_SIZE."""
        chunk = [{"bid": i} for i in range(1000)]
        responses = [
            {"totalCount": 1500, "data": chunk},
            {"totalCount": 1500, "data": [{"bid": i} for i in range(500)]},
        ]
        self.mock_connector.data_request.side_effect = responses

        start = datetime.now(timezone.utc) - timedelta(hours=2)
        result = self.eq.bid_ask_history(start)
        self.assertEqual(len(result), 1500)
        self.assertEqual(self.mock_connector.data_request.call_count, 2)

    def test_bid_ask_history_utc_timestamps(self):
        """bid_ask_history must convert timestamps to UTC ISO format."""
        self.mock_connector.data_request.return_value = {"totalCount": 0, "data": []}
        start = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        end   = datetime(2024, 6, 1, 18, 0, 0, tzinfo=timezone.utc)
        self.eq.bid_ask_history(start, end)
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertIn("Z", params["from"])
        self.assertIn("Z", params["to"])

    def test_bid_ask_history_no_isin_raises(self):
        from bf4py.equities import Equities
        eq = Equities(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            eq.bid_ask_history(datetime.now())

    # --- times_sales ---------------------------------------------------

    def test_times_sales_endpoint(self):
        """times_sales must call 'tick_data'."""
        self.mock_connector.data_request.return_value = {"totalCount": 0, "ticks": []}
        self.eq.times_sales(datetime.now() - timedelta(days=1))
        self.assertEqual(self.mock_connector.data_request.call_args[0][0], "tick_data")

    def test_times_sales_default_end_is_now(self):
        """times_sales must set end to now when end is None."""
        self.mock_connector.data_request.return_value = {"totalCount": 0, "ticks": []}
        before = datetime.now(timezone.utc)
        self.eq.times_sales(datetime.now() - timedelta(hours=1))
        after = datetime.now(timezone.utc)
        params = self.mock_connector.data_request.call_args[0][1]
        # maxDateTime should be between before and after
        max_dt_str = params["maxDateTime"].replace("Z", "+00:00")
        max_dt = datetime.fromisoformat(max_dt_str)
        self.assertGreaterEqual(max_dt, before)
        self.assertLessEqual(max_dt, after)

    def test_times_sales_no_isin_raises(self):
        from bf4py.equities import Equities
        eq = Equities(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            eq.times_sales(datetime.now())

    def test_times_sales_returns_ticks(self):
        """times_sales must return the 'ticks' list."""
        expected = [{"price": 100.5}, {"price": 101.0}]
        self.mock_connector.data_request.return_value = {
            "totalCount": 2, "ticks": expected
        }
        result = self.eq.times_sales(datetime.now() - timedelta(hours=1))
        self.assertEqual(result, expected)

    # --- related_indices -----------------------------------------------

    def test_related_indices_endpoint(self):
        """related_indices must call 'related_indices'."""
        self.mock_connector.data_request.return_value = []
        self.eq.related_indices()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "related_indices")

    def test_related_indices_no_isin_raises(self):
        from bf4py.equities import Equities
        eq = Equities(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            eq.related_indices()


# ===========================================================================
# 5. Company module
# ===========================================================================

class TestCompany(unittest.TestCase):

    def setUp(self):
        from bf4py.company import Company
        self.mock_connector = MagicMock()
        self.co = Company(connector=self.mock_connector, default_isin=BMW_ISIN)

    def test_about_endpoint(self):
        self.mock_connector.data_request.return_value = {}
        self.co.about()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "about_the_company")

    def test_about_no_isin_raises(self):
        from bf4py.company import Company
        co = Company(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            co.about()

    def test_upcoming_events_endpoint(self):
        self.mock_connector.data_request.return_value = []
        self.co.upcoming_events()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "upcoming_events")

    def test_upcoming_events_default_limit(self):
        self.mock_connector.data_request.return_value = []
        self.co.upcoming_events()
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["limit"], 100)

    def test_upcoming_events_custom_limit(self):
        self.mock_connector.data_request.return_value = []
        self.co.upcoming_events(limit=5)
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["limit"], 5)

    def test_upcoming_events_no_isin_raises(self):
        from bf4py.company import Company
        co = Company(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            co.upcoming_events()

    def test_contact_information_endpoint(self):
        self.mock_connector.data_request.return_value = {}
        self.co.contact_information()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "contact_information")

    def test_contact_information_no_isin_raises(self):
        from bf4py.company import Company
        co = Company(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            co.contact_information()

    def test_company_information_endpoint(self):
        self.mock_connector.data_request.return_value = {}
        self.co.company_information()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "corporate_information")

    def test_company_information_no_isin_raises(self):
        from bf4py.company import Company
        co = Company(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            co.company_information()

    def test_ipo_details_endpoint(self):
        self.mock_connector.data_request.return_value = {}
        self.co.ipo_details()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "ipo_company_data")

    def test_ipo_details_no_isin_raises(self):
        from bf4py.company import Company
        co = Company(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            co.ipo_details()

    def test_explicit_isin_overrides_default(self):
        """Each company method must accept an explicit ISIN that overrides the default."""
        self.mock_connector.data_request.return_value = {}
        for method in (self.co.about, self.co.contact_information,
                       self.co.company_information, self.co.ipo_details):
            self.mock_connector.data_request.reset_mock()
            method(isin=SAP_ISIN)
            params = self.mock_connector.data_request.call_args[0][1]
            self.assertEqual(params["isin"], SAP_ISIN,
                             f"{method.__name__} did not use explicit ISIN")


# ===========================================================================
# 6. News module
# ===========================================================================

class TestNews(unittest.TestCase):

    def setUp(self):
        from bf4py.news import News
        self.mock_connector = MagicMock()
        self.news = News(connector=self.mock_connector, default_isin=BMW_ISIN)

    # --- get_categories ------------------------------------------------

    def test_get_categories_returns_list(self):
        categories = self.news.get_categories()
        self.assertIsInstance(categories, list)
        self.assertGreater(len(categories), 0)

    def test_get_categories_contains_all(self):
        self.assertIn("ALL", self.news.get_categories())

    def test_get_categories_contains_expected(self):
        expected = ["EQUITY_MARKET_REPORT", "COMPANY_NEWS",
                    "EQUITY_AD_HOC", "EQUITY_ALL", "BOND"]
        for cat in expected:
            self.assertIn(cat, self.news.get_categories())

    # --- news_by_category ----------------------------------------------

    def test_news_by_category_invalid_type_raises(self):
        with self.assertRaises(AssertionError):
            self.news.news_by_category(news_type="INVALID_CATEGORY")

    def test_news_by_category_default_is_all(self):
        self.mock_connector.data_request.return_value = {
            "totalCount": 0, "data": []
        }
        self.news.news_by_category()
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["newsType"], "ALL")

    def test_news_by_category_limit_stops_early(self):
        """When limit is set, news_by_category must return at most limit items."""
        items = [{"id": str(i), "time": "2024-01-01T10:00:00",
                  "headline": f"News {i}"} for i in range(20)]
        self.mock_connector.data_request.return_value = {
            "totalCount": 20, "data": items
        }
        result = self.news.news_by_category(limit=5)
        self.assertEqual(len(result), 5)

    def test_news_by_category_end_date_raises_name_error(self):
        """
        KNOWN BUG: news.py imports `datetime` at class scope with
            `from datetime import datetime`
        but then uses bare `datetime` inside a method body, where class-level
        names are not in scope. This causes a NameError at runtime whenever
        `end_date` is not None.

        The same bug exists in news_by_isin() with an end_date argument.
        """
        items = [
            {"id": "1", "time": "2024-06-01T10:00:00", "headline": "Recent"},
            {"id": "2", "time": "2024-01-01T10:00:00", "headline": "Old"},
        ]
        self.mock_connector.data_request.return_value = {
            "totalCount": 2, "data": items
        }
        end_date = datetime(2024, 3, 1)
        with self.assertRaises(NameError):
            self.news.news_by_category(end_date=end_date)

    def test_news_by_category_uses_correct_endpoint(self):
        self.mock_connector.data_request.return_value = {"totalCount": 0, "data": []}
        self.news.news_by_category(news_type="COMPANY_NEWS")
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "category_news")

    # --- news_by_isin --------------------------------------------------

    def test_news_by_isin_uses_correct_endpoint(self):
        self.mock_connector.data_request.return_value = {"totalCount": 0, "data": []}
        self.news.news_by_isin()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "instrument_news")

    def test_news_by_isin_includes_isin_in_params(self):
        self.mock_connector.data_request.return_value = {"totalCount": 0, "data": []}
        self.news.news_by_isin()
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["isin"], BMW_ISIN)

    def test_news_by_isin_no_isin_raises(self):
        from bf4py.news import News
        news = News(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            news.news_by_isin()

    def test_news_by_isin_explicit_isin(self):
        self.mock_connector.data_request.return_value = {"totalCount": 0, "data": []}
        self.news.news_by_isin(isin=SAP_ISIN)
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["isin"], SAP_ISIN)

    def test_news_by_isin_limit(self):
        items = [{"id": str(i), "time": "2024-06-01T10:00:00"}
                 for i in range(10)]
        self.mock_connector.data_request.return_value = {
            "totalCount": 10, "data": items
        }
        result = self.news.news_by_isin(limit=3)
        self.assertEqual(len(result), 3)

    # --- news_by_id ----------------------------------------------------

    def test_news_by_id_endpoint(self):
        self.mock_connector.data_request.return_value = {}
        self.news.news_by_id("abc123")
        self.assertEqual(self.mock_connector.data_request.call_args[0][0], "news")

    def test_news_by_id_passes_id(self):
        self.mock_connector.data_request.return_value = {}
        self.news.news_by_id("my-news-id")
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["id"], "my-news-id")


# ===========================================================================
# 7. Bonds module
# ===========================================================================

class TestBonds(unittest.TestCase):

    def setUp(self):
        from bf4py.bonds import Bonds
        self.mock_connector = MagicMock()
        self.bonds = Bonds(connector=self.mock_connector)

    # --- search_parameter_template -------------------------------------

    def test_search_parameter_template_is_dict(self):
        """search_parameter_template must return a dict."""
        from bf4py.bonds import Bonds
        template = Bonds.search_parameter_template()
        self.assertIsInstance(template, dict)

    def test_search_parameter_template_has_required_keys(self):
        from bf4py.bonds import Bonds
        template = Bonds.search_parameter_template()
        required_keys = ["lang", "offset", "limit", "sorting", "sortOrder",
                         "greenBond", "issuers", "currencies"]
        for key in required_keys:
            self.assertIn(key, template,
                          f"Key '{key}' missing from search_parameter_template()")

    def test_search_parameter_template_is_static(self):
        """search_parameter_template must be callable as a static method."""
        from bf4py.bonds import Bonds
        # Should work without an instance
        result = Bonds.search_parameter_template()
        self.assertIsInstance(result, dict)

    # --- search --------------------------------------------------------

    def test_search_calls_bond_search(self):
        """search must call search_request with 'bond_search'."""
        self.mock_connector.search_request.return_value = {
            "recordsTotal": 0, "data": []
        }
        from bf4py.bonds import Bonds
        params = Bonds.search_parameter_template()
        self.bonds.search(params)
        self.assertEqual(self.mock_connector.search_request.call_args[0][0],
                         "bond_search")

    def test_search_paginates(self):
        """search must issue multiple requests when recordsTotal > CHUNK_SIZE."""
        chunk = [{"isin": f"DE{i:012d}"} for i in range(1000)]
        self.mock_connector.search_request.side_effect = [
            {"recordsTotal": 1200, "data": chunk},
            {"recordsTotal": 1200, "data": [{"isin": "extra"} for _ in range(200)]},
        ]
        from bf4py.bonds import Bonds
        params = Bonds.search_parameter_template()
        result = self.bonds.search(params)
        self.assertEqual(len(result), 1200)
        self.assertEqual(self.mock_connector.search_request.call_count, 2)

    def test_search_empty_results(self):
        self.mock_connector.search_request.return_value = {
            "recordsTotal": 0, "data": []
        }
        from bf4py.bonds import Bonds
        result = self.bonds.search(Bonds.search_parameter_template())
        self.assertEqual(result, [])

    # --- bond_data (known bug: missing default_mic) --------------------

    def test_bond_data_missing_default_mic_raises_attribute_error(self):
        """
        KNOWN BUG: Bonds.__init__ does not set self.default_mic,
        so bond_data() raises AttributeError when mic=None is passed.
        """
        with self.assertRaises(AttributeError):
            self.bonds.bond_data(isin=BOND_ISIN)

    def test_bond_data_with_explicit_mic_calls_correct_endpoint(self):
        """When both isin and mic are provided, bond_data calls 'master_data_bond'."""
        self.mock_connector.data_request.return_value = {}
        self.bonds.bond_data(isin=BOND_ISIN, mic=XFRA_MIC)
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "master_data_bond")

    def test_bond_data_no_isin_raises(self):
        with self.assertRaises(AssertionError):
            self.bonds.bond_data(isin=None, mic=XFRA_MIC)


# ===========================================================================
# 8. Derivatives module
# ===========================================================================

class TestDerivatives(unittest.TestCase):

    def setUp(self):
        from bf4py.derivatives import Derivatives
        self.mock_connector = MagicMock()
        self.deriv = Derivatives(connector=self.mock_connector,
                                 default_isin=DERIV_ISIN)

    # --- search_params (static) ----------------------------------------

    def test_search_params_is_dict(self):
        from bf4py.derivatives import Derivatives
        params = Derivatives.search_params()
        self.assertIsInstance(params, dict)

    def test_search_params_contains_required_keys(self):
        from bf4py.derivatives import Derivatives
        params = Derivatives.search_params()
        for key in ["lang", "sorting", "sortOrder", "types", "underlyings"]:
            self.assertIn(key, params)

    def test_search_params_static(self):
        from bf4py.derivatives import Derivatives
        result = Derivatives.search_params()
        self.assertIsInstance(result, dict)

    # --- trade_history -------------------------------------------------

    def test_trade_history_calls_correct_endpoint(self):
        self.mock_connector.data_request.return_value = {
            "totalElements": 0, "data": []
        }
        self.deriv.trade_history(search_date=date.today())
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "derivatives_trade_history")

    def test_trade_history_paginates(self):
        chunk = [{"isin": "X"} for _ in range(1000)]
        self.mock_connector.data_request.side_effect = [
            {"totalElements": 1500, "data": chunk},
            {"totalElements": 1500, "data": [{"isin": "Y"}] * 500},
        ]
        result = self.deriv.trade_history(date.today())
        self.assertEqual(len(result), 1500)
        self.assertEqual(self.mock_connector.data_request.call_count, 2)

    def test_trade_history_utc_timestamps(self):
        """trade_history must format from/to as UTC ISO strings."""
        self.mock_connector.data_request.return_value = {
            "totalElements": 0, "data": []
        }
        self.deriv.trade_history(date(2024, 6, 15))
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertIn("Z", params["from"])
        self.assertIn("Z", params["to"])

    # --- instrument_data -----------------------------------------------

    def test_instrument_data_endpoint(self):
        self.mock_connector.data_request.return_value = {}
        self.deriv.instrument_data()
        self.assertEqual(self.mock_connector.data_request.call_args[0][0],
                         "derivatives_master_data")

    def test_instrument_data_no_isin_raises(self):
        from bf4py.derivatives import Derivatives
        deriv = Derivatives(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            deriv.instrument_data()

    def test_instrument_data_passes_isin_and_mic(self):
        self.mock_connector.data_request.return_value = {}
        self.deriv.instrument_data(isin=DERIV_ISIN, mic=XETR_MIC)
        params = self.mock_connector.data_request.call_args[0][1]
        self.assertEqual(params["isin"], DERIV_ISIN)
        self.assertEqual(params["mic"], XETR_MIC)

    # --- search_criteria -----------------------------------------------

    def test_search_criteria_calls_search_request(self):
        self.mock_connector.search_request.return_value = {}
        self.deriv.search_criteria()
        self.mock_connector.search_request.assert_called_once()
        self.assertEqual(self.mock_connector.search_request.call_args[0][0],
                         "derivative_search_criteria_data")

    # --- search_derivatives --------------------------------------------

    def test_search_derivatives_endpoint(self):
        self.mock_connector.search_request.return_value = {
            "recordsTotal": 0, "data": []
        }
        from bf4py.derivatives import Derivatives
        params = Derivatives.search_params()
        self.deriv.search_derivatives(params)
        self.assertEqual(self.mock_connector.search_request.call_args[0][0],
                         "derivative_search")

    def test_search_derivatives_paginates(self):
        chunk = [{"isin": f"DE{i:010d}"} for i in range(1000)]
        self.mock_connector.search_request.side_effect = [
            {"recordsTotal": 2000, "data": chunk},
            {"recordsTotal": 2000, "data": chunk},
        ]
        from bf4py.derivatives import Derivatives
        params = Derivatives.search_params()
        result = self.deriv.search_derivatives(params)
        self.assertEqual(len(result), 2000)


# ===========================================================================
# 9. LiveData module
# ===========================================================================

class TestLiveData(unittest.TestCase):

    def setUp(self):
        from bf4py.live_data import LiveData
        self.mock_connector = MagicMock()
        self.live = LiveData(connector=self.mock_connector, default_isin=BMW_ISIN)

    def _make_client_for(self, method_name):
        from bf4py.live_data import BFStreamClient
        method = getattr(self.live, method_name)
        client = method()
        self.assertIsInstance(client, BFStreamClient)
        return client

    def test_price_information_returns_stream_client(self):
        from bf4py.live_data import BFStreamClient
        client = self.live.price_information()
        self.assertIsInstance(client, BFStreamClient)

    def test_bid_ask_overview_returns_stream_client(self):
        from bf4py.live_data import BFStreamClient
        client = self.live.bid_ask_overview()
        self.assertIsInstance(client, BFStreamClient)

    def test_live_quotes_returns_stream_client(self):
        from bf4py.live_data import BFStreamClient
        client = self.live.live_quotes()
        self.assertIsInstance(client, BFStreamClient)

    def test_price_information_no_isin_raises(self):
        from bf4py.live_data import LiveData
        live = LiveData(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            live.price_information()

    def test_bid_ask_overview_no_isin_raises(self):
        from bf4py.live_data import LiveData
        live = LiveData(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            live.bid_ask_overview()

    def test_live_quotes_no_isin_raises(self):
        from bf4py.live_data import LiveData
        live = LiveData(connector=self.mock_connector)
        with self.assertRaises(AssertionError):
            live.live_quotes()

    def test_client_uses_correct_isin(self):
        client = self.live.price_information()
        self.assertEqual(client.params["isin"], BMW_ISIN)

    def test_client_uses_default_mic_xetr(self):
        client = self.live.price_information()
        self.assertEqual(client.params["mic"], "XETR")

    def test_client_custom_mic(self):
        client = self.live.price_information(mic="XFRA")
        self.assertEqual(client.params["mic"], "XFRA")

    def test_client_registered_in_streaming_clients(self):
        """Newly created clients must be appended to live_data.streaming_clients."""
        initial_count = len(self.live.streaming_clients)
        self.live.price_information()
        self.assertEqual(len(self.live.streaming_clients), initial_count + 1)

    def test_client_cache_data_flag(self):
        """cache_data flag must be passed through to BFStreamClient."""
        client = self.live.price_information(cache_data=True)
        self.assertTrue(client.cache_data)

    def test_client_not_active_before_open(self):
        """A freshly created BFStreamClient must not be active yet."""
        client = self.live.price_information()
        self.assertFalse(client.active)


# ===========================================================================
# 10. BFStreamClient
# ===========================================================================

class TestBFStreamClient(unittest.TestCase):

    def _make_client(self, isin=BMW_ISIN, cache_data=False):
        from bf4py.live_data import BFStreamClient
        mock_connector = MagicMock()
        cb = MagicMock()
        client = BFStreamClient(
            function="price_information",
            params={"isin": isin, "mic": "XETR"},
            callback=cb,
            connector=mock_connector,
            cache_data=cache_data,
        )
        return client, mock_connector, cb

    def test_initial_state(self):
        """A new BFStreamClient must start in an inactive, unstarted state."""
        client, _, _ = self._make_client()
        self.assertFalse(client.active)
        self.assertFalse(client.stop)
        self.assertIsNone(client.receiver_thread)
        self.assertEqual(client.data, [])

    def test_open_stream_starts_thread(self):
        """open_stream must create a daemon thread and mark active=True."""
        client, mock_connector, _ = self._make_client()
        # Make stream_request return an iterable with no events
        mock_sse = MagicMock()
        mock_sse.events.return_value = iter([])
        mock_connector.stream_request.return_value = mock_sse

        client.open_stream()
        self.assertTrue(client.active)
        self.assertIsNotNone(client.receiver_thread)
        self.assertTrue(client.receiver_thread.daemon)
        client.close()

    def test_open_stream_idempotent(self):
        """Calling open_stream twice must not create a second thread."""
        client, mock_connector, _ = self._make_client()
        mock_sse = MagicMock()
        mock_sse.events.return_value = iter([])
        mock_connector.stream_request.return_value = mock_sse

        client.open_stream()
        thread_first = client.receiver_thread
        client.open_stream()           # second call — must be a no-op
        self.assertIs(client.receiver_thread, thread_first)
        client.close()

    def test_callback_invoked_on_message(self):
        """The callback must be called with the parsed JSON payload for each message."""
        from bf4py.live_data import BFStreamClient

        received = []
        def my_callback(data):
            received.append(data)

        mock_connector = MagicMock()
        event = MagicMock()
        event.event = "message"
        event.data = json.dumps({"price": 99.5})

        mock_sse = MagicMock()
        mock_sse.events.return_value = iter([event])
        mock_connector.stream_request.return_value = mock_sse

        client = BFStreamClient(
            function="price_information",
            params={"isin": BMW_ISIN, "mic": "XETR"},
            callback=my_callback,
            connector=mock_connector,
            cache_data=True,
        )
        client.open_stream()
        # Wait for the daemon thread to process the single event
        client.receiver_thread.join(timeout=3)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["price"], 99.5)

    def test_cache_data_stores_all_events(self):
        """With cache_data=True, all received events must be stored in client.data."""
        from bf4py.live_data import BFStreamClient

        mock_connector = MagicMock()
        events = []
        for price in [10.0, 11.0, 12.0]:
            ev = MagicMock()
            ev.event = "message"
            ev.data = json.dumps({"price": price})
            events.append(ev)

        mock_sse = MagicMock()
        mock_sse.events.return_value = iter(events)
        mock_connector.stream_request.return_value = mock_sse

        client = BFStreamClient(
            function="price_information",
            params={"isin": BMW_ISIN, "mic": "XETR"},
            callback=None,
            connector=mock_connector,
            cache_data=True,
        )
        client.open_stream()
        client.receiver_thread.join(timeout=3)

        self.assertEqual(len(client.data), 3)
        prices = [d["price"] for d in client.data]
        self.assertEqual(prices, [10.0, 11.0, 12.0])

    def test_no_cache_keeps_only_latest(self):
        """With cache_data=False, client.data should contain only the last event."""
        from bf4py.live_data import BFStreamClient

        mock_connector = MagicMock()
        events = []
        for price in [10.0, 11.0, 12.0]:
            ev = MagicMock()
            ev.event = "message"
            ev.data = json.dumps({"price": price})
            events.append(ev)

        mock_sse = MagicMock()
        mock_sse.events.return_value = iter(events)
        mock_connector.stream_request.return_value = mock_sse

        client = BFStreamClient(
            function="price_information",
            params={"isin": BMW_ISIN, "mic": "XETR"},
            callback=None,
            connector=mock_connector,
            cache_data=False,
        )
        client.open_stream()
        client.receiver_thread.join(timeout=3)

        self.assertEqual(len(client.data), 1)
        self.assertEqual(client.data[0]["price"], 12.0)

    def test_invalid_json_is_skipped(self):
        """Malformed JSON events must be silently skipped."""
        from bf4py.live_data import BFStreamClient

        mock_connector = MagicMock()
        ev_bad  = MagicMock(event="message", data="not-valid-json")
        ev_good = MagicMock(event="message",
                            data=json.dumps({"price": 42.0}))

        mock_sse = MagicMock()
        mock_sse.events.return_value = iter([ev_bad, ev_good])
        mock_connector.stream_request.return_value = mock_sse

        client = BFStreamClient(
            function="price_information",
            params={"isin": BMW_ISIN, "mic": "XETR"},
            callback=None,
            connector=mock_connector,
            cache_data=True,
        )
        client.open_stream()
        client.receiver_thread.join(timeout=3)

        # Only the valid event should be stored
        self.assertEqual(len(client.data), 1)
        self.assertEqual(client.data[0]["price"], 42.0)

    def test_non_message_events_ignored(self):
        """Events that are not of type 'message' must be ignored."""
        from bf4py.live_data import BFStreamClient

        mock_connector = MagicMock()
        ev_heartbeat = MagicMock(event="heartbeat", data="")
        ev_message   = MagicMock(event="message",
                                 data=json.dumps({"price": 5.0}))

        mock_sse = MagicMock()
        mock_sse.events.return_value = iter([ev_heartbeat, ev_message])
        mock_connector.stream_request.return_value = mock_sse

        client = BFStreamClient(
            function="price_information",
            params={"isin": BMW_ISIN, "mic": "XETR"},
            callback=None,
            connector=mock_connector,
            cache_data=True,
        )
        client.open_stream()
        client.receiver_thread.join(timeout=3)

        self.assertEqual(len(client.data), 1)

    def test_close_stops_thread(self):
        """close() must set active=False and clear receiver_thread."""
        from bf4py.live_data import BFStreamClient

        mock_connector = MagicMock()
        mock_sse = MagicMock()
        mock_sse.events.return_value = iter([])
        mock_connector.stream_request.return_value = mock_sse

        client = BFStreamClient(
            function="price_information",
            params={"isin": BMW_ISIN, "mic": "XETR"},
            callback=None,
            connector=mock_connector,
        )
        client.open_stream()
        client.receiver_thread.join(timeout=2)
        client.close()

        self.assertFalse(client.active)
        self.assertIsNone(client.receiver_thread)


# ===========================================================================
# 11. Integration tests (skipped unless BF4PY_INTEGRATION_TESTS=1)
# ===========================================================================

@skip_integration
class TestIntegration(unittest.TestCase):
    """
    Integration tests that make real HTTP requests to the boerse-frankfurt.de API.
    These tests require a working internet connection and are disabled by default.

    Enable with: BF4PY_INTEGRATION_TESTS=1 python -m pytest unit_tests.py -v -k Integration
    """

    @classmethod
    def setUpClass(cls):
        from bf4py import BF4Py
        cls.bf = BF4Py(default_isin=BMW_ISIN)

    # --- Connector -------------------------------------------------

    def test_connector_salt_extracted(self):
        """Connector must successfully extract a non-empty salt from boerse-frankfurt.de."""
        self.assertIsNotNone(self.bf.connector.salt)
        self.assertGreater(len(self.bf.connector.salt), 0)

    # --- General ---------------------------------------------------

    def test_eod_data_returns_list(self):
        min_date = date.today() - timedelta(days=30)
        result = self.bf.general.eod_data(min_date)
        self.assertIsInstance(result, list)

    def test_eod_data_ohlc_keys(self):
        min_date = date.today() - timedelta(days=10)
        result = self.bf.general.eod_data(min_date)
        if result:
            keys = result[0].keys()
            for k in ("open", "high", "low", "close"):
                self.assertIn(k, keys)

    def test_data_sheet_header_has_isin(self):
        result = self.bf.general.data_sheet_header()
        self.assertIn("isin", result)
        self.assertEqual(result["isin"], BMW_ISIN)

    def test_instrument_information_not_empty(self):
        result = self.bf.general.instrument_information()
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_index_instruments_dax(self):
        result = self.bf.general.index_instruments()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("isin", result[0])
        self.assertIn("name", result[0])
        self.assertIn("wkn", result[0])

    # --- Equities --------------------------------------------------

    def test_equity_details_not_empty(self):
        result = self.bf.equities.equity_details()
        self.assertIsInstance(result, dict)

    def test_key_data_not_empty(self):
        result = self.bf.equities.key_data()
        self.assertIsInstance(result, dict)

    def test_related_indices_is_list(self):
        result = self.bf.equities.related_indices()
        self.assertIsInstance(result, (list, dict))

    # --- Company ---------------------------------------------------

    def test_about_not_empty(self):
        result = self.bf.company.about()
        self.assertIsInstance(result, dict)

    def test_contact_information_not_empty(self):
        result = self.bf.company.contact_information()
        self.assertIsInstance(result, dict)

    def test_company_information_not_empty(self):
        result = self.bf.company.company_information()
        self.assertIsInstance(result, dict)

    def test_upcoming_events_is_list_or_dict(self):
        result = self.bf.company.upcoming_events()
        self.assertIsInstance(result, (list, dict))

    # --- News ------------------------------------------------------

    def test_news_categories_returns_list(self):
        cats = self.bf.news.get_categories()
        self.assertIsInstance(cats, list)

    def test_news_by_category_returns_news(self):
        result = self.bf.news.news_by_category(news_type="COMPANY_NEWS", limit=5)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 5)

    def test_news_by_isin_returns_list(self):
        result = self.bf.news.news_by_isin(limit=5)
        self.assertIsInstance(result, list)

    # --- Derivatives -----------------------------------------------

    def test_search_criteria_returns_dict(self):
        result = self.bf.derivatives.search_criteria()
        self.assertIsInstance(result, dict)

    def test_trade_history_is_list(self):
        # Use a weekday from the recent past to maximize chance of data
        d = date.today() - timedelta(days=7)
        result = self.bf.derivatives.trade_history(d)
        self.assertIsInstance(result, list)

    # --- Bonds -----------------------------------------------------

    def test_bond_search_returns_list(self):
        from bf4py.bonds import Bonds
        bonds = Bonds(connector=self.bf.connector)
        params = Bonds.search_parameter_template()
        params["limit"] = 5
        result = bonds.search(params)
        self.assertIsInstance(result, list)

    # --- Live data (quick smoke-test) ------------------------------

    def test_live_price_stream_starts(self):
        """Live price stream must open without error and receive at least one update."""
        import time
        received = []
        client = self.bf.live_data.price_information(
            callback=received.append, cache_data=True
        )
        client.open_stream()
        time.sleep(5)
        client.close()
        self.assertGreater(len(received), 0,
                           "No live price data received in 5 seconds")


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)

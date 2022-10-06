import logging
import numpy as np
import requests
import pandas as pd

from typing import List, Tuple
from bs4 import BeautifulSoup
from provider_base import ProviderBase


LANGUAGE_CODE = "de_DE"

""" Definition of urls for login and making requests in loinc search website """
URL_AUTH = "https://loinc.org/wp-login.php?redirect_to=https%3A%2F%2Floinc.org%2Fsearch%2F&reauth=1"
URL_SEARCH = "https://loinc.org/search/?t=1&s={search_term}&l=" + LANGUAGE_CODE

""" Definition of possible URL responses while loinc search and login process """
RESPONSE_NO_ENTRIES = "Keine passenden Einträge gefunden"
RESPONSE_LOGIN = "Log In ‹ LOINC — WordPress"

logger = logging.getLogger(__name__)


class LoincWebManager:
    """
    connector for LOINC web search http https://loinc.org/search/ handling session
    """

    def __init__(self, credentials: dict = {}) -> None:
        self.credentials = credentials
        self.session = None
        self.connected = self.__start_session()

    def __start_session(self):
        """ starting web session with loinc web server """
        with requests.Session() as s:
            # set session object
            self.session = s
            post = s.post(URL_AUTH, data=self.credentials)
            # check if url can be reached
            if not post.ok:
                logger.info("connection has not been established")
                return False
            # send empty request to check the login
            soup = self.perform_search()
            # check if loggin was successful
            if soup.find("title").text == RESPONSE_LOGIN:
                print(soup.find("title").text)
                logger.info("login was not successful, please try again")
                return False
            # return successfully established session object
            return True

    def perform_search(self, term: list= []):
        """ performing term request against loinc weg server """
        if len(term) != 0:
            term = self.get_search_syntax_string(term)
        else:
            term = "test"
        r = self.session.get(URL_SEARCH.format(search_term=term))
        soup = BeautifulSoup(r.content, "html.parser")
        # return first root parsed note for login checking
        if term == "test":
            return soup
        # perform parsing for results if real tokens are entered
                    # find results in response
        search_result = soup.find(id="results")
        # get table rows and parse table
        table_columns = self.parse_table_columns(search_result)
        table = self.parse_table_rows(search_result)
        # build dataframe and append to result
        if table[0][0] == RESPONSE_NO_ENTRIES:
            logger.info(RESPONSE_NO_ENTRIES)
            return None
        return self.build_dataframe(table, table_columns)

    def parse_table_columns(self, search_result=None):
        """
        parses columns from response
                Parameters:
                        search_result (result_set): resultset for parsing result table from loinc search
                Returns:
                        columns (list): list of table columns for result
        """
        column_spans = [x.find("span") for x in search_result.find("thead").find_all("th")]
        column_texts = [x.text for x in column_spans if x is not None]
        return column_texts

    def parse_table_rows(self, search_result=None):
        """
        parses rows from response
                Parameters:
                        search_result (result_set): resultset for parsing result table from loinc search
                Returns:
                        table (2dim numpyarray): table as two dim array from results
        """
        body = search_result.find("tbody")
        table_rows = body.findAll("tr")
        return np.array([np.array([x.text for x in row.findAll("td")]) for row in table_rows])

    def build_dataframe(self, table: np.array, columns: list = []):
        """
        converts 2dim array to dataframe with columns
                Parameters:
                        table (2dim numpyarray): resultset for parsing result table from loinc search
                        columns (list): list of table columns for result
                Returns:
                        df (pandas df): table as pandas dataframe with columns
        """
        return pd.DataFrame(table, columns=columns)

    def get_search_syntax_string(self, tokens: list = []):
        """
        adds syntax for LOINC search and gets search string 
        tokens are combined with OR and fuzzy searched with ~
        see https://loinc.org/kb/search/advanced-search-syntax/
                Parameters:
                        tokens (list): List of tokens
                Returns:
                        search string (str): String with search syntax
        """
        return '~ OR '.join(e for e in tokens) + '~'


class LoincProvider(ProviderBase):
    def __init__(self, config) -> None:
        super().__init__()
        self.config = config
        self.loinc_web_connector = None

        self.http_response_no_resultset = RESPONSE_NO_ENTRIES
        self.http_response_login_promt = RESPONSE_LOGIN

    def initialize(self) -> None:
        if not self.initialized:
            self.loinc_web_connector = LoincWebManager(credentials=self.config)
            logger.info("...connected to the loinc search API ...")

    def get_matches(
        self, term: List[str], score_threshold: float = 0.1,
    ) -> List[Tuple[str, str, float]]:
        """
        Generate tokens from term, references and headings

        Returns
        ---
            List[Tuple[str, str, float]]:   List of tuples
            (ID, Term, Score)
        """

        # result has more data field than framework can handel TODO speak with Alex about information loss?
        result = self.loinc_web_connector.perform_search(term=term)

        # calculation of levenstein distance?

        return []

lp = LoincProvider(config={"log": "ngiesa", "pwd": "napkon123@"})
lp.initialize()
lp.get_matches(term=["Blutdruck", "systolisch"])
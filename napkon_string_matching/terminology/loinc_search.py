import logging
import yaml

import numpy as np
import pandas as pd
import requests

from nltk.corpus import stopwords
from bs4 import BeautifulSoup

LANGUAGE_CODE = "de_DE"

URL_AUTH = "https://loinc.org/wp-login.php?redirect_to=https%3A%2F%2Floinc.org%2Fsearch%2F&reauth=1"
URL_SEARCH = "https://loinc.org/search/?t=1&s={search_term}&l=" + LANGUAGE_CODE

RESPONSE_NO_ENTRIES = "Keine passenden Einträge gefunden"
RESPONSE_LOGIN = "Log In ‹ LOINC — WordPress"

STOP_WORDS = set(stopwords.words('german'))

EXAMPLEOUTCOME_ITEMS = [
    """Dialyse:""",
    """Invasiver Beatmung:""",
    """Sauerstoff:""",
    """Trachealkanüle:""",
    """Respiratorisches Outcome (Sauerstoff-Therapie):"""]

EXAMPLE_QUESTIONS = [
    """Wurde der Barthel-Index vor der Entlassung durchgeführt?""",
    """Fatigue Screening durchgeführt? Datum der Durchführung""",
    """Wurde der "PROMIS Dyspnoe-Funktionseinschränkungen" durchgeführt?"""]

logger = logging.getLogger(__name__)


def remove_non_alphanumerics(token: str):
    """
    removes all non alphanumerics in token
            Parameters:
                    token (str): The input char sequence
            Returns:
                    token (str): Same token without special chars
    """
    return ''.join(e for e in token if e.isalnum())


def remove_stop_words(tokens: list = []):
    """
    removes stop words from tokenized list
            Parameters:
                    tokens (list): List of tokens
            Returns:
                    tokens (list): List of tokens without stop words
    """
    return [t for t in tokens if t.lower() not in STOP_WORDS]


def get_search_syntax_string(tokens: list = []):
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


def get_auth_payload(user_name: str, password: str):
    """
    creates payload element as dict from credentials.
            Parameters:
                    user_name (str): The user name for search.loinc.org
                    password (str): The password for search.loinc.org
            Returns:
                    payload (dict): A dict of username and password with website spedific ids
    """
    return {"log": user_name, "pwd": password}


def ask_for_credentials():
    """
    asks users to provide credentials as inputs
            Parameters: -
            Returns:
                    payload (dict): A dict of username and password with website spedific ids
    """
    user_name = input("Please enter your user name for loinc.search: ")
    password = input("Please enter your password for loinc.search: ")
    return get_auth_payload(user_name=user_name, password=password)


def parse_table_columns(search_result=None):
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


def parse_table_rows(search_result=None):
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


def build_dataframe(table: np.array, columns: list = []):
    """
    converts 2dim array to dataframe with columns
            Parameters:
                    table (2dim numpyarray): resultset for parsing result table from loinc search
                    columns (list): list of table columns for result
            Returns:
                    df (pandas df): table as pandas dataframe with columns
    """
    return pd.DataFrame(table, columns=columns)


def start_search_session(search_terms: list = []):
    """
    starts and configures session and executes parsing functions
            Parameters:
                    search_terms (list[str]): list of search terms that must be queries for loinc
            Returns:
                    result_dfs (list[df]): list of dataframes that are returned per loinc search
    """
    result_dfs = []
    with requests.Session() as s:
        # ask user for credentials
        payload = ask_for_credentials()
        # authenticate on website
        p = s.post(URL_AUTH, data=payload)
        # check if connection was successful
        if not p.ok:
            logger.info("connection has not been established")
            return None
        # execute search calls
        for term in search_terms:
            r = s.get(URL_SEARCH.format(search_term=term))
            # parse content and search for result section
            soup = BeautifulSoup(r.content, "html.parser")
            # check if loggin was successful
            if soup.find("title").text == RESPONSE_LOGIN:
                logger.info("login was not successful, please try again")
                return None
            # find results in response
            search_result = soup.find(id="results")
            # get table rows and parse table
            table_columns = parse_table_columns(search_result)
            table = parse_table_rows(search_result)
            # build dataframe and append to result
            if table[0][0] == RESPONSE_NO_ENTRIES:
                logger.info(RESPONSE_NO_ENTRIES)
                return None
            result_dfs.append(build_dataframe(table, table_columns))
    return result_dfs


if __name__ == "__main__":
    search_strings = []
    # example call
    for item in EXAMPLEOUTCOME_ITEMS:
        # tokenize according to space
        tokens = item.split(" ")
        # make tokens alphanumeric
        tokens = [remove_non_alphanumerics(t) for t in tokens]
        # remove stop words
        tokens = remove_stop_words(tokens=tokens)
        # create search syntax string and append to list
        search_strings.append(get_search_syntax_string(tokens=tokens))
    # starting session and search getting one df per search
    search_results = start_search_session(search_strings)

# TODO maybe use this in base class for mesh and loinc?
def __read_config_yml(file_path): 
    """ reading yml config file """
    with open(file_path, 'r') as f:
        return yaml.load(f)

# TODO maybe use this in base class for mesh and loinc?
class Credentials():
    """ credential instance holding user name and password """
    def __init__(self, user, passwd) -> None:
        self.user = user
        self.passwd = passwd

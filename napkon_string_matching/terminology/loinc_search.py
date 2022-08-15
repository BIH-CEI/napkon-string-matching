# import REST and parsing modules
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

URL_AUTH = "https://loinc.org/wp-login.php?redirect_to=https%3A%2F%2Floinc.org%2Fsearch%2F&reauth=1"
URL_SEARCH = "https://loinc.org/search/?t=1&s={search_term}&l=de_DE"

RESPONSE_NO_ENTRIES = "Keine passenden Einträge gefunden"
RESPONSE_LOGIN = "Log In ‹ LOINC — WordPress"


def get_auth_payload(user_name: str, password: str):
    """
    creates payload element as dict from credentials.
            Parameters:
                    user_name (str): The user name for search.loinc.org
                    password (str): The password for search.loinc.org
            Returns:
                    payload (dict): A dict of username and password with website spedific ids
            Author: giesan
    """
    return {"log": user_name, "pwd": password}


def ask_for_credentials():
    """
    asks users to provide credentials as inputs
            Parameters: -
            Returns:
                    payload (dict): A dict of username and password with website spedific ids
            Author: giesan
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
            Author: giesan
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
            Author: giesan
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
            Author: giesan
    """
    return pd.DataFrame(table, columns=columns)


def start_search_session(search_terms: list = []):
    """
    starts and configures session and executes parsing functions
            Parameters:
                    search_terms (list[str]): list of search terms that must be queries for loinc
            Returns:
                    result_dfs (list[df]): list of dataframes that are returned per loinc search
    Author: giesan
    """
    result_dfs = []
    with requests.Session() as s:
        # ask user for credentials
        payload = ask_for_credentials()
        # authenticate on website
        p = s.post(URL_AUTH, data=payload)
        # check if connection was successful
        if not p.ok:
            print("connection has not been established")
            return None
        # execute search calls
        for term in search_terms:
            r = s.get(URL_SEARCH.format(search_term=term))
            # parse content and search for result section
            soup = BeautifulSoup(r.content, "html.parser")
            # check if loggin was successful
            if soup.find("title").text == RESPONSE_LOGIN:
                print("login was not successful, please try again")
                return None
            # find results in response
            search_result = soup.find(id="results")
            # get table rows and parse table
            table_columns = parse_table_columns(search_result)
            table = parse_table_rows(search_result)
            # build dataframe and append to result
            if table[0][0] == RESPONSE_NO_ENTRIES:
                print(RESPONSE_NO_ENTRIES)
                return None
            result_dfs.append(build_dataframe(table, table_columns))
    return result_dfs


if __name__ == "__main__":
    # example call
    start_search_session(["systolischer Blutdruck", "COVID"])

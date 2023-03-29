# pylint: disable=too-many-locals
"""
Module to get data from wikidata about Welsh castles.
"""
from pprint import pprint
import random
import os
import sqlite3
from typing import Dict, List
import requests

def get_query(filename: str = "query.txt", encoding: str = "utf-8") -> str:
    """Gets a SPARQL query from a given file

    Args:
        filename (str, optional): File to read the query from. Defaults to "query.txt".
        encoding (str, optional): Encoding of the file. Defaults to "utf-8".

    Returns:
        str: The SPARQL query
    """
    with open(filename, "r", encoding = encoding) as file:
        return "".join(file.readlines())

def get_wikidata_from_sparql_as_json(query: str):
    """Gets data from wikidata via the use of a SPARQL query

    Args:
        query (str): A SPARQL query

    Returns:
        any: a JSON response from wikidata
    """
    url: str = "https://query.wikidata.org/sparql"

    params: Dict[str, str] = {
        "format": "json",
        "query": query
        }

    response = requests.get(url, params = params)

    return response.json()

def get_castles_from_json(json_data) -> list:
    """Create a list of valid castles from json data

    Args:
        json_data: JSON data from wikidata containing castle information

    Returns:
        list: A list of castles containing attributes for name, location and image
    """
    castles: List = []

    for item in json_data["results"]["bindings"]:
        castle = {}

        castle["name"] = item["itemLabel"]["value"]
        castle["location"] = item["locationLabel"]["value"]

        if "image" in item:
            castle["image"] = item["image"]["value"]
        else:
            castle["image"] = None

        castles.append(castle)

    return castles

def download_wikimedia_commons_image(wikimedia_commons_url: str) -> None:
    """Downloads an image at a specified wikimedia commons url

    Args:
        wikidata_url (str): An image on the wikimedia commons site
    """
    filename: str = wikimedia_commons_url.split("/")[-1]

    headers: Dict[str, str] = {
        'User-Agent': 'Welsh Castles User Agent'
    }

    req = requests.get(wikimedia_commons_url, headers=headers)

    with open(filename, "wb") as file:
        file.write(req.content)

def is_integer(val: str) -> bool:
    """Checks whether a given string can be represented as an int

    Args:
        val (str): A value to check

    Returns:
        bool: True if int else false
    """
    try:
        int(val)
        return True
    except ValueError:
        return False

def get_integer_input_in_range(
        prompt: str = "Enter an integer: ",
        min_val: int = -1000,
        max_val: int = 1000
    ) -> int:
    """Gets an integer from user in given range

    Args:
        prompt (str, optional): A prompt to show the user. Defaults to "Enter an integer: ".
        min_val (int, optional): minimum value. Defaults to -1000.
        max_val (int, optional): maximum value. Defaults to 1000.

    Returns:
        int: An input from the user
    """

    inp: str = ""

    while not is_integer(inp):
        inp = input(prompt)

        int_val: int = -1001

        if is_integer(inp):
            int_val = int(inp)

            if int_val < min_val or int_val > max_val:
                print(f"{int_val} not in range {min_val} - {max_val}")
                inp = ""

    return int_val

def get_option_from_list(list_of_options: list) -> int:
    """Gets an index from a list by user input

    Args:
        list_of_options (list): List of choices

    Returns:
        int: index of choice selected by user
    """
    for index, value in enumerate(list_of_options, start = 1):
        print(f"{index}.) {value}")

    value: int = get_integer_input_in_range(
        "Select an option by choosing a number.\n",
        1,
        len(list_of_options)
    )

    return value - 1

def check_if_sqlite_file_exists(filename: str = "table.db") -> bool:
    """Checks if a sqlite file exists

    Args:
        filename (str, optional): Name of the file. Defaults to "table.db".

    Returns:
        bool: True if file exists else false
    """
    return os.path.exists(filename)

def create_sqlite_file(filename: str = "table.db") -> None:
    """Creates a file for the database

    Args:
        filename (str, optional): The name of the file to create. Defaults to "table.db".
    """
    with open(filename, "x", encoding = "utf-8") as _:
        return

def execute_sqlite_query(cursor: sqlite3.Cursor, query: str, parameters: tuple = tuple()) -> None:
    """Executes a sqlite query

    Args:
        cursor (sqlite3.Cursor): The cursor to use
        query (str): The query to run
    """

    if parameters:
        print(query)
        print(parameters)
        cursor.execute(query, parameters)
        return

    cursor.execute(query)

def main() -> None:
    """Main method
    """
    query: str = get_query("wikidata_query.rq")

    data = get_wikidata_from_sparql_as_json(query)

    castles: List = get_castles_from_json(data)

    options: List[str] = [
        "Download a Random Castle",
        "Populate SQLite Table"
    ]

    option_selected: str = get_option_from_list(options)

    if option_selected == 0:
        castles_with_images: List = [castle for castle in castles if castle["image"] is not None]

        random_castle = random.choice(castles_with_images)

        random_castle_image: str = random_castle["image"]

        pprint(random_castle)

        download_wikimedia_commons_image(random_castle_image)
    if option_selected == 1:
        file: str = "castles.db"

        if not check_if_sqlite_file_exists(file):
            create_sqlite_file(file)

        create_table_query = get_query("createTable.sql")

        con: sqlite3.Connection = sqlite3.connect(file)
        cur: sqlite3.Cursor = con.cursor()

        execute_sqlite_query(cur, create_table_query)

        delete_data_query: str = get_query("deleteData.sql")

        execute_sqlite_query(cur, delete_data_query)

        insert_castle_queries: Dict[str, str] = {
            "withoutImage": get_query("insertCastleWithoutImage.sql"),
            "withImage": get_query("insertCastleImage.sql")
        }

        for castle in castles:

            castle_tuple: tuple = tuple()
            insert_castle_query: str = ""

            if castle["image"]:
                castle_tuple = (castle["name"], castle["location"], castle["image"])
                insert_castle_query = insert_castle_queries["withImage"]
            else:
                castle_tuple = (castle["name"], castle["location"])
                insert_castle_query = insert_castle_queries["withoutImage"]

            execute_sqlite_query(cur, insert_castle_query, castle_tuple)

        cur.close()
        con.commit()
        con.close()

if __name__ == '__main__':
    main()

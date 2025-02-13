#!/usr/bin/python3
"""hacked together script to download letterboxd data"""

import csv
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class Entry:
    """Entry class"""

    def __init__(self, source):
        self.source = source
        self.length = self.get_length(source)

    def get_page(self, page):
        """get page"""
        result = requests.get(page, timeout=20.0)
        # make sure page is reachable
        if result.status_code == 200:
            return result.content
        message = (
            "Failed to get page, "
            f"webserver returned code {result.status_code}"
            f"for page {self.source}"
        )
        print(message)
        return ""

    def soupify(self, page):
        """transform page into soup object"""
        return BeautifulSoup(self.get_page(page), features="html5lib")

    def get_film_link(self, page):
        """get movie url"""
        return (
            "https://letterboxd.com/"
            + self.soupify(page).select('a[href^="/film/"]')[0]["href"]
        )

    def get_length(self, page):
        """get movie lenght"""
        page = self.soupify(self.get_film_link(page))
        paragraph = page.select('p[class^="text-link text-footer"]')[0]
        movie_length = paragraph.get_text(strip=True).partition("\xa0")[0]
        return movie_length


def mv_str(inp: int):
    """string manipulation"""
    mv = "movies"
    if inp == 1:
        mv = mv[:-1]
    return mv


def get_movie_length(url):
    """get movie length"""
    return Entry(url).length


# get data from csv
with open("diary.csv", mode="r") as ifile:
    raw_data = {rows[3]: rows[7] for rows in csv.reader(ifile)}
    raw_data.pop("Letterboxd URI")

QUERIED = 0

# check for pickled data
try:
    with open("database.pkl", mode="rb") as pfile:
        database = pickle.load(pfile)
    QUERIED = len(database)
    print(f"Found pickled data, {QUERIED} {mv_str(QUERIED)} in the database.")
except IOError:
    print("No pickled data found.")
    database = {}

totalmov = len(raw_data)
to_query = totalmov - QUERIED

print("Querying letterboxd.com for movie lengths.")

# get missing data from website
try:
    with ThreadPoolExecutor(max_workers=8) as executor:
        mapping = {}
        futures = []
        sleep(5)
        for movie in raw_data:
            if movie not in database:
                # get length:
                future = executor.submit(get_movie_length, movie)
                mapping[future] = movie
                futures.append(future)
        with tqdm(
            desc="Received",
            initial=QUERIED,
            total=totalmov,
            unit="movies",
        ) as totalbar:
            for future in as_completed(futures):
                movie = mapping[future]
                length = int(future.result())
                totalbar.update(1)
                if isinstance(length, int):
                    database[movie] = {
                        "length": length,
                        "date": raw_data[movie],
                    }
                else:
                    print(f"Error getting length of {future.exception()}")
                    #  database.pop(movie)
except BaseException as err:
    print(f"Error during data gathering for movie {movie}. Error = {err}")
finally:
    # put data into pickle
    with open("database.pkl", mode="wb") as pfile:
        pickle.dump(database, pfile)

print(f"{to_query} new {mv_str(to_query)} found.")
print(f"{totalmov} {mv_str(totalmov)} in the diary.")

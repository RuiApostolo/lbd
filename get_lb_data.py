#!/usr/bin/python3
import csv
import pickle
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


class entry(object):
    def __init__(self, source):
        self.source = source
        self.length = self.get_length(source)

    def get_page(self, page):
        """get page"""
        result = requests.get(page)
        # make sure page is reachable
        if result.status_code == 200:
            return result.content
        else:
            message = ("Failed to get page, "
                       f"webserver returned code {result.status_code}"
                       f"for page {self.source}")
            print(message)

    def soupify(self, page):
        """transform page into soup object"""
        return BeautifulSoup(self.get_page(page), features="html5lib")

    def get_film_link(self, page):
        """get movie url"""
        return 'https://letterboxd.com/' + self.soupify(
                page).select('a[href^="/film/"]')[0]['href']

    def get_length(self, page):
        """get movie lenght"""
        page = self.soupify(self.get_film_link(page))
        paragraph = page.select('p[class^="text-link text-footer"]')[0]
        length = paragraph.get_text(strip=True).partition("\xa0")[0]
        return length


def get_movie_length(url):
    return entry(url).length


# get data from csv
with open('diary.csv', mode='r') as ifile:
    raw_data = {rows[3]: rows[7] for rows in csv.reader(ifile)}
    raw_data.pop('Letterboxd URI')

# check for pickled data
try:
    with open('database.pkl', mode='rb') as pfile:
        database = pickle.load(pfile)
    print('Found pickled data.')
except IOError:
    print('No pickled data found.')
    database = {}

# get missing data from website
try:
    with ThreadPoolExecutor() as executor:
        mapping = {}
        futures = []
        for movie in raw_data:
            if movie not in database:
                future = executor.submit(get_movie_length, movie)  # get length
                mapping[future] = movie
                futures.append(future)
        for future in as_completed(futures):
            movie = mapping[future]
            length = int(future.result())
            if type(length) == int:
                database[movie] = {'length': length, 'date': raw_data[movie]}
            else:
                print(f"Error getting length of {future.exception()}")
                #  database.pop(movie)
except BaseException as err:
    print(f"Error during data gathering for movie {movie}. Error = {err}")
finally:
    # put data into pickle
    with open('database.pkl', mode='wb') as pfile:
        pickle.dump(database, pfile)

print(f"{len(database)} movies found")

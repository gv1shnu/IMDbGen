import time
from urllib.parse import urlparse
import imdb
import math
import os
import random
import requests
import csv
from bs4 import BeautifulSoup
import pickle


def valid(_url):
    try:
        result = urlparse(_url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


class IMDbGen:
    def __init__(self):
        self.hashmap = None
        self.hm_pickle = "db/hashmap.pickle"
        self.homepage = "https://www.imdb.com/"
        if not os.path.exists('db'):
            os.mkdir('db')
        self.types = ["tv_series", "feature", "video_game"]
        self.genres = ["Action", "Adventure", "Animation", "Biography", "Comedy",
                       "Crime", "Documentary", "Drama", "Family", "Fantasy",
                       "Film-Noir", "Game-Show", "History", "Horror", "Music", "Musical",
                       "Mystery", "News", "Reality-TV", "Romance", "Sci-Fi",
                       "Short", "Sport", "Talk-Show", "Thriller", "War", "Western"
                       ]
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        ]
        self.csv_file = 'db/imdb_plot.csv'
        self.field_names = ['imdbID', 'title', 'genres', 'kind', 'plot']
        self.imdb = imdb
        self.load_hashmap()

    def get_header(self) -> dict:
        tmp = random.choice(self.user_agents)
        return {'User-Agent': tmp}

    def getSoup(self, url: str):
        header = self.get_header()
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        return None

    def get_hashmap(self):
        with open(self.hm_pickle, "rb") as file:
            return pickle.load(file)

    def load_hashmap(self):
        if not os.path.exists(self.hm_pickle):
            with open(self.hm_pickle, "wb") as file:
                pickle.dump({}, file)
        self.hashmap = self.get_hashmap()

    def get_title_count(self, _url: str) -> int:
        soup = self.getSoup(_url)
        total_div = soup.find('div', class_="desc")
        h = total_div.span.text
        if "titles." not in h:
            return 0
        r = h.split(' ')
        x = r.index("titles.") - 1
        s = int(r[x].replace(',', ''))
        return s

    def get_page_count(self, _url: str) -> int:
        return math.ceil(self.get_title_count(_url) / 50)  # max. 50 titles per page

    def get_details(self, _id):
        ia = self.imdb.IMDb()
        series = ia.get_movie(_id).data
        title = series.get('title')
        genres = ",".join(series.get('genres'))
        kind = series.get('kind')
        imdbID = series.get('imdbID')
        plot = series.get('plot')
        if plot:
            plot = ";".join(series.get('plot'))
        return {'title': title, 'imdbID': imdbID, 'genres': genres,
                'kind': kind, 'plot': plot}

    def get_all_ids_from_imdb(self):
        limit = 0
        random.shuffle(self.genres)
        for _type in self.types:
            for _genre in self.genres:
                url = f"{self.homepage}search/title/?title_type={_type}&genres={_genre}&sort=alpha,asc"
                if valid(url):
                    total_pages = self.get_page_count(url)
                    self.load_hashmap()
                    print(_type, _genre)
                    for m, cnt in enumerate(range(1, total_pages + 1)):
                        url_ = url + f"&start={(1 + 50 * (cnt - 1))}"
                        try:
                            _soup = self.getSoup(url_)
                            hashmap = {}
                            if _soup:
                                page_list = _soup.find('div', class_="lister-list")
                                adv_items = page_list.find_all('div', class_="lister-item mode-advanced")
                                for adv_item in adv_items:
                                    content_item = adv_item.find('div', class_="lister-item-content")
                                    header_item = content_item.find('h3', class_='lister-item-header')
                                    tag = header_item.find('a')['href'][1:]
                                    title_id = str(tag.split('/')[1])[2:]
                                    if not self.hashmap.get(title_id):
                                        hashmap[title_id] = True
                                        row = {}
                                        details = self.get_details(title_id)
                                        for item in self.field_names:
                                            row[item] = details[item]
                                        with open(self.csv_file, 'a', newline='') as file:
                                            writer = csv.DictWriter(file, fieldnames=self.field_names)
                                            if file.tell() == 0:
                                                writer.writeheader()
                                            writer.writerows([row])
                                time.sleep(3)
                                with open(self.hm_pickle, "wb") as jkl:
                                    pickle.dump(hashmap, jkl)
                            print(f"{m + 1}/{total_pages}")
                        except Exception as e:
                            print(f"Exception@Pg{m + 1}: {e}")
                            limit += 1
                            if limit > 10:
                                return
                    print()
                else:
                    print(f"Invalid URL: {_type}-{_genre}")
                    continue


if __name__ == '__main__':
    imdbgen = IMDbGen()

    imdbgen.get_all_ids_from_imdb()

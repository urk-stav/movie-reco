import os
import re
import sys
import requests
import _pickle as pickle
from bs4 import BeautifulSoup
from utils.utils import _requests, _print, _wrn_print, _err_print


URL = 'https://en.wikipedia.org'
COUNTRIES = ['American', 'Argentine', 'Australian', 'Brazilian',
             'British', 'Chinese', 'Czech', 'Danish', 'Dutch',
             'French', 'German', 'Bollywood', 'Iranian',
             'Israeli', 'Italian', 'South_Korean', 'Mexican',
             'Soviet', 'Spanish', 'Swedish', 'Tamil-language']
YEAR_CUTOFF = 1980


def _get_yearly_film_url_for_country(c):
    r = _requests(f'{URL}/wiki/{c}', request_store)
    soup = BeautifulSoup(r.content, 'html.parser')
    hrefs = soup.find_all('a')
    country = c.split('_')[2]
    list_of_country = set()
    for b in hrefs:
        if 'href' in b.attrs:
            href = b.attrs['href']
            txt = f'/List_of_{country}_films_of_'
            if txt in href:
                year = re.findall('\d{4}', href)[0]
                if int(year) > YEAR_CUTOFF:
                    list_of_country.update({href})

    return list_of_country


if __name__ == '__main__':
    # load request store or create one
    if not os.path.exists('data/request_store.pkl'):
        request_store = {}
    else:
        with open('data/request_store.pkl', 'rb') as f:
            request_store = pickle.load(f)
        _print('Loaded request store')
    # scrape
    print('starting scraping ...')
    r = _requests(f'{URL}/wiki/Lists_of_films', request_store)
    if r.status_code != 200:
        _err_print(f'Failed {URL}/wiki/Lists_of_films')
        sys.exit()
    # find the urls for films by country
    soup = BeautifulSoup(r.content, 'html.parser')
    _temp = soup.find(id="By_country_of_origin")
    found_list = False
    while not found_list:
        _temp = _temp.findNext()
        if _temp.name == 'ul':
            found_list = True
    if not found_list:
        _err_print('Film list by country not found')
        sys.exit()
    hrefs = _temp.find_all('a')
    lists_by_country = set()
    for b in hrefs:
        href = b.attrs['href']
        m = re.findall('Lists_of_[\a-zA-z]+_films', href)
        if m:
            lists_by_country.update({m[0]})
    manual_country_list = [f'Lists_of_{c}_films' for c in COUNTRIES]
    common_country_list = set(manual_country_list).intersection(lists_by_country)
    # film list by country
    print('Getting films for ...')
    for c in common_country_list:
        print(c)
        print('=' * len(c))
        list_of_country_by_year = _get_yearly_film_url_for_country(c)
        for url in list_of_country_by_year:
            r = _requests(f'{URL}{url}', request_store)

    
    # write to request store
    with open('data/request_store.pkl', 'wb') as f:
        pickle.dump(request_store, f)
    _print('Written to request store')

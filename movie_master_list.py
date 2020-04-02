import os
import re
import sys
import json
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
MONTHS = \
['JANUARY',
 'FEBRUARY',
 'MARCH',
 'APRIL',
 'MAY',
 'JUNE',
 'JULY',
 'AUGUST',
 'SEPTEMBER',
 'OCTOBER',
 'NOVEMBER',
 'DECEMBER']


def _get_yearly_film_url_for_country(c):
    """urls for films by year for country c"""
    r = _requests(f'{URL}/wiki/{c}', request_store)
    soup = BeautifulSoup(r.content, 'html.parser')
    hrefs = soup.find_all('a')
    list_of_country = set()
    country = '_'.join(c.split('_')[2:-1])
    txt = f'/List_of_{country}_films_of_'
    for b in hrefs:
        if 'href' in b.attrs:
            href = b.attrs['href']
            if txt in href:
                year = re.findall('\d{4}', href)[0]
                if int(year) > YEAR_CUTOFF:
                    list_of_country.update({href})

    return list_of_country


def _get_movie_info(r):
    """movie info from wiki table for a country for a year"""
    soup = BeautifulSoup(r.content, 'html.parser')
    tables = soup.findAll("table", {"class": 'wikitable'})
    movie_infos = []
    n_films = 0
    columns = []
    for table in tables:
        if 'title' in table.find_all('th')[0].text.strip().lower() or \
        'title' in table.find_all('th')[1].text.strip().lower():
            columns = [th.text.strip() for th in table.find_all('th')]
        elif table.find_all('td') and \
           ('title' in table.find_all('td')[0].text.strip().lower() or \
           'title' in table.find_all('td')[1].text.strip().lower()):
            for td in table.find_all('td'):
                if td.find('a'):
                    break
                columns.append(td.text.strip())
        if columns:
            columns = [c for c in columns if c not in MONTHS]
            for i, c in enumerate(columns):
                if 'title' in c.lower():
                    title_ix = i
                    break
            trs = table.find_all('tr')
            for tr in trs:
                tds = [td for td in tr.find_all('td')]
                texts = [td.text.strip() for td in tds]
                if len(tds) == len(columns) or len(tds) == len(columns) - 1:
                    info  = dict(zip(columns[:len(tds)], texts))
                    hrefs = tds[title_ix].find_all('a')
                    if hrefs:
                        info['url'] = hrefs[0]['href']
                        movie_infos.append(info)
                        n_films += 1
        else:
            _err_print('Film table not found')

    if n_films:
        print(f'{n_films} films found!')
    else:
        _err_print(f'No films found')
    return movie_infos


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
    all_movie_info = {}
    for c in common_country_list:
        print(c)
        print('=' * len(c))
        all_movie_info[c] = {}
        list_of_country_by_year = _get_yearly_film_url_for_country(c)
        for url in list_of_country_by_year:
            r = _requests(f'{URL}{url}', request_store)
            movie_infos = _get_movie_info(r)
            if movie_infos:
                all_movie_info[c][url] = movie_infos

    # write out movie infos
    with open('data/wiki_movie_infos.json', 'w') as f:
        json.dump(all_movie_info, f)
    _print('Written movie infos')
    
    # write to request store
    with open('data/request_store.pkl', 'wb') as f:
        pickle.dump(request_store, f)
    _print('Written to request store')

# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 04:27:02 2020

@author: manickavasagam.s
"""


import os
import json
import _pickle as pickle
from bs4 import BeautifulSoup, NavigableString
from utils import _requests, _print, _wrn_print, _err_print

URL = 'https://en.wikipedia.org'

def _check_if_reference_anchor(tag):
    """ Checks if a tag is a reference tag """
    result = False
    if tag.parent.has_attr('class'):
        if tag.parent['class']==['reference']:
            result = True
    return result
        
def _get_infobox_data(r):
    """Scrapes the infobox table contents from the wiki page"""
    soup = BeautifulSoup(r.content, 'html.parser')
    infobox_soup = soup.find("table", {"class":"infobox vevent"})
    if infobox_soup is None:
        return -1
    infobox = {}
    rows = infobox_soup.find_all('tr')
    
    for i, row in enumerate(rows):
        if i == 0:
            # Title always appears at the top of the table
            infobox['title'] = row.find('th').text
        elif row.find('a',{'class':'image'}):
            # Image, if present, follow the title
            try:
                infobox['image'] = {}
                infobox['image']['image_url'] = row.find('td').a['href']
                try:
                    infobox['image']['image_desc'] = row.find('td').a['title']
                except:
                    infobox['image']['image_desc'] = ""
            except:
                continue
        elif not row.find('th'):
            # Skip if no header present 
            continue
        elif row.find('th').get_text(" ") == "Release date":
            # Special case for date due to the formatting
            if row.find('span'):
                t = row.find('span')
            else:
                t = row.find('td')
            infobox['Release date'] = (
                t.get_text()
                   .strip()
                   .replace('(','')
                   .replace(')','')
                   )
        elif row.find('th').get_text(" ") == "Running time":
            # Special case for Run time due to additional junk 
            try:
                infobox['Running time'] = (
                    row.find('li').get_text()
                    .strip()
                    .replace('\xa0', ' ')
                    )
            except:
                infobox['Running time'] = (
                    row.find('td').get_text()
                    .strip()
                    .replace('\xa0', ' ')
                    )
        else:
            list_of_values = []
            if not row.find('td'):
                continue
            for val in row.find('td'):
                # Iterate through table values
                if isinstance(val, NavigableString):
                    list_of_values.append(
                        {'value':val.string
                                    .strip()
                                    .replace('\xa0', ' ')
                                    })
                    continue
                if val.name == 'a':
                    list_of_values.append(
                        {'value': val.string,
                         'url': val['href']
                         })
                    continue
                if val.find('li'):
                    for li in val.find_all('li'):
                        if li.findChildren("a"):
                            if not _check_if_reference_anchor(li.a):
                                list_of_values.append(
                                    {'value': li.string,
                                     'url': li.a['href']
                                     })
                            else:
                                list_of_values.append(
                                    {'value': li.get_text()
                                     })
                        else:
                            list_of_values.append(
                                {'value': li.get_text()
                                 })
                elif val.find('a'):
                    if not _check_if_reference_anchor(val.find('a')):
                        list_of_values.append(
                            {'value': val.find('a')
                                         .string,
                             'url': val.find('a')['href']
                             })
                else:
                    list_of_values.append(
                        {'value':val.get_text()
                                    .strip()
                                    })
                    
            infobox[row.find('th').get_text(" ")] = list_of_values
    return infobox

if __name__ == '__main__':
    
    # load request store or create one
    if not os.path.exists('data/request_store.pkl'):
        request_store = {}
    else:
        with open('data/request_store.pkl', 'rb') as f:
            request_store = pickle.load(f)
        _print('Loaded request store')
    # load movie info json
    with open('data/wiki_movie_infos.json', 'rb') as f:
        movie_list = json.load(f)
    _print('Loaded movie info')
    movie_metadata = {}
    list_counter = 0
    md_counter = 0
    for country in movie_list:
        for country_year in movie_list[country]:
            for movie in movie_list[country][country_year]:
                list_counter = list_counter + 1
                print("Scrapping for {}".format(country_year))
                try:
                    wiki_url = URL+movie['url']
                except:
                    (
                        _wrn_print("URL not available for {}. Skipping.."
                                   .format(country_year))
                        )
                    continue
                r = _requests(wiki_url, request_store)
                if r is None:
                    _wrn_print("Skipping {}".format(wiki_url))
                    continue
                _temp_output = _get_infobox_data(r)
                if _temp_output != -1:
                    movie_metadata[wiki_url] = _temp_output
                md_counter = md_counter + 1
                if list_counter%100 == 0:
                    print(list_counter)
                    print(md_counter)
    
    with open('data/wiki_movie_metadata.json', 'w') as f:
        json.dump(movie_metadata, f)
    
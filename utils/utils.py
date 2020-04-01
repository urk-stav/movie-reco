import requests
from termcolor import colored


def _requests(url, request_store):
    """cache for requestes"""
    if url not in request_store:
        r = requests.get(url)
        if r.status_code == 200:
            request_store[url] = r
            _print(f'Stored in cache: {url}')
            return r
        else:
            _err_print('Request failed')
    else:
        _print(f'Found in request store: {url}')
        return request_store[url]


def _print(txt):
    print(colored(f'[{txt}]', 'green'))


def _err_print(txt):
    print(colored(f'[{txt}]', 'red'))


def _wrn_print(txt):
    print(colored(f'[{txt}]', 'yellow'))

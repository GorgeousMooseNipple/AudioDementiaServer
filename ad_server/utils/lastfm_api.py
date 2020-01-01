import requests
from ad_server.config import Config


BASE_URL = 'http://ws.audioscrobbler.com/2.0'
API_KEY = Config.LAST_FM_API_KEY


def search_on_lastfm(title, artist, searchfor='track'):
    if searchfor == 'track':
        method = 'track.getinfo'
    elif searchfor == 'album':
        method = 'album.getinfo'
    else:
        raise ValueError('searchfor must be either track or album')
    params = {
        'method': method,
        searchfor: title,
        'api_key': API_KEY,
        'artist': artist,
        'format': 'json'}

    response = requests.get(BASE_URL, params=params)
    if not response.ok:
        raise ConnectionError(f'Request (url {response.url}) for {title} has returned anything but 200 OK')

    jresponse = response.json()
    if 'error' in jresponse:
        raise ConnectionError(f'Request (url {response.url}) for {title} ended up with an error:\n{jresponse["error"]}')
    return jresponse.get('album')

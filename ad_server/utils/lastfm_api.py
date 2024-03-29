import requests
from flask import current_app


BASE_URL = 'http://ws.audioscrobbler.com/2.0'

searchable = {
    'album':
    {'method': 'album.getInfo', 'required': ('album', 'artist')},
    'track':
    {'method': 'track.getInfo', 'required': ('track', 'artist')},
    'artist':
    {'method': 'artist.getInfo', 'required': ('artist')}
}


def search_on_lastfm(searchfor='track', **kwargs):

    api_key = current_app.config.get('LAST_FM_API_KEY')

    if searchfor not in searchable:
        raise ValueError('searchfor must be either track or album')
    else:
        api_request = searchable[searchfor]

    params = {
        'method': api_request.get('method'),
        'api_key': api_key,
        'format': 'json'}

    for par in api_request['required']:
        if par not in kwargs:
            raise ValueError(
                f'Parameter {par} must be provided!'
                f'Required parameters: {api_request["required"]}'
            )
    params.update(kwargs)

    response = requests.get(BASE_URL, params=params)
    if not response.ok:
        raise ConnectionError(
            f'Request (url {response.url}) with parameters: {params} '
            'has returned anything but 200 OK'
        )

    jresponse = response.json()
    if 'error' in jresponse:
        raise ConnectionError(
            f'Request (url {response.url}) with parameters: {params} '
            f'ended up with an error:\n{jresponse["error"]}'
        )
    return jresponse.get(searchfor)

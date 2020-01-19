from flask import url_for
from ad_server.models import Genre, Album, Song, Artist
from mutagen.mp3 import EasyMP3
from ad_server import db
import pytest
import json
import os


def test_get_top_genres(test_client, fill_db):
    """
    Test getting list of top genres
    """

    response = test_client.get(url_for('media.top_genres'))

    assert response.status_code == 200

    genres = response.json.get('genres')

    # There is some genres returned
    assert len(genres) != 0

    # There is an id and a title for each genre
    for g in genres:
        assert g['id']
        assert g['title']


def test_request_without_required_parameter(test_client):
    """
    Tests sends request to the endpoint which requires parameters
    without those parameters.
    Tests if required_params decorator works properly.
    """

    url = url_for('media.playlist_songs')

    response = test_client.get(url)

    assert response.status_code == 400

    # Here parameter is present but it's type is wrong
    response = test_client.get(
        url,
        query_string={'id': 'notinteger'}
        )

    assert response.status_code == 400
    assert response.json.get('message') ==\
        'Parameter id of type int is required'


def test_get_songs_from_playlist(test_client, user_with_playlist, fill_db):
    """
    Test endpoint which must return list of songs for playlist.
    Requiers playlist id as a parameter.
    """
    user, _, _ = user_with_playlist
    playlist = user.playlists[0]

    params = {'id': playlist.id, 'per_page': playlist.songs.count()}

    response = test_client.get(
        url_for('media.playlist_songs'), query_string=params)

    assert response.status_code == 200

    songs = response.json.get('songs')
    assert songs
    # All songs from db should be in this playlist
    assert len(songs) == len(list(playlist.songs))


def test_get_songs_from_genre(test_client, fill_db):
    """
    Tests endpoint which returns all song for genre.
    """

    genre = Genre.query.first()
    genre_songs_count = sum([len(list(a.songs)) for a in genre.albums])

    response = test_client.get(
        url_for('media.genre_songs'),
        query_string={'id': genre.id, 'per_page': genre_songs_count}
    )

    assert response.status_code == 200

    songs = response.json.get('songs')
    assert songs
    assert len(songs) == genre_songs_count


def test_get_songs_from_album(test_client, fill_db):
    """
    Tests endpoint which should return all songs from specified album.
    """

    album = Album.query.first()

    response = test_client.get(
        url_for('media.album_songs'),
        query_string={'id': album.id}
    )

    assert response.status_code == 200

    songs = response.json.get('songs')
    assert songs
    assert len(songs) == len(list(album.songs))


def test_search_songs_by_title(test_client, songs_for_search, fill_db):
    """
    Tests view function which returns songs with title matching requested.
    """
    # Each song's title contains "search" in it
    search_songs, artist = songs_for_search

    response = test_client.get(
        url_for('media.songs_by_title'),
        query_string={'title': 'search'}
    )

    assert response.status_code == 200

    songs = response.json.get('songs')
    assert songs
    assert len(songs) == len(search_songs)

    for song in songs:
        assert song['title'] in [s.title for s in search_songs]


def test_search_songs_by_artist_title(test_client, songs_for_search, fill_db):
    """
    Tests view function which searches songs by artist's title.
    """

    search_songs, artist = songs_for_search

    response = test_client.get(
        url_for('media.songs_by_artist'),
        query_string={'title': artist.title}
    )

    assert response.status_code == 200

    songs = response.json.get('songs')
    assert songs
    assert len(songs) == len(search_songs)

    for s in songs:
        assert artist.title in s['artists']


def test_stream_song(test_client, fill_db):
    """
    Tests view function wich streams audio file as a response.
    """
    # Grab random song from db. All of them should point at the same mp3 file.
    song = Song.query.first()

    response = test_client.get(
        url_for('media.stream_song'),
        query_string={'id': song.id}
    )

    assert response.status_code == 200
    assert response.headers.get('Content-Type') == 'audio/mpeg'

    content = response.get_data()
    assert isinstance(content, bytes) or isinstance(content, bytearray)

    filename = 'streamed_song.mp3'

    with open(filename, 'wb+') as f:
        f.write(content)

    # This is going to throw an exception if this file is not valid mp3.
    try:
        song_info = EasyMP3(filename)
    except Exception:
        pytest.fail('Not a valid mp3 file.')

    assert song_info.tags.get('title')

    os.remove(filename)


def test_search_albums_by_title(test_client, albums_for_search, fill_db):
    """
    Tests view function wich searches albums by title
    """

    # All albums have 'search' in title
    search_albums = albums_for_search

    response = test_client.get(
        url_for('media.albums_by_title'),
        query_string={'title': 'search'}
    )

    assert response.status_code == 200

    albums = response.json.get('albums')
    assert albums
    assert len(albums) == len(search_albums)

    for album in albums:
        assert album['title'] in [a.title for a in search_albums]


def test_get_top_albums(test_client, fill_db):
    """
    Tests view function which returns top albums by listens
    """

    response = test_client.get(url_for('media.top_albums'))

    assert response.status_code == 200

    albums = response.json.get('albums')

    assert albums
    assert len(albums) != 0


def test_get_users_playlists(test_client, user_with_playlist, fill_db):
    """
    Tests view function which returns all playlists owned by user.
    This call requires token authentication.
    """

    user, access, refresh = user_with_playlist

    # If get parameter username is not provided -
    # playlists for this user will be sent back
    response = test_client.get(
        url_for('media.user_playlists'),
        headers={'Authorization': f'Bearer {access}'}
    )

    assert response.status_code == 200

    playlists = response.json.get('playlists')
    assert playlists
    assert len(playlists) == user.playlists.count()

    # Try to get other user's playlists by his username
    username = 'TestUser'

    response = test_client.get(
        url_for('media.user_playlists'),
        headers={'Authorization': f'Bearer {access}'},
        query_string={'username': username}
    )

    assert response.status_code == 404
    assert response.json.get('message') ==\
        f'Playlists not found for user {username}'


def test_create_new_playlist(test_client_json, user_with_playlist, fill_db):
    """
    Test creation of new playlist for user.
    """

    user, access, _ = user_with_playlist

    playlists_before = list(user.playlists)

    # First with empty title. Should return bad request.
    response = test_client_json.put(
        url_for('media.create_playlist'),
        headers={'Authorization': f'Bearer {access}'},
        data=json.dumps({'title': ''})
    )

    assert response.status_code == 400

    playlist_title = 'FreshlyCreated'
    response = test_client_json.put(
        url_for('media.create_playlist'),
        headers={'Authorization': f'Bearer {access}'},
        data=json.dumps({'title': playlist_title})
    )

    assert response.status_code == 200
    assert response.json.get('message') == \
        f'New playlist {playlist_title} have been created.'

    playlists_after = list(user.playlists)

    assert len(playlists_after) == len(playlists_before) + 1
    assert playlist_title in [p.title for p in playlists_after]


def test_delete_playlist(test_client_json, user_with_playlist, fill_db):
    """
    Tests deletetion of user's playlist.
    This causes warning on teardown of user_with_playlist fixture
    because it tries to delete this playlist again.
    """

    user, access, _ = user_with_playlist

    playlists_before = list(user.playlists)

    playlist_to_delete = playlists_before[0]

    response = test_client_json.delete(
        url_for('media.delete_playlist'),
        headers={'Authorization': f'Bearer {access}'},
        data=json.dumps({'id': playlist_to_delete.id})
    )

    assert response.status_code == 200
    assert playlist_to_delete.title in response.json.get('message') and\
        user.login in response.json.get('message')

    playists_after = list(user.playlists)
    assert len(playists_after) == len(playlists_before) - 1
    assert playlist_to_delete not in playists_after


def test_add_delete_song_from_playlist(test_client_json,
                                       user_with_playlist,
                                       fill_db):
    """
    Tests view functions which add and delete song from playlist.
    """

    user, access, _ = user_with_playlist

    playlist = list(user.playlists)[0]
    artist = Artist.query.first()

    song = Song(title='newsong', artist=artist, filepath='')
    db.session.add(song)
    db.session.commit()

    songs_before = playlist.songs.count()

    response = test_client_json.put(
        url_for('media.add_song_to_playlist'),
        headers={'Authorization': f'Bearer {access}'},
        data=json.dumps({'playlist_id': playlist.id, 'song_id': song.id})
    )

    assert response.status_code == 200
    assert playlist.songs.count() == songs_before + 1
    assert song in playlist.songs

    response = test_client_json.delete(
        url_for('media.delete_song_from_playlist'),
        headers={'Authorization': f'Bearer {access}'},
        data=json.dumps({'playlist_id': playlist.id, 'song_id': song.id})
    )

    assert response.status_code == 200
    assert playlist.songs.count() == songs_before
    assert song not in playlist.songs


def test_delete_other_user_playlist(test_client_json,
                                    user_with_playlist,
                                    user_with_tokens,
                                    fill_db):
    """
    Tests situation, when user tries to delete someone else's playlist.
    """

    user, access, _ = user_with_tokens
    user_with_playlist, _, _ = user_with_playlist

    playlist = list(user_with_playlist.playlists)[0]

    response = test_client_json.delete(
        url_for('media.delete_playlist'),
        headers={'Authorization': f'Bearer {access}'},
        data=json.dumps({'id': playlist.id})
    )

    assert response.status_code == 403
    assert response.json.get('message') == 'Operation is forbidden'


def test_pagination(test_client, fill_db):
    """
    Tests pagination of returned results.
    """
    title = 's'
    # Songs containing 'a' in title
    search_songs = Song.get_by_title(title)
    first_page = len(search_songs) // 2
    second_page = len(search_songs) - first_page

    first_response = test_client.get(
        url_for('media.songs_by_title'),
        query_string={
            'title': title,
            'per_page': first_page,
            'last_id': 0
            }
    )

    assert first_response.status_code == 200

    first_songs = first_response.json.get('songs')
    assert first_songs
    assert len(first_songs) == first_page

    # Songs should be sorted by id ascending
    assert first_songs == sorted(first_songs, key=lambda s: s['id'])

    # Id of the last song from list of songs
    last_id = first_songs[-1]['id']

    second_response = test_client.get(
        url_for('media.songs_by_title'),
        query_string={
            'title': title,
            'per_page': second_page,
            'last_id': last_id
            }
    )

    assert second_response.status_code == 200

    second_songs = second_response.json.get('songs')
    assert second_songs
    assert len(second_songs) == second_page

    first_ids = [s['id'] for s in first_songs]
    second_ids = [s['id'] for s in second_songs]

    # Check if a the songs from first and second queries is different
    assert set(first_ids).isdisjoint(set(second_ids))

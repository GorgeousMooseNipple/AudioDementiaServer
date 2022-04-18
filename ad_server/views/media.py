from flask import Blueprint, request, g
from ad_server.views.auth import token_auth
from ad_server.models import Song, Album, Playlist, Genre, User
from ad_server import db
from flask import Response
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
import ad_server.views.messages as msg


media = Blueprint('media', __name__)


def required_params(required):
    """
    Decorator for view functions.
    Takes dict of format <param_name>: <param_type>
    Checks if parameters is present in request with respective types.
    Returns error message otherwise.
    """
    def decorator(func):
        @wraps(func)
        def check_params(*args, **kwargs):
            # p - param name, t - param required type
            for p, t in required.items():
                try:
                    if request.is_json:
                        param = request.json[p]
                    else:
                        param = request.values[p]
                    kwargs[p] = t(param)
                except (KeyError, ValueError):
                    return msg.errors.bad_request(
                        f'Parameter {p} of type {t.__name__} is required')
            return func(*args, **kwargs)
        return check_params
    return decorator


@media.route('/genres/top', methods=['GET'])
def top_genres():
    """
    _server_/media/genres/top GET
    Returns list of genres sorted by popularity

    :return: response with fields _status_ and _message_
    """
    limit = 5
    top_genres = Genre.get_top(limit)
    if not top_genres:
        return msg.errors.internal_error('Error occured. Please try later')

    return msg.success(f'Top {limit} genres', genres=top_genres)


@media.route('/songs/playlist', methods=['GET'])
@required_params({'id': int})
def playlist_songs(id):
    """
    _server_/media/songs/playlist GET
    Returns songs for playlist specified by id.

    :param int id: id of a playlist
    :param last_id: pagination - id of the last received item from list on a previous page
    :param per_page: pagination - items per page
    :return: response with fields _status_, _message_ and _songs_ - list of songs
    """
    playlist = Playlist.query.get(id)

    if not playlist:
        return msg.errors.not_found('Playlist not found')

    per_page = request.args.get('per_page') or 20
    last_id = request.args.get('last_id') or 0

    songs = playlist.get_songs(per_page=per_page, last=last_id)

    if songs is None:
        return msg.errors.internal_error('Error occured. Please try later')
    elif len(songs) == 0:
        return msg.errors.not_found(
            f'Songs not found for playlist {playlist.title}')

    return msg.success(
        f'Songs from playlist {playlist.title}',
        songs=songs)


@media.route('/songs/genre', methods=['GET'])
@required_params({'id': int})
def genre_songs(id):
    """
    _server_/media/songs/genre GET
    Returns songs with matching genre

    :param int id: id of a genre
    :param last_id: pagination - id of the last received item from list on a previous page
    :param per_page: pagination - items per page
    :return: response with fields _status_, _message_ and _songs_ - list of songs
    """
    genre = Genre.query.get(id)

    if not genre:
        return msg.errors.not_found('Genre not found')

    per_page = request.args.get('per_page') or 20
    last_id = request.args.get('last_id') or 0

    songs = genre.get_songs(per_page=per_page, last=last_id)

    if songs is None:
        return msg.errors.internal_error('Error occured. Please try later')
    elif len(songs) == 0:
        return msg.errors.not_found(f'Songs not found for genre {genre.title}')

    return msg.success(
        f'Songs from genre {genre.title}',
        songs=songs
    )


@media.route('/songs/album', methods=['GET'])
@required_params({'id': int})
def album_songs(id):
    """
    _server_/media/songs/album GET
    Returns songs from an album

    :param int id: id of an album
    :param last_id: pagination - id of the last received item from list on a previous page
    :param per_page: pagination - items per page
    :return: response with fields _status_, _message_ and _songs_ - list of songs
    """
    album = Album.query.get(id)

    if not album:
        return msg.errors.not_found('Album not found')

    songs = album.get_songs()

    if songs is None:
        return msg.errors.internal_error('Error occured. Please try later')
    elif len(songs) == 0:
        return msg.errors.not_found(f'Songs not found for album {album.title}')

    return msg.success(
        f'Songs from album {album.title}',
        songs=songs
    )


@media.route('/songs/search', methods=['GET'])
@required_params({'title': str})
def songs_by_title(title):
    """
    _server_/media/songs/search GET
    Returns all songs matching the specified title.

    :param str title: title of a song
    :param last_id: pagination - id of the last received item from list on a previous page
    :param per_page: pagination - items per page
    :return: response with fields _status_, _message_ and _songs_ - list of fitting songs
    """
    if title == '' or title.isspace():
        return msg.errors.bad_request('Title parameter is an empty string')

    per_page = request.args.get('per_page') or 20
    last_id = request.args.get('last_id') or 0

    songs = Song.get_by_title(title, per_page=per_page, last=last_id)

    if songs is None:
        return msg.errors.internal_error('Error occured. Please try later')
    elif len(songs) == 0:
        return msg.errors.not_found(f'Songs not found with title {title}')

    return msg.success(
        f'Songs mathing title {title}',
        songs=songs
    )


@media.route('/songs/artist', methods=['GET'])
@required_params({'title': str})
def songs_by_artist(title):
    """
    _server_/media/songs/artits GET
    Returns all songs by specified artist.

    :param str title: title of an artist
    :param last_id: pagination - id of the last received item from list on a previous page
    :param per_page: pagination - items per page
    :return: response with fields _status_, _message_ and _songs_ - list of songs
    """
    if title == '' or title.isspace():
        return msg.errors.bad_request('Title parameter is an empty string')

    per_page = request.args.get('per_page') or 20
    last_id = request.args.get('last_id') or 0

    songs = Song.get_by_artist_title(title, per_page=per_page, last=last_id)

    if songs is None:
        return msg.errors.internal_error('Error occured. Please try later')
    elif len(songs) == 0:
        return msg.errors.not_found(f'Songs not found for artist {title}')

    return msg.success(
        f'Songs by artist matching title {title}',
        songs=songs
    )


@media.route('/songs/play', methods=['GET'])
@required_params({'id': int})
def stream_song(id):
    """
    _server_/media/songs/play GET
    Streams song specified by id.

    :param int id: id of a song
    :return: response with content type 'audio/mpeg' which contains stream of an audio file
    """

    # Get song filepath from db and increment listens count
    song_file = Song.play_song(id)
    if not song_file:
        return msg.errors.bad_request('Invalid id provided')
    db.session.commit()

    # Generator function. Yields chuncks of the file into Response
    def stream_file(filepath):
        # What is the optimal chunk size for this?
        chunk_size = 512
        with open(filepath, 'rb') as f:
            chunk = f.read(chunk_size)
            while chunk:
                yield chunk
                chunk = f.read(chunk_size)

    return Response(
        stream_file(song_file),
        status=200,
        content_type='audio/mpeg')


@media.route('/albums/search', methods=['GET'])
@required_params({'title': str})
def albums_by_title(title):
    """
    _server_/media/albums/search GET
    Returns all albums matching specified title.

    :param str title: searched title of an album
    :param last_id: pagination - id of the last received item from list on a previous page
    :param per_page: pagination - items per page
    :return: response with fields _status_, _message_ and _albums_ - list of albums
    """
    if title == '' or title.isspace():
        return msg.errors.bad_request('Title parameter is an empty string')

    per_page = request.args.get('per_page') or 20
    last_id = request.args.get('last_id') or 0

    albums = Album.get_by_title(title, per_page=per_page, last=last_id)

    if albums is None:
        return msg.errors.internal_error('Error occured. Please try later')
    elif len(albums) == 0:
        return msg.errors.not_found(f'Albums not found with title {title}')

    return msg.success(
        f'Abums matching title {title}',
        albums=albums
    )


@media.route('albums/top', methods=['GET'])
def top_albums():
    """
    _server_/media/albums/top GET
    Returns top albums sorted by listens

    :return: response with fields _status_ and _message_
    """
    limit = 5
    top_albums = Album.get_top(limit)
    if not top_albums:
        return msg.errors.internal_error('Error occured. Please try later')

    return msg.success(f'Top {limit} albums', albums=top_albums)


@media.route('/playlists/user', methods=['GET'])
@token_auth.login_required
def user_playlists():
    """
    _server_/media/playlists/user GET
    Returns playlists of current user of the one specified by username.
    Requires valid token in an Authorization header in a form Authorization: Bearer <token>

    :return: response with fields _status_, _message_ and _playlists_ - list of playlists
    """
    # If user id is specified in request - get that user's playlists
    username = request.values.get('username')

    if username:
        user = User.query.filter_by(login=username).first()
    else:
        # Otherwise - get current user's playlists
        # g.current_user is set in token verification method
        user = g.current_user

    if not user:
        return msg.errors.not_found('User not found')

    playlists = user.get_playlists()

    if playlists is None:
        return msg.errors.internal_error('Error occured. Please try later')
    elif len(playlists) == 0:
        return msg.errors.not_found(
            f'Playlists not found for user {user.login}')

    return msg.success(
        f'Playlists of user {user.login}',
        playlists=playlists
    )


@media.route('/playlists/add', methods=['PUT'])
@token_auth.login_required
@required_params({'title': str})
def create_playlist(title):
    """
    _server_/media/playlists/add PUT
    Adds new playlist for user
    Requires valid token in an Authorization header in a form Authorization: Bearer <token>

    :param str title: title of a new platlist
    :return: response with fields _status_ and _message_
    """

    if title == '' or title.isspace():
        return msg.errors.bad_request('Title parameter is an empty string')

    user = g.current_user
    playlist = Playlist(user_id=user.id, title=title)

    try:
        db.session.add(playlist)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return msg.errors.internal_error(
            'Unsuccesfull creation of playlist. Internal error')

    return msg.success(f'New playlist {title} have been created.')


@media.route('/playlists/add/song', methods=['PUT'])
@token_auth.login_required
@required_params({'playlist_id': int, 'song_id': int})
def add_song_to_playlist(playlist_id, song_id):
    """
    _server_/media/playlists/add/song PUT
    Adds song to a playlist.
    Requires valid token in an Authorization header in a form Authorization: Bearer <token>

    :param int playlist_id: id of a playlist to which a song should be added
    :param int songs_id: id of a song
    :return: response with fields _status_ and _message_
    """
    user = g.current_user
    playlist = Playlist.query.get(playlist_id)

    if not playlist:
        return msg.errors.not_found(
            f'Playlist with id {playlist_id} is not found')

    if user.id != playlist.user_id:
        return msg.errors.forbidden('Operation is forbidden')

    song = Song.query.get(song_id)

    if not song:
        return msg.errors.not_found(
            f'Song with id {song_id} is not found')

    try:
        playlist.add_song(song)
        db.session.commit()
        return msg.success(
            f'Song {song.title} was added to '
            f'playlist {playlist.title}')
    except SQLAlchemyError:
        db.session.rollback()
        return msg.errors.internal_error('Internal error.')


@media.route('/playlists/delete/song', methods=['DELETE'])
@token_auth.login_required
@required_params({'playlist_id': int, 'song_id': int})
def delete_song_from_playlist(playlist_id, song_id):
    """
    _server_/media/playlists/delete/song DELETE
    Delete song from a playlist.
    Requires valid token in an Authorization header in a form Authorization: Bearer <token>

    :param int playlist_id: id of a playlist from which a song should be deleted
    :param int songs_id: id of a song
    :return: response with fields _status_ and _message_
    """
    user = g.current_user
    playlist = Playlist.query.get(playlist_id)

    if not playlist:
        return msg.errors.not_found(
            f'Playlist with id {playlist_id} is not found')

    if user.id != playlist.user_id:
        return msg.errors.forbidden('Operation is forbidden')

    song = Song.query.get(song_id)

    if not song:
        return msg.errors.not_found(
            f'Song with id {song_id} is not found')

    try:
        playlist.songs.remove(song)
        db.session.commit()
        return msg.success(
            f'Song {song.title} was deleted from '
            f'playlist {playlist.title}')
    except SQLAlchemyError:
        db.session.rollback()
        return msg.errors.internal_error('Internal error.')
    # If song is not in playlist playlist.songs.remove will raise
    except ValueError:
        return msg.errors.bad_request('This song is already not in playlist')


@media.route('/playlists/delete', methods=['DELETE'])
@token_auth.login_required
@required_params({'id': int})
def delete_playlist(id):
    """
    _server_/media/playlists/delete DELETE
    Delete playlist.
    Requires valid token in an Authorization header in a form Authorization: Bearer <token>

    :param int id: id of a playlist which should be deleted
    :return: response with fields _status_ and _message_
    """
    user = g.current_user
    playlist = Playlist.query.get(id)

    if not playlist:
        return msg.errors.not_found(f'Playlist with id {id} is not found')

    if user.id != playlist.user_id:
        return msg.errors.forbidden('Operation is forbidden')

    try:
        db.session.delete(playlist)
        db.session.commit()
        return msg.success(
            f'Playlist {playlist.title} of user {user.login} is deleted')
    except SQLAlchemyError:
        db.session.rollback()
        return msg.errors.internal_error(
            'Internal error. Playlist deletion failed.')

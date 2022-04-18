from ad_server import create_app, db
from ad_server.models import (
    Song,
    Album,
    User,
    Genre,
    Artist,
    Playlist,
    PlaylistSong,
    AlbumArtist,
    AlbumGenre,
    RefreshToken,
    )


app = create_app()


@app.shell_context_processor
def get_shell_context():
    return {
        'db': db,
        'app': app,
        'Song': Song,
        'Album': Album,
        'Artist': Artist,
        'User': User,
        'Genre': Genre,
        'Playlist': Playlist,
        'PlaylistSong': PlaylistSong,
        'AlbumGenre': AlbumGenre,
        'AlbumArtist': AlbumArtist,
        'RefreshToken': RefreshToken,
        }

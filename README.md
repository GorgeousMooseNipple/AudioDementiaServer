## Flask based REST music streaming service

![Build Status](https://github.com/GorgeousMooseNipple/AudioDementiaServer/actions/workflows/python-app.yml/badge.svg?event=push)
[![codecov](https://codecov.io/gh/GorgeousMooseNipple/AudioDementiaServer/branch/master/graph/badge.svg)](https://codecov.io/gh/GorgeousMooseNipple/AudioDementiaServer)

Server side for [my music streaming android application](https://github.com/GorgeousMooseNipple/AudioDementiaApp). It was built using [Flask][flask] web framework.

## Contents
* [Description](#description)
* [Dependencies](#dependencies)
* [Improvements](#improvements)

## Description
This application provides REST API endpoints to handle working with users, basic and token authentication, managing playlists, searching database for music related content and streaming audio files.  
It uses [postgres][postgres] as a database. All audio files themselves are stored in a file system.  
Detailed information about songs, albums and links to album covers retrieved via [last.fm API][last-fm-api] and stored in a database.  
All http responses contain data in a JSON format.  

## Dependencies
Besides [Flask][flask] as a base web framework, this application uses:  
* [Flask-HttpAuth][flask-http-auth] to provide basic authentication capabilities
* [Flask-SqlAlchemy][flask-sqlalchemy] as an ORM to communicate with postgres database
* [Flask-Migrate][flask-migrate] to handle SQLAlchemy database migrations
* [PyJWT][pyjwt] as a way to introduce token authentication
* [Requests][requests] to get data from last.fm API
* [Mutagen][mutagen] to extract metadata from local audio files
* and [Pytest][pytest] for testing during development

## Improvements
* Provide private API endpoints as an admin panel
* Rework application files structure
* Provide a comfortable way to upload new audio files. So far it just uses python script to add files from a local folder.

[flask]: [https://github.com/pallets/flask]
[flask-http-auth]: [https://github.com/miguelgrinberg/Flask-HTTPAuth]
[flask-sqlalchemy]: [https://github.com/pallets-eco/flask-sqlalchemy]
[flask-migrate]: [https://github.com/miguelgrinberg/Flask-Migrate]
[last-fm-api]: [https://www.last.fm/api]
[postgres]: [https://www.postgresql.org/]
[pyjwt]: [https://github.com/jpadilla/pyjwt]
[requests]: [https://github.com/psf/requests]
[mutagen]: [https://github.com/quodlibet/mutagen]
[pytest]: [https://github.com/pytest-dev/pytest]

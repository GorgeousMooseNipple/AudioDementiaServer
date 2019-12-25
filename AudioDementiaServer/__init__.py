#!/usr/bin/env python
import os


def getEnvVar(name):
    try:
        return os.environ[name]
    except KeyError:
        raise Exception(f'Environment variable {name} is not set.')


pg_url = getEnvVar('POSTGRES_URL')
pg_user = getEnvVar('POSTGRES_USER')
pg_pw = getEnvVar('POSTGRES_PW')
pg_db = getEnvVar('POSTGRES_DB')

CONFIG = {}
CONFIG['CONNECTION_STRING'] = f'postgresql+psycopg2://{pg_user}:{pg_pw}@{pg_url}/{pg_db}'
#!/usr/bin/env python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from AudioDementiaServer import CONFIG

app = Flask(__name__)

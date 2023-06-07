import json

from flask import Flask, url_for
from markupsafe import escape

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello'


@app.route('/user/<name>')
def user_page(name):
    return f'User: {escape(name)}'


@app.route('/test')
def test_url_for():
    res = []
    res.append(url_for('hello'))
    res.append(url_for('user_page', name='max'))
    res.append(url_for('test_url_for'))
    return json.dumps(res)

#coding=utf-8
import os
from bottle import Bottle, TEMPLATE_PATH, run
from beaker.middleware import SessionMiddleware

from admin.config.routing import setup_routing
from admin.config.config import DEBUG, HOST, PORT


def setup_app():
    root = os.path.dirname(os.path.abspath(__file__))
    session_opts = {
        'session.type': 'file',
        'session.cookie_expires': 3600 * 10,
        'session.data_dir': os.path.join(root, 'data/'),
        'session.auto': True
    }

    app = Bottle()
    app = setup_routing(app)
    TEMPLATE_PATH.append(os.path.join(root, 'templates/'))
    TEMPLATE_PATH.remove('./views/')
    app = SessionMiddleware(app, session_opts)
    return app

app = setup_app()

if __name__ == '__main__':
    run(app, host=HOST, port=PORT, debug=DEBUG, reloader=True)

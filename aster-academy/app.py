"""Application entry point. HTTP controller and services live in their MVC layers."""
import os
import sys
from http.server import ThreadingHTTPServer
from core import HOST, PORT, init_db, bootstrap_admin
from controllers.http_controller import App

if __name__ == '__main__':
    init_db()
    if len(sys.argv)>1 and sys.argv[1]=='--create-admin':
        bootstrap_admin()
    else:
        print(f'Aster Academy: http://{HOST}:{PORT} · Admin: http://{HOST}:{PORT}/admin')
        ThreadingHTTPServer((HOST,PORT),App).serve_forever()

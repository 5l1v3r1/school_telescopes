#!/usr/bin/env python
"""
Starts a Tornado static file server in a given directory.
To start the server in the current directory:

    tserv .

Then go to http://localhost:8000 to browse the directory.

Use the --prefix option to add a prefix to the served URL,
for example to match GitHub Pages' URL scheme:

    tserv . --prefix=jiffyclub

Then go to http://localhost:8000/jiffyclub/ to browse.

Use the --port option to change the port on which the server listens.

"""


import os
import sys
from argparse import ArgumentParser
import pwd
import spwd
import crypt

import tornado.ioloop
import tornado.web
import tornado.template

class IndexHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET']
    @tornado.web.authenticated
    def get(self, path):
        """ GET method to list contents of directory or
        write index page if index.html exists."""

        # remove heading slash
        #path = path[1:]

        for index in ['index.html', 'index.htm']:
            index = os.path.join(path, index)
            if os.path.exists(index):
                with open(index, 'rb') as f:
                    self.write(f.read())
                    self.finish()
                    return
        html = self.generate_index(path)
        self.write(html)
        self.finish()

    def generate_index(self, path):
        """ generate index html page, list all files and dirs.
        """
        if path:
            files = os.listdir(path)
        else:
            files = os.listdir('.')
        files = [filename + '/'
                if os.path.isdir(os.path.join(path, filename))
                else filename
                for filename in files]
        html_template = """
        <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"><html>
        <title>Directory listing for /{{ path }}</title>
        <body>
        <h2>Directory listing for /{{ path }}</h2>
        <hr>
        <ul>
        {% for filename in files %}
        <li><a href="{{ filename }}">{{ filename }}</a>
        {% end %}
        </ul>
        <hr>
        </body>
        </html>
        """
        t = tornado.template.Template(html_template)
        return t.generate(files=files, path=path)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class Handler(tornado.web.StaticFileHandler):
    @tornado.web.authenticated
    def parse_url_path(self, url_path):
        if not url_path or url_path.endswith('/'):
            url_path = url_path + 'index.html'
        return url_path

class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   '<h3>Radio Telescope Data System</h3>'
                   'Username: <input type="text" name="name">'
                   '<br>'
                   'Password: <input type="password" name="pw">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        user = self.get_argument("name")
        pw = self.get_argument("pw")
        errstr = "<html><body><h3>Unknown Username or Password</h3></body></html>"
        goodstr = "<html><body><h3>Login successful</h3></body></html>"
        try:
            pw_struct = pwd.getpwnam(user)
        except:
            self.write(errstr)
            return
        
        if (pw_struct.pw_uid < 10):
            self.write(errstr)
            return
        try:
            spw_struct = spwd.getspnam(user)
        except:
            self.write(errstr)
            return
            
        epassword = crypt.crypt(pw, spw_struct.sp_pwd)
        if (epassword != spw_struct.sp_pwd):
            self.write(errstr)
        else:
            self.write(goodstr)
            self.set_secure_cookie("user", user)

def mkapp(cookie_secret):
    application = tornado.web.Application([
        (r"/login", LoginHandler),
        (r"/(.*)/$", IndexHandler),
        (r"/(astro_data)$", IndexHandler),
        (r"/astro_data/(.*)", Handler, {'path': "/home/astronomer/astro_data"}),
        (r"/(real-time\.html)", Handler, {'path' : "/home/astronomer"}),
        (r"/(expcontrol\.html)", Handler, {'path' : "/home/astronomer"}),
        (r"/(jquery.*\.js)", Handler, {'path' : "/home/astronomer"}),
        (r"/(experiment.*\.json)", Handler, {'path' : "/home/astronomer"})
    ], debug=False, cookie_secret=cookie_secret, login_url="/login")

    return application

import random
def start_server(port=8000):
    
    #
    # Deal with cookie secret
    #
    rf = open("/dev/urandom", "r")
    rv = rf.read(32)
    rv = rv.encode('hex')
    rf.close()
    
    try:
        f=open(".cookie_secret", "r")
    except:
        f=open(".cookie_secret", "w")
        f.write(rv+"\n")
        f.close()
        f=open(".cookie_secret", "r")
    
    cook = f.read()
    cook = cook.strip('\n')
    print cook
    
    app = mkapp(cook)
    app.listen(port)
    tornado.ioloop.IOLoop.instance().start()


def main(args=None):
    print('Starting server on port 8000')
    start_server(port=8000)


if __name__ == '__main__':
    sys.exit(main())

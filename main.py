#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import jinja2
import webapp2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def get_posts(lim, off):
    #posts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC LIMIT 5 OFFSET 5")

    #posts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC limit :lim offset :off" , lim = lim, off = off)
    #return posts

    query = BlogPost.all().order('-created')  #THis is a bad way to do it when the DB is large...
    return query.fetch(limit=lim, offset=off)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class BlogPost(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

class MainHandler(Handler):
    def render_bloghome(self, subject="", content="", error="", posts="", next_page="", prev_page=""):
        page = self.request.get("page")
        page_limit = 5
        offset = 0
        page = page and int(page)
        if page:
            offset = (page-1)*page_limit
        else:
            page = 1
        posts = get_posts(int(page_limit), int(offset))
        prev_page = None
        next_page = None
        if page > 1:
            prev_page= page-1
        if len(posts) == page_limit and BlogPost.all().count() > offset+page_limit:
            next_page = page + 1

        self.render("bloghome.html", subject=subject, content = content, error=error, posts=posts, next_page=next_page, prev_page=prev_page)

    def get(self):
        self.render_bloghome()

class BlogHandler(Handler):
    def get(self):
        self.render("bloghome.html")



class NewPostHandler(Handler):
    def render_blogpost(self, subject="", content="", error=""):
        self.render("blogpost.html", subject=subject, content = content, error=error)

    def get(self):
        self.render_blogpost()

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            a = BlogPost(subject=subject, content = content) #create art object from the database class
            a.put() #store entity in the database
            id = a.key().id()
            self.redirect("/blog/"+ str(id))
        else:
            error = "we need a subject and content!"
            self.render_blogpost(subject, content, error)

class ViewPostHandler(Handler):
    def get(self, id):
        post = BlogPost.get_by_id(int(id))

        if not post:
            self.render("permalink.html", post = post, error = "This blog entry does NOT exist")
        else:
            self.render("permalink.html", post = post)


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/blog', MainHandler),
    ('/blog/newpost', NewPostHandler),
    webapp2.Route('/blog/<id:\d+>', ViewPostHandler)
], debug=True)

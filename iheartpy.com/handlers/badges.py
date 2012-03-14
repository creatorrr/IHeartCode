#!/usr/bin/python

# Copyright 2011-12 Diwank SIngh Tomer
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An interactive, Python instructor.

Uses AIML for interactive tutorial.

Latest build on GitHub http://creatorrr.github.com/IHeartPy

Interpreter state is stored as strings in the memcache so that variables, function
definitions, and other values in the global and local namespaces can be used
across commands.
"""

import sys
import logging
import os
import wsgiref.handlers
import random

sys.path.append(os.path.abspath(''))

from models import *

try:
  from google.appengine.api import users
  from google.appengine.ext import webapp
  from google.appengine.ext.webapp import template


except ImportError:
  from google3.apphosting.api import users
  from google3.apphosting.ext import webapp
  from google3.apphosting.ext.webapp import template


# Set to True if stack traces should be shown in the browser, etc.
_DEBUG = False

# The entity kind for shell sessions. Feel free to rename to suit your app.
_GA_ID='UA-25004086-1'

#List of Awards
_AWARDS = ['Lover', 'Rookie', 'Master', 'Pro', 'God']

def getQuote():
  """Returns a randomized quotation"""
  libraryFile=open('../site/quotes.txt','r')
  library=libraryFile.readlines()
  return (random.choice(library)).split(';')

class BadgeHandler(webapp.RequestHandler):
  """Creates a badge page using email."""

  def get(self):
    # set up the session. TODO: garbage collect old shell sessions
    try:
        email = self.request.get('email')
        query=ShellUser.all()
        query.filter("email = ", email)
        user = query.get()
        level = int(user.current_lesson/4)
        award = _AWARDS[level]
        template_file = os.path.abspath('../site/badges.html')
        quote=getQuote()

        vars = { 'user': users.get_current_user(),
             'login_url': users.create_login_url('/shell'),
             'logout_url': users.create_logout_url('/'),
             'quotation': quote[0],
             'quotation_author': quote[1],
             'quotation_link': quote[2],
             'title': 'Badge',
             'analytics_id':_GA_ID,
             'award': award,
             'awardee': user.name,
             'badge_url': '/badges?email=%s' % user.email,
             }
        rendered = webapp.template.render(template_file, vars, debug=_DEBUG)
        self.response.out.write(rendered)
    except:
        logging.warning("Badge for Email: %s not found" % email)
        self.redirect("/instructions")

def main():
  application = webapp.WSGIApplication(
    [('/badges', BadgeHandler),], debug=_DEBUG)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()

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
I Heart Py!
Main Page Handler

"""

import logging
import os
import wsgiref.handlers
import random

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
_GA_ID = 'UA-25004086-1'


def getQuote():
  """Returns a randomized quotation"""
  libraryFile=open('../site/quotes.txt','r')
  library=libraryFile.readlines()
  return (random.choice(library)).split(';')

class PageHandler(webapp.RequestHandler):
  """Renders the Front Page."""

  def get(self,argument):
    # set up the session. TODO: garbage collect old shell sessions

    uagent = self.request.user_agent.lower()
    mobile = False
    if ("mobi" in uagent) or ("mini" in uagent):
        mobile = True

    iOS = False
    if ("iphone" in uagent) or ("ipad" in uagent):
        iOS = True

    if argument in ('','shell','resources','instructions','wth'):
		template_file = os.path.abspath('../site/'+argument+'.html')
		template_fallback = os.path.abspath('../site/main.html')
	
    else:
		template_fallback = template_file = os.path.abspath('../site/error.html')

    
    session_url = '/shell'
    quote=getQuote()

    vars = { 'user': users.get_current_user(),
             'login_url': users.create_login_url('/shell'),
             'logout_url': users.create_logout_url('/'),
             'quotation': quote[0],
             'quotation_author': quote[1],
             'quotation_link': quote[2],
             'title': argument or 'home',
             'analytics_id': _GA_ID,
             'mobile': mobile,
             'iOS': iOS,
             }
    try:
    	rendered = webapp.template.render(template_file, vars, debug=_DEBUG)
    except:
    	rendered = webapp.template.render(template_fallback, vars, debug=_DEBUG)
    
    logging.info(argument+' called.')
    self.response.out.write(rendered)

def main():
  application = webapp.WSGIApplication(
						    [('/(.*)', PageHandler),], debug=_DEBUG)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()

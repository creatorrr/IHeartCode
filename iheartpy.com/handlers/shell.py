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

import logging
import pickle
import new
import os
import sys
import traceback
import types
import wsgiref.handlers
import random

sys.path.append(os.path.abspath(''))

import lolpython
import aiml
import highlighter
from models import *

try:
  from google.appengine.api import users
  from google.appengine.ext import db
  from google.appengine.ext import webapp
  from google.appengine.ext.webapp import template
  from google.appengine.ext.webapp.util import login_required
  INITIAL_UNPICKLABLES = [
    'from google.appengine.ext import db',
    'from google.appengine.api import users',
	]

except ImportError:
  from google3.apphosting.api import users
  from google3.apphosting.ext import db
  from google3.apphosting.ext import webapp
  from google3.apphosting.ext.webapp import template
  from google3.apphosting.ext.webapp.util import login_required
  INITIAL_UNPICKLABLES = [
    'from google3.apphosting.ext import db',
    'from google3.apphosting.api import users',
    ]


# Set to True if stack traces should be shown in the browser, etc.
_DEBUG = False

# The entity kind for shell sessions. Feel free to rename to suit your app.
_SESSION_KIND = 'IHeartPy_Shell_Session'
_GA_ID='UA-25004086-1'

# Types that can't be pickled.
UNPICKLABLE_TYPES = (
  types.ModuleType,
  types.TypeType,
  types.ClassType,
  types.FunctionType,
  )

# Unpicklable statements to seed new sessions with.
INITIAL_UNPICKLABLES += [
  'import logging',
  'import os',
  'import sys',
  'class Foo(db.Expando):\n  pass',
  ]

def getQuote():
  """Returns a randomized quotation"""
  libraryFile=open('../site/quotes.txt','r')
  library=libraryFile.readlines()
  return tuple((random.choice(library)).split(';'))

def send_greeting(recipient):
  from google.appengine.api import mail

  diwank = "Python Lover! <diwank@iheartpy.com>"
  alternate_addr = "diwank.singh@gmail.com"
  header = "Happy Coding!"
  content = """Hi!

Just wrote in to say hello.

Welcome to IHeartPy!
We hope you love using the service as much as we loved making it a reality.

Feel free to write in.
We love feedback.
Just reply back with your thoughts.

Thanks!

Take care.

Diwank
@IHeartPy

P.s. This was the only time we couldn't resist bothering you!
Don't worry. We won't spam you.
Pinky Promise.

"%s"
 ~ %s
 %s
""" % getQuote()
  
  try:
      mail.send_mail(sender = diwank,
              to = recipient,
              subject = header,
              body = content,
              reply_to = alternate_addr)
  except:
      logging.warning('Unable to send greeting email.')

def responder(statement,chat,user):
  """Lesson Handler"""
  kernel=aiml.Kernel()
  kernel.verbose(False)
  current_lesson = user.current_lesson
  kernel.bootstrap(brainFile='rawAIML/lesson%d.brn'%(int(current_lesson)),commands=[])
  statement=statement.replace('=',' EQUALS ').replace('**',' POW ').replace('*',' MUL ').replace('(',' ').replace(')',' ').replace('"',' ')
  chat=chat.replace('=',' EQUALS ').replace('**',' POW ').replace('*',' MUL ').replace('(',' ').replace(')',' ').replace('"',' ')
  kernel.setPredicate('topic','sublesson%d'%(int(current_lesson*10)%10))
  kernel.setBotPredicate('user',user.name)
  kernel.setPredicate('gender','male') #TODO: gert gender info
  reply=''
  if kernel.respond(statement).split('#')[0]:
      reply+='\n#'+(kernel.respond(statement).split('#')[0].replace('\n','\n#'))
  if kernel.respond(chat):
      reply+='\n#'+kernel.respond(chat).replace('\n','\n#')
  try:
      user.current_lesson = float(kernel.getPredicate('lesson'))
      user.put()
  except:
      logging.warning('Lesson not set')
  return reply+'\n'

class ShellPageHandler(webapp.RequestHandler):
  """Creates a new session and renders the shell.html template."""

  def get(self):
    # set up the session. TODO: garbage collect old shell sessions. Try cron backend.

    first_time = False
    user=users.get_current_user()
    query=ShellUser.all()
    query.filter("account = ", user)
    db_user = query.get()
    
    uagent = self.request.user_agent.lower()
    
    if not db_user:
       #Register the User.
       first_time = True
       db_user = ShellUser(name=user.nickname(),
							account = user,
							email = user.email(),
							current_lesson = 1.1)
       db_user.put()
       send_greeting(user.email())
       logging.info("New user: %s registered" % user.nickname())

    session_key = self.request.get('session')
    is_mobile = False
    if session_key:
      session = Session.get(session_key)
    else:
      # create a new session
      session = Session()
      session.unpicklables = [db.Text(line) for line in INITIAL_UNPICKLABLES]
      session_key = session.put()

    template_file = os.path.abspath('../site/shell.html')
    
    if ("mobi" in uagent) or ("mini" in uagent):
        is_mobile = True
    
    if is_mobile:
		template_file = os.path.abspath('../site/mobile.html')

    session_url = '/shell'
    quote=getQuote()

    notifications="Feedback."
    
    greetings = "To get started, type #Hello and hit enter."
    
    vars = { 'server_software': os.environ['SERVER_SOFTWARE'],
             'python_version': sys.version,
             'session': str(session_key),
             'user': users.get_current_user(),
             'login_url': users.create_login_url(session_url),
             'greetings': greetings,
             'logout_url': users.create_logout_url('/shell.delete?session=%s' % str(session_key)),
             'notifications': notifications,
             'quotation': quote[0],
             'quotation_author': quote[1],
             'quotation_link': quote[2],
             'title': 'Shell',
             'analytics_id':_GA_ID,
             'badge_url': '/badges?email=%s' % users.get_current_user().email(),
             'first_time':first_time,
             }
    rendered = webapp.template.render(template_file, vars, debug=_DEBUG)
    self.response.out.write(rendered)


class HangoutHandler(webapp.RequestHandler):
  """Handles hanoguts!"""

  def get(self):
    # set up the session. 

    session_key = self.request.get('session')
    is_mobile = False
    if session_key:
      session = Session.get(session_key)
    else:
      # create a new session
      session = Session()
      session.unpicklables = [db.Text(line) for line in INITIAL_UNPICKLABLES]
      session_key = session.put()

    template_file = os.path.abspath('../site/hangouts.xml')

    quote=getQuote()
    
    greetings = "To get started, type #Hello and hit enter.\n"
    
    vars = { 'session': str(session_key),
             'greetings': greetings,
             'quotation': quote[0],
             'quotation_author': quote[1],
             'quotation_link': quote[2],
             }

    self.response.headers['Content-Type'] = 'text/xml'		#HANGOUTS require xml files!
    rendered = webapp.template.render(template_file, vars, debug=_DEBUG)
    self.response.out.write(rendered)


class StatementHandler(webapp.RequestHandler):
  """Evaluates a python statement in a given session and returns the result."""

  @login_required		#SHIT! TODO: Try and see if login works inside of Hangouts....
  def get(self):
    # extract the statement to be run
    
    first_time = False
    user=users.get_current_user()
    query=ShellUser.all()
    query.filter("account = ", user)
    db_user = query.get()

    statement = self.request.get('statement')
    if not statement:
      return

    # the python compiler doesn't like network line endings
    statement = statement.replace('\r\n', '\n')
    is_mobile = False

    uagent = self.request.user_agent.lower()

    # add a couple newlines at the end of the statement. this makes
    # single-line expressions such as 'class Foo: pass' evaluate happily.
    statement += '\n'
    
    if ("mobi" in uagent) or ("mini" in uagent):
        is_mobile = True
    
    mobile_template=[os.path.abspath('../site/mobile.part.html'),os.path.abspath('../site/mobile.part2.html')]
    tidbit = '</div><form name="shell" action="shell.do" method="get"><textarea id="prompt" name="statement">#Type Away!</textarea><input id="shellSessionId" type="hidden" name="session" value="'

    lol = self.request.get('lol')
    if lol == '1':
      statement = lolpython.to_python(statement)
      import sys as _lol_sys
      statement=statement.strip()

    reply=''
    chat=(''.join([statement,'#']).split('#')[1])

    self.response.clear()

    if is_mobile:
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(open(mobile_template[0]).read())
        highlighter.Parser(statement,self.response.out).format()
    else:
        self.response.headers['Content-Type'] = 'text/text'
        self.response.out.write(statement)
    
    statement = statement.split('#')[0] #TODO: change this.
    reply=responder(statement,chat,db_user)

    # log and compile the statement up front
    try:
      if statement.strip():
          compiled = compile(statement, '<string>', 'single')
    except:
      self.response.out.write(traceback.format_exc())
      self.response.out.write(responder('some stupid error','',db_user))
      return

    # create a dedicated module to be used as this statement's __main__
    statement_module = new.module('__main__')

    # use this request's __builtin__, since it changes on each request.
    # this is needed for import statements, among other things.
    import __builtin__
    statement_module.__builtins__ = __builtin__

    # load the session from the datastore
    session_id = self.request.get('session')
    session = Session.get(session_id)

    # swap in our custom module for __main__. then unpickle the session
    # globals, run the statement, and re-pickle the session globals, all
    # inside it.
    old_main = sys.modules.get('__main__')
    try:
      sys.modules['__main__'] = statement_module
      statement_module.__name__ = '__main__'

      # re-evaluate the unpicklables
      for code in session.unpicklables:
        exec code in statement_module.__dict__

      # re-initialize the globals
      for name, val in session.globals_dict().items():
        try:
          statement_module.__dict__[name] = val
        except:
          msg = 'Dropping %s since it could not be unpickled.\n' % name
          self.response.out.write(msg)
          logging.warning(msg + traceback.format_exc())
          session.remove_global(name)

      # run!
      old_globals = dict(statement_module.__dict__)
      try:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
          sys.stdout = self.response.out
          sys.stderr = self.response.out
          if statement.strip():
                exec compiled in statement_module.__dict__
        finally:
          sys.stdout = old_stdout
          sys.stderr = old_stderr
      except:
        self.response.out.write(traceback.format_exc())
        self.response.out.write(responder('some stupid error','',db_user))
        return

      # extract the new globals that this statement added
      new_globals = {}
      for name, val in statement_module.__dict__.items():
        if name not in old_globals or val != old_globals[name]:
          new_globals[name] = val

      if True in [isinstance(val, UNPICKLABLE_TYPES)
                  for val in new_globals.values()]:
        # this statement added an unpicklable global. store the statement and
        # the names of all of the globals it added in the unpicklables.
        session.add_unpicklable(statement, new_globals.keys())

      else:
        # this statement didn't add any unpicklables. pickle and store the
        # new globals back into the datastore.
        session.set_global('help', 'Use the instructions link at the bottom for more info.')
        session.set_global('author', 'Diwank Singh')
        session.set_global('about', 'The friendly Python Instructor')
        session.set_global('inspiration', 'Ila Nitin Gokarn')
        for name, val in new_globals.items():
          if not name.startswith('__'):
            session.set_global(name, val)

    finally:
      sys.modules['__main__'] = old_main

    self.response.out.write(reply)
    if is_mobile:
        self.response.out.write(tidbit)
        self.response.out.write(session_id)
        self.response.out.write(open(mobile_template[1]).read())
    session.put()
    
  def post(self):
    # extract the statement to be run. RUNNING IN HANGOUT.

    if not self.request.get('hangouts'):
        return

    statement = self.request.get('statement')
    if not statement:
      return

    # the python compiler doesn't like network line endings
    statement = statement.replace('\r\n', '\n')
    is_mobile = False


    # add a couple newlines at the end of the statement. this makes
    # single-line expressions such as 'class Foo: pass' evaluate happily.
    statement += '\n'
    

    lol = self.request.get('lol')
    if lol == '1':
      statement = lolpython.to_python(statement)
      import sys as _lol_sys
      statement=statement.strip()

    reply=''
    chat=(''.join([statement,'#']).split('#')[1])

    self.response.clear()

    self.response.headers['Content-Type'] = 'text/text'
    self.response.out.write(statement)
    
    statement = statement.split('#')[0] #TODO: change this.
    reply=responder(statement,chat,db_user)

    # log and compile the statement up front
    try:
      if statement.strip():
          compiled = compile(statement, '<string>', 'single')
    except:
      self.response.out.write(traceback.format_exc())
      self.response.out.write(responder('some stupid error','',db_user))
      return

    # create a dedicated module to be used as this statement's __main__
    statement_module = new.module('__main__')

    # use this request's __builtin__, since it changes on each request.
    # this is needed for import statements, among other things.
    import __builtin__
    statement_module.__builtins__ = __builtin__

    # load the session from the datastore
    session_id = self.request.get('session')
    session = Session.get(session_id)

    # swap in our custom module for __main__. then unpickle the session
    # globals, run the statement, and re-pickle the session globals, all
    # inside it.
    old_main = sys.modules.get('__main__')
    try:
      sys.modules['__main__'] = statement_module
      statement_module.__name__ = '__main__'

      # re-evaluate the unpicklables
      for code in session.unpicklables:
        exec code in statement_module.__dict__

      # re-initialize the globals
      for name, val in session.globals_dict().items():
        try:
          statement_module.__dict__[name] = val
        except:
          msg = 'Dropping %s since it could not be unpickled.\n' % name
          self.response.out.write(msg)
          logging.warning(msg + traceback.format_exc())
          session.remove_global(name)

      # run!
      old_globals = dict(statement_module.__dict__)
      try:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
          sys.stdout = self.response.out
          sys.stderr = self.response.out
          if statement.strip():
                exec compiled in statement_module.__dict__
        finally:
          sys.stdout = old_stdout
          sys.stderr = old_stderr
      except:
        self.response.out.write(traceback.format_exc())
        self.response.out.write(responder('some stupid error','',db_user))
        return

      # extract the new globals that this statement added
      new_globals = {}
      for name, val in statement_module.__dict__.items():
        if name not in old_globals or val != old_globals[name]:
          new_globals[name] = val

      if True in [isinstance(val, UNPICKLABLE_TYPES)
                  for val in new_globals.values()]:
        # this statement added an unpicklable global. store the statement and
        # the names of all of the globals it added in the unpicklables.
        session.add_unpicklable(statement, new_globals.keys())

      else:
        # this statement didn't add any unpicklables. pickle and store the
        # new globals back into the datastore.
        session.set_global('help', 'Use the instructions link at the bottom for more info.')
        session.set_global('author', 'Diwank Singh')
        session.set_global('about', 'The friendly Python Instructor')
        session.set_global('inspiration', 'Ila Nitin Gokarn')
        for name, val in new_globals.items():
          if not name.startswith('__'):
            session.set_global(name, val)

    finally:
      sys.modules['__main__'] = old_main

    self.response.out.write(reply)
    session.put()




class LogoutHandler(webapp.RequestHandler):
  """Deletes session and redirects to feedback form."""

  def get(self):
    # set up the session. TODO: garbage collect old shell sessions
    session_key = self.request.get('session')
    if session_key:
      session = Session.get(session_key)

    if session:
      session.delete()

    self.redirect("https://docs.google.com/spreadsheet/viewform?formkey=dG5OSlBTTGJrYUVjVjloRXhjYlE3c2c6MQ")


def main():
  application = webapp.WSGIApplication(
    [('/shell', ShellPageHandler),
     ('/shell.do', StatementHandler),
     ('/shell.delete', LogoutHandler),
     ('/hangouts', HangoutHandler)], debug=_DEBUG)		#ADDED Hangout supprt
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()

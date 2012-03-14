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


import types

try:
  from google.appengine.api import users
  from google.appengine.ext import db
  from google.appengine.ext import webapp
  from google.appengine.ext.webapp import template
  INITIAL_UNPICKLABLES = [
    'from google.appengine.ext import db',
    'from google.appengine.api import users',
	]

except ImportError:
  from google3.apphosting.api import users
  from google3.apphosting.ext import db
  from google3.apphosting.ext import webapp
  from google3.apphosting.ext.webapp import template
  INITIAL_UNPICKLABLES = [
    'from google3.apphosting.ext import db',
    'from google3.apphosting.api import users',
    ]


_DEBUG = False

_SESSION_KIND = 'IHeartPy_Shell_Session'

UNPICKLABLE_TYPES = (
  types.ModuleType,
  types.TypeType,
  types.ClassType,
  types.FunctionType,
  )

INITIAL_UNPICKLABLES += [
  'import logging',
  'import os',
  'import sys',
  'class Foo(db.Expando):\n  pass',
  ]

notifications = [
  'Hola, &#223;-Tester! Rough Seas ahead...',
  'Give Feedback!',
  'Something broken?',
  'Oh dear...',
  'Glad to see you.',
  ]

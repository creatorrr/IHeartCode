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


import cgi, string, sys, cStringIO
import keyword, token, tokenize

# Python Source Parser (does highlighting into HTML)

_KEYWORD = token.NT_OFFSET + 1
_TEXT = token.NT_OFFSET + 2
_colors = {
                        token.NUMBER:'#0080C0',
                        token.OP:'#0000C0',
                        token.STRING:'#004080',
                        tokenize.COMMENT:'#008000',
                        token.NAME:'#000000',
                        token.ERRORTOKEN:'#FF8080',
                        _KEYWORD:'#C00000',
                        _TEXT:'#000000',
                        }


class Parser:
        """ Send colorized Python source as HTML to an output file (normally stdout)."""

        def __init__(self, raw, out = sys.stdout):
                """ Store the source text. """

                self.raw = string.strip(string.expandtabs(raw))
                self.out = out


        def format(self):
                """ Parse and send the colorized source to output."""

                # Store line offsets in self.lines
                self.lines = [0, 0]
                pos = 0

                while 1:
                        pos = string.find(self.raw, '\n', pos) + 1
                        if not pos: break
                        self.lines.append(pos)

                self.lines.append(len(self.raw))
                    
                # Parse the source and write it
                self.pos = 0
                text = cStringIO.StringIO(self.raw)
                self.out.write('<pre><font face="Lucida,Courier New">')

                try:
                        tokenize.tokenize(text.readline, self) # self as handler callable

                except tokenize.TokenError, ex:
                        msg = ex[0]
                        line = ex[1][0]
                        self.out.write("<h3>ERROR: %s</h3>%s\n" % (msg, self.raw[self.lines[line]:]))
                self.out.write('</font></pre>')


        def __call__(self, toktype, toktext, (srow,scol),(erow,ecol), line):
                """ Token handler """

                if 0: # You may enable this for debugging purposes only
                        print "type", toktype, token.tok_name[toktype],"text", toktext,
                        print "start", srow,scol, "end", erow,ecol,"<br>"

                # Calculate new positions
                oldpos = self.pos
                newpos = self.lines[srow] + scol
                self.pos = newpos + len(toktext)

                # Handle newlines
                if toktype in [token.NEWLINE, tokenize.NL]:
                        self.out.write('\n')
                        return

                # Send the original whitespace, if needed
                if newpos > oldpos:
                        self.out.write(self.raw[oldpos:newpos])

                # Skip indenting tokens
                if toktype in [token.INDENT, token.DEDENT]:
                        self.pos = newpos
                        return

                # Map token type to a color group
                if token.LPAR <= toktype <= token.OP:
                        toktype = token.OP
                elif toktype == token.NAME and keyword.iskeyword(toktext):
                        toktype = _KEYWORD

                color = _colors.get(toktype, _colors[_TEXT])
                style = ''

                if toktype == token.ERRORTOKEN:
                        style = ' style=""'

                # Send text
                self.out.write('<font color="%s"%s>' % (color,style))
                self.out.write(cgi.escape(toktext))
                self.out.write('</font>')


if __name__ == "__main__":
        import os, sys
        print "Formatting..."

        # Open own source
        source = open('hello.py').read( )

        # Write colorized version to "python.html"
        Parser(source, open('python.html', 'wt')).format( )

        # Load HTML page into browser
        if os.name == "nt":
                os.system("explorer python.html")
        else:
                os.system("netscape python.html &")

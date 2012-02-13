#!/usr/bin/env python2
#
# A simple password keeper for the console
#
# Copyright (C) 2012 Tue Abrahamsen <tue.abrahamsen@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import os
import inspect
from subprocess import call
from ConfigParser import ConfigParser, NoSectionError
from getpass import getpass
import shlex

__VERSION__ = 0.1

DATABASE_UNENC = os.path.expanduser("~/Dropbox/database.fort")
DATABASE = DATABASE_UNENC+'.gpg'

class Database(object):

    def __init__(self, passphrase):
        self.dirty = False
        self.passphrase = passphrase

    def __enter__(self):
        if not os.path.exists(DATABASE) and not os.path.exists(DATABASE_UNENC):
            print "Database does not exist. Creating it..."
            fh = open(DATABASE_UNENC, 'w+')
            fh.close()
            self.dirty = True
        elif os.path.exists(DATABASE_UNENC):
            print "Database seems unencrypted. Attempting to encrypt..."
            call(['gpg', '-q', '--no-mdc-warning', '--passphrase', self.passphrase, '-c', DATABASE_UNENC])
        else:
            if not call(['gpg', '-q', '--no-mdc-warning', '--passphrase', self.passphrase, DATABASE]) == 0:
                sys.exit(1)
        self.cp = ConfigParser()
        self.cp.read(DATABASE_UNENC)
        return self

    def __exit__(self, *args):
        if self.dirty:
            self.cp.write(open(DATABASE_UNENC, 'w'))
            if os.path.exists(DATABASE):
                os.unlink(DATABASE)
            call(['gpg', '-q', '--no-mdc-warning', '--passphrase', self.passphrase, '-c', DATABASE_UNENC])
        if os.path.exists(DATABASE_UNENC):
            os.unlink(DATABASE_UNENC)

    def set(self, section, key, value):
        if not self.cp.has_section(section):
            self.cp.add_section(section)
        self.cp.set(section, key, value)
        self.dirty = True

    def get(self, section):
        try:
            return self.cp.items(section)
        except NoSectionError:
            return []

    def sections(self):
        return self.cp.sections()

    def delete(self, section, key):
        self.cp.remove_option(section, key)
        if not self.cp.items(section):
            self.cp.remove_section(section)
        self.dirty = True

class Fort(object):

    def __init__(self, db, shell=False):
        self.db = db
        self.shell = shell

        self.methods = {}
        for methodname in [n for n in dir(Fort) if not n.startswith('_')]:
            method = getattr(self, methodname)
            self.methods[methodname] = {
                'doc': method.__doc__,
                'args': [n.upper() for n in inspect.getargspec(method).args[1:]],
            }

    def _loop(self):
        cmd = []
        while not cmd or cmd[0] not in ['q', 'quit', 'x', 'exit']:
            if cmd:
                self._run(cmd[0], cmd[1:])
            try:
                cmd = shlex.split(raw_input("fort> ").strip())
            except ValueError, e:
                print " Error:", str(e)
                cmd = []

    def _run(self, command, args):
        if not command in self.methods.keys():
            print " Unknown command"
            return
        if not len(args) == len(self.methods[command]['args']):
            print " Usage: %s %s - %s" % (command, ' '.join(self.methods[command]['args']), self.methods[command]['doc'])
            return
        
        getattr(self, command)(*args)

    def list(self):
        """Show all entries"""
        print " Entries:"
        for section in self.db.sections():
            print " ", section

    def search(self, searchstring):
        """Search entries"""
        print " Filtered entries:"
        for section in [s for s in self.db.sections() if searchstring in s]:
            print " ", section

    def show(self, entry):
        """Show all information in an entry"""
        data = dict(self.db.get(entry))
        if not data:
            print " No such entry"
        else:
            maxl = max(len(n) for n in data.keys())
            print " Data in entry %s" % entry
            for k,v in data.iteritems():
                print ("  %%%ss: %%s" % maxl) % (k, v)

    def set(self, entry, key, value):
        """Set a key value"""
        self.db.set(entry, key, value)

    def delete(self, entry, key):
        """Delete a key"""
        if entry in self.db.sections():
            self.db.delete(entry, key)
        else:
            print " No such entry"

    def changepassword(self):
        """Change password"""
        pass1 = 1
        pass2 = 2
        while not pass1 == pass2:
            if pass1 != 1:
                print " Passwords does not match! Try again."
            pass1 = getpass(" New password: ")
            if not pass1:
                break
            pass2 = getpass(" New password again: ")
        if pass1 == pass2:
            self.db.passphrase = pass1
            self.db.dirty = True
        else:
            print " Password not changed!"

    def help(self):
        """Help"""
        strs = []
        for methodname, info in self.methods.iteritems():
            strs.append(("%s %s" % (methodname, ', '.join(info['args'])), info['doc']))
        maxlen = max(len(n[0]) for n in strs)
        for method in strs:
            print (" %%-%ss - %%s" % maxlen) % (method[0], method[1])

if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1] != 'shell':
        if (not len(sys.argv) > 1 or not sys.argv[1] in [n for n in dir(Fort) if not n.startswith('_')] or sys.argv[1] == 'help'):
            print "Usage:"
            strs = []
            for methodname, info in Fort(db=None).methods.iteritems(): 
                strs.append(("%s %s" % (methodname, ' '.join(info['args'])), info['doc']))
            maxlen = max(len(n[0]) for n in strs)
            for method in strs:
                print (" %s %%-%ss - %%s" % (sys.argv[0], maxlen)) % (method[0], method[1])
            sys.exit(1)

    passphrase = getpass()
    with Database(passphrase=passphrase) as db:
        do_shell = sys.argv[1] == 'shell'
        fort = Fort(db, shell=do_shell)
        if do_shell:
            try:
                fort._loop()
            except KeyboardInterrupt:
                pass # Exit quietly
        else:
            fort._run(sys.argv[1], sys.argv[2:])

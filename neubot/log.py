# neubot/log.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import logging
import traceback

from neubot.net.poller import POLLER

from neubot.database import DATABASE
from neubot.database import table_log
from neubot.notify import NOTIFIER

from neubot import system
from neubot import utils

def stderr_logger(severity, message):
    sys.stderr.write('<%s> %s\n' % (severity, message))

#
# We commit every NOCOMMIT log messages or when we see
# a WARNING or ERROR message (whichever of the two comes
# first).
#
NOCOMMIT = 32

#
# Interval in seconds between each invocation of the
# function that takes care of the logs saved into the
# database.
#
INTERVAL = 120

#
# This is the number of days of logs we keep into
# the database.  Older logs are pruned.
# TODO Allow to configure this.
#
DAYS_AGO = 7

class Logger(object):

    """Logging object.  Usually there should be just one instance
       of this class, accessible with the default logging object
       LOG.  We keep recent logs in the database in order to implement
       the /api/log API."""

    def __init__(self):
        self.logger = stderr_logger
        self.interactive = True
        self.noisy = False
        self.message = None
        self.ticks = 0

        self._nocommit = NOCOMMIT
        self._use_database = False
        self._queue = []

    #
    # Better not to touch the database when a test is in
    # progress, i.e. "testdone" is subscribed.
    # Maintenance consists mainly of removing old logs and
    # is mandatory because we don't want the database to grow
    # without control.
    #
    def _maintain_database(self, *args, **kwargs):

        POLLER.sched(INTERVAL, self._maintain_database)

        if (self._use_database and not NOTIFIER.is_subscribed("testdone")):
            self._writeback()

    #
    # We don't want to log into the database when we run
    # the server side or when we run from command line.
    #
    def use_database(self):
        POLLER.sched(INTERVAL, self._maintain_database)
        self._use_database = True

    def verbose(self):
        self.noisy = True

    def quiet(self):
        self.noisy = False

    def redirect(self):
        self.logger = system.get_background_logger()
        system.redirect_to_dev_null()
        self.interactive = False

    #
    # In some cases it makes sense to print progress during a
    # long operation, as follows::
    #
    #   Download in progress......... done
    #
    # This makes sense when: (i) the program is not running in
    # verbose mode; (ii) logs are directed to the stderr.
    # If the program is running in verbose mode, there might
    # be many messages between the 'in progress...' and 'done'.
    # And if the logs are not directed to stderr then it does
    # not make sense to print progress as well.
    # So, in these cases, the output will look like::
    #
    #   Download in progress...
    #    [here we might have many debug messages]
    #   Download complete.
    #
    def start(self, message):
        self.ticks = utils.ticks()
        if self.noisy or not self.interactive:
            self.info(message + " in progress...")
            self.message = message
        else:
            sys.stderr.write(message + "...")

    def progress(self, dot="."):
        if not self.noisy and self.interactive:
            sys.stderr.write(dot)

    def complete(self, done="done\n"):
        elapsed = utils.time_formatter(utils.ticks() - self.ticks)
        done = "".join([done.rstrip(), " [in ", elapsed, "]\n"])
        if self.noisy or not self.interactive:
            if not self.message:
                self.message = "???"
            self.info(self.message + "..." + done)
            self.message = None
        else:
            sys.stderr.write(done)

    # Log functions

    def exception(self, message="", func=None):
        if not func:
            func = self.error
        if message:
            func("EXCEPT: " + message + " (traceback follows)")
        for line in traceback.format_exc().split("\n"):
            func(line)

    def oops(self, message="", func=None):
        if not func:
            func = self.error
        if message:
            func("OOPS: " + message + " (traceback follows)")
        for line in traceback.format_stack()[:-1]:
            func(line)

    def error(self, message):
        self._log("ERROR", message)

    def warning(self, message):
        self._log("WARNING", message)

    def info(self, message):
        self._log("INFO", message)

    def debug(self, message):
        if self.noisy:
            self._log("DEBUG", message)

    def log_access(self, message):
        #
        # CAVEAT Currently Neubot do not update logs "in real
        # time" using AJAX.  If it did we would run in trouble
        # because each request for /api/log would generate a
        # new access log record.  A new access log record will
        # cause a new "logwritten" event.  And the result is
        # something like a Comet storm.
        #
        self._log("ACCESS", message)

    def __writeback(self):
        """Really commit pending log records into the database"""

        connection = DATABASE.connection()
        table_log.prune(connection, DAYS_AGO, commit=False)

        for record in self._queue:
            table_log.insert(connection, record, False)
        connection.commit()

        connection.execute("VACUUM;")
        connection.commit()

    def _writeback(self):
        """Commit pending log records into the database"""

        # At least do not crash
        try:
            self.__writeback()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # TODO write this exception to syslog
            pass

        # Purge the queue in any case
        del self._queue[:]

    def _log(self, severity, message):
        message = message.rstrip()

        if self._use_database and severity != "ACCESS":
            record = {
                      "timestamp": utils.timestamp(),
                      "severity": severity,
                      "message": message,
                     }

            #
            # We don't need to commit INFO and DEBUG
            # records: it's OK to see those with some
            # delay.  While we want to see immediately
            # WARNING and ERROR records.
            # TODO We need to commit the database on
            # sys.exit() and signals etc.  (This is
            # more a database problem that a problem
            # of this file.)
            #
            if severity in ("INFO", "DEBUG"):
                commit = False

                # Do we need to commit now?
                self._nocommit = self._nocommit -1
                if self._nocommit <= 0:
                    self._nocommit = NOCOMMIT
                    commit = True

            else:
                # Must commit now
                self._nocommit = NOCOMMIT
                commit = True

            self._queue.append(record)
            if commit:
                self._writeback()

        self.logger(severity, message)

    # Marshal

    def listify(self):
        if self._use_database:
            lst = table_log.listify(DATABASE.connection())
            lst.extend(self._queue)
            return lst
        else:
            return []

LOG = Logger()

#
# Neubot code should always use logging and we should
# eventually provide a backend for this subsystem.
# For now, the hack of the day is to override the names
# in the logging subsystem.
# To avoid a pylint warning ("Specify format string arguments
# as logging function parameters") I had to write the wrappers
# below.  The debug() method does not interpolate unless the
# logger is running verbose.  I like that design idea of logging,
# as I said, I should write my special-purpose backend for the
# logging module.
#

def _log_info(msg, *args):
    ''' Wrapper for info() '''
    LOG.info(msg % args)

def _log_error(msg, *args):
    ''' Wrapper for error() '''
    LOG.error(msg % args)

def _log_warning(msg, *args):
    ''' Wrapper for warning() '''
    LOG.warning(msg % args)

def _log_debug(msg, *args):
    ''' Wrapper for debug() '''
    if LOG.noisy:
        LOG.debug(msg % args)

logging.info = _log_info
logging.error = _log_error
logging.warning = _log_warning
logging.debug = _log_debug

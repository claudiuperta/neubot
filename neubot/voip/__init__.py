# neubot/raw.py

#
# Copyright (c) 2012
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

'''
 The main() of `neubot voip` subcommand.
'''

import getopt
import logging
import os
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')


from neubot.http.server import HTTP_SERVER
from neubot.net.poller import POLLER
from neubot.config import CONFIG
from neubot.log import oops
from neubot.notify import NOTIFIER
from neubot.main import common

from neubot import negotiate
from neubot import privacy
from neubot import runner_clnt
from neubot import utils

from neubot.voip import config

from neubot.database import DATABASE
from neubot.poller import POLLER
from neubot.negotiate import server_voip
from neubot.voip.client import ClientVoIP

from neubot import log
from neubot import privacy
from neubot import runner_clnt

def run(poller, conf):
    '''
     This function is invoked when the user wants
     to run precisely this module.
    '''

    config.finalize_conf(conf)
    conf = CONFIG.copy()
    config.finalize_conf(conf)

    if conf["voip.listen"]:

        #
        # If we need to negotiate and we're runing
        # standalone we also need to bring up the
        # global HTTP server.
        #
        if conf["voip.negotiate"]:
            HTTP_SERVER.configure(conf)
            HTTP_SERVER.listen((conf["voip.address"],
                               conf["voip.negotiate.port"]))
            conf["negotiate.listen"] = True
            negotiate.run(POLLER, conf)

    else:

        #
        # Make sure there is someone ready to receive the
        # "testdone" event.  If there is noone it is a bug
        # none times out of ten.
        #
        if not NOTIFIER.is_subscribed("testdone"):
            oops("The 'testdone' event is not subscribed")

        if conf["voip.negotiate"]:
            client = ClientVoIP(poller)
            client.configure(conf)

            #
            # The rendezvous client uses this hidden variable
            # to pass us the URI to connect() to (the rendezvous
            # returns an URI, not address and port).
            #
            uri = None
            if "voip._uri" in conf:
                uri = conf["voip._uri"]

            client.connect_uri(uri)

        else:
            client = ClientVoIP(poller)
            client.configure(conf)
            client.connect((conf["voip.address"],
                           conf["voip.port"]))


def main(args):
    '''
     This function is invoked when the user wants
     to run precisely this module.
    '''

    config.register_descriptions()
    common.main("voip", "Neubot VoIP module", args)
    conf = CONFIG.copy()
    config.finalize_conf(conf)

    if conf["voip.listen"]:

        #
        # If we need to negotiate and we're runing
        # standalone we also need to bring up the
        # global HTTP server.
        #
        if conf["voip.negotiate"]:
            HTTP_SERVER.configure(conf)
            HTTP_SERVER.listen((conf["voip.address"],
                               conf["voip.negotiate.port"]))
            conf["negotiate.listen"] = True
            negotiate.run(POLLER, conf)

    else:

        #
        # If possible use the runner, which will execute the
        # test in the context of the neubot daemon.  Then exit
        # to bypass the run() invokation that is below here.
        # If the runner fails, fallback to the usual code path,
        # which executes the test in the context of the local
        # process.
        # Set 'runned.enabled' to 0 to bypass the runner and
        # run the test locally.
        #
        if (utils.intify(conf['runner.enabled']) and
            runner_clnt.runner_client(conf["agent.api.address"],
                                      conf["agent.api.port"],
                                      CONFIG['verbose'],
                                      "voip")):
            sys.exit(0)

        logging.info('Will run the test in the local context...')

        if not privacy.allowed_to_run():
            privacy.complain()
            sys.exit(1)

        #
        # When we're connecting to a remote host to perform a test
        # we want Neubot to quit at the end of the test.  When this
        # happens the test code publishes the "testdone" event, so
        # here we prepare to intercept the event and break our main
        # loop.
        #
        NOTIFIER.subscribe("testdone", lambda event, ctx: POLLER.break_loop())

    run(POLLER, conf)

    POLLER.loop()

if __name__ == '__main__':
    main(sys.args)


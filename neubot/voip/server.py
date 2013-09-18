# neubot/voip/server.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

import StringIO
import cgi
import logging

from neubot.http.server import ServerHTTP
from neubot.http.server import HTTP_SERVER
from neubot.http.message import Message

from neubot.negotiate.server import NEGOTIATE_SERVER
from neubot.compat import json
from neubot import utils

class VoIPServer(ServerHTTP):
    ''' VoIP server  '''

    # Adapted from neubot/negotiate/server.py
    def got_request_headers(self, stream, request):
        ''' Decide whether we can accept this HTTP request '''
        isgood = (request['transfer-encoding'] == '' and
                  # Fix for old clients
                  (request['content-length'] == '' or
                   request.content_length() <= 1048576) and
                  # XXX wrong because the scope of the check is too broad
                  request.uri.startswith('/voip/'))
        return isgood

    def process_request(self, stream, request):
        ''' Dispatch and process the incoming HTTP request '''
        if request.uri.startswith('/voip/negotiate'):
            self.do_negotiate(stream, request)
        elif request.uri == '/voip/collect':
            self.do_collect(stream, request)
        else:
            raise RuntimeError('Invalid URI')

    def do_negotiate(self, stream, request):
        ''' Invoked on GET /voip/negotiate'''

        #request_body = json.loads(request.body)
        logging.info('<VoIP> %s', request.body)

        response_body = {
            'uuid': utils.get_uuid(),
            'voip_test': 'skype',
        }

        response = Message()
        response.compose(code='200', reason='Ok',
                         body=json.dumps(response_body),
                         keepalive=True,
                         mimetype='application/json')
        stream.send_response(request, response)

    def do_collect(self, stream, request):
        ''' Invoked on GET /voip/collect '''

        # TODO(claudiu)
        request.uri = '/collect/voip'

        message = {
            'uuid': '',
            'voip_test': 'skype',
        }
        # XXX Here we don't rewrite content-length which becomes bogus
        request['content-type'] = 'application/json'
        request.body = StringIO.StringIO(json.dumps(message))

        NEGOTIATE_SERVER.process_request(stream, request)

# No poller, so it cannot be used directly
VOIP_SERVER = VoIPServer(None)


#
# TODO I've added here the run() function for convenience,
# but this should actually be moved in speedtest/__init__.py
# in the future.
#
def run(poller, conf):
    ''' Start the server-side of the voip module '''

    HTTP_SERVER.register_child(VOIP_SERVER, '/voip/negotiate')
    HTTP_SERVER.register_child(VOIP_SERVER, '/voip/collect')

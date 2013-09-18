# neubot/raw_srvr_glue.py

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
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

'''
 Glue between skype_srvr.py and server-side negotiation.  Adds to skype_srvr.py
 access control capabilities.
'''

from neubot.negotiate.server_skype import NEGOTIATE_SERVER_SKYPE
from neubot.skype_srvr import SkypeServer

class SkypeServerEx(SkypeServer):
    ''' Negotiation-enabled SKYPE test server '''
    # Same-as SkypeServer but checks that the peer is authorized

    def filter_auth(self, stream, tmp):
        ''' Filter client auth '''
        if tmp not in NEGOTIATE_SERVER_SKYPE.clients:
            raise RuntimeError('skyoe_negotiate: unknown client')
        context = stream.opaque
        context.state = NEGOTIATE_SERVER_SKYPE.clients[tmp]

SKYPE_SERVER_EX = SkypeServerEx()

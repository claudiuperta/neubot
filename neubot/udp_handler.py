# neubot/udp_handler.py

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
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

''' Handles poller events '''

# Adapted from neubot/net/stream.py
# Python3-ready: yes

from neubot.connector import Connector
from neubot.listener import Listener

from neubot import utils_net

class UDPHandler(object):

    ''' Event handler '''

    def listen(self, endpoint, prefer_ipv6):
        pass

    def handle_listen_error(self, endpoint):
        pass

    def handle_listen(self, listener):
        pass

    def handle_listen_close(self, listener):
        pass

    def handle_accept(self, listener, sock):
        pass

    def handle_accept_error(self, listener):
        pass

    def connect(self, endpoint, prefer_ipv6):
        pass

    def handle_connect_error(self, connector):
        pass

    def handle_connect(self, connector, sock, rtt, extra):
        pass

    def handle_close(self, udp_stream):
        pass

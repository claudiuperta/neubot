# neubot/udp_stream.py

#
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

import collections
import errno
import socket
import sys
import types
import logging

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.log import oops
from neubot.net.poller import POLLER
from neubot.net.poller import Pollable

from neubot import utils
from neubot import utils_net

from neubot.main import common

# States returned by the socket model
STATES = [ SUCCESS, ERROR, WANT_READ, WANT_WRITE ] = range(4)

# Maximum amount of bytes we read from a socket
MAXBUF = 1 << 18

# Soft errors on sockets, i.e. we can retry later
SOFT_ERRORS = [ errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR ]

class UDPSocketWrapper(object):
    def __init__(self, local_address):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(local_address)
        except socket.error:
            logging.error('Exception', exc_info=1)

    def soclose(self):
        try:
            self.sock.close()
        except socket.error:
            logging.error('Exception', exc_info=1)

    def sorecv(self, maxlen):
        try:
            # Differently from the TCP stream, here we must
            # also return the remote address.
            # TODO (claudiu) Perform a check on the remote address
            octets, address = self.sock.recvfrom(maxlen)
            return SUCCESS, octets
        except socket.error, exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_READ, ""
            else:
                return ERROR, exception

    def sosend(self, datagram, address):
        try:
            count = self.sock.sendto(octets, address)
            return SUCCESS, count
        except socket.error, exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_WRITE, 0
            else:
                return ERROR, exception

class UDPStream(Pollable):
    '''Handles an UDP stream between two endpoints'''
    # This is different from the tcp Stream class
    # since we need to know the remote address.
    def __init__(self, local_address, remote_address):
        Pollable.__init__(self)
        # TODO(claudiu) Check that the address is well-formed.
        self.remote_address = remote_address

        self.sock = UDPSocketWrapper(local_address)
        self.filenum = -1
        self.myname = None
        self.peername = None
        self.logname = None
        self.eof = False

        self.close_complete = False
        self.close_pending = False
        self.recv_blocked = False
        self.recv_pending = False
        self.send_blocked = False
        self.send_octets = None
        self.send_queue = collections.deque()
        self.send_pending = False

        self.bytes_recv_tot = 0
        self.bytes_sent_tot = 0

        self.opaque = None
        self.atclosev = set()

    def __repr__(self):
        return "datagram %s" % self.logname

    def fileno(self):
        return self.filenum


    def close(self):
        self.close_pending = True
        if self.send_pending or self.close_complete:
            return
        self.poller.close(self)

    def handle_close(self):
        if self.close_complete:
            return

        self.close_complete = True

        self.connection_lost(None)
        self.parent.connection_lost(self)

        atclosev, self.atclosev = self.atclosev, set()
        for func in atclosev:
            try:
                func(self, None)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error("Error in atclosev", exc_info=1)

        self.send_octets = None
        self.sock.soclose()

    # Recv path

    def start_recv(self):
        if (self.close_complete or self.close_pending
          or self.recv_pending):
            return

        self.recv_pending = True

        if self.recv_blocked:
            return

        self.poller.set_readable(self)

    def handle_read(self):
        if self.recv_blocked:
            self.poller.set_writable(self)
            if not self.recv_pending:
                self.poller.unset_readable(self)
            self.recv_blocked = False
            self.handle_write()
            return

        status, octets = self.sock.sorecv(MAXBUF)
        # TODO(claudiu) Check that the address we're
        # receipting data matches self.remote_ddress

        if status == SUCCESS and octets:

            self.bytes_recv_tot += len(octets)
            self.recv_pending = False
            self.poller.unset_readable(self)

            self.recv_complete(octets)
            return

        if status == WANT_READ:
            return

        if status == WANT_WRITE:
            self.poller.unset_readable(self)
            self.poller.set_writable(self)
            self.send_blocked = True
            return

        if status == SUCCESS and not octets:
            self.eof = True
            self.poller.close(self)
            return

        if status == ERROR:
            # Here octets is the exception that occurred
            raise octets

        raise RuntimeError("Unexpected status value")

    def recv_complete(self, octets):
        pass

    # Send path

    def read_send_queue(self):
        octets = ""

        while self.send_queue:
            octets = self.send_queue[0]
            if isinstance(octets, basestring):
                # remove the piece in any case
                self.send_queue.popleft()
                if octets:
                    break
            else:
                octets = octets.read(MAXBUF)
                if octets:
                    break
                # remove the file-like when it is empty
                self.send_queue.popleft()

        if octets:
            if type(octets) == types.UnicodeType:
                oops("Received unicode input")
                octets = octets.encode("utf-8")

        return octets

    def start_send(self, octets):
        if self.close_complete or self.close_pending:
            return

        self.send_queue.append(octets)
        if self.send_pending:
            return

        self.send_octets = self.read_send_queue()
        if not self.send_octets:
            return

        self.send_pending = True

        if self.send_blocked:
            return

        self.poller.set_writable(self)

    def handle_write(self):
        if self.send_blocked:
            self.poller.set_readable(self)
            if not self.send_pending:
                self.poller.unset_writable(self)
            self.send_blocked = False
            self.handle_read()
            return

        status, count = self.sock.sosend(self.send_octets, self.remote_ddress)

        if status == SUCCESS and count > 0:
            self.bytes_sent_tot += count

            if count == len(self.send_octets):

                self.send_octets = self.read_send_queue()
                if self.send_octets:
                    return

                self.send_pending = False
                self.poller.unset_writable(self)

                self.send_complete()
                if self.close_pending:
                    self.poller.close(self)
                return

            if count < len(self.send_octets):
                self.send_octets = buffer(self.send_octets, count)
                self.poller.set_writable(self)
                return

            raise RuntimeError("Sent more than expected")

        if status == WANT_WRITE:
            return

        if status == WANT_READ:
            self.poller.unset_writable(self)
            self.poller.set_readable(self)
            self.recv_blocked = True
            return

        if status == ERROR:
            # Here count is the exception that occurred
            raise count

        if status == SUCCESS and count == 0:
            self.eof = True
            self.poller.close(self)
            return

        if status == SUCCESS and count < 0:
            raise RuntimeError("Unexpected count value")

        raise RuntimeError("Unexpected status value")

    def send_complete(self):
        pass

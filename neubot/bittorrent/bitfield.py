# neubot/bittorrent/bitfield.py

#
# The contents of this file are subject to the Python Software Foundation
# License Version 2.3 (the License).  You may not copy or use this file, in
# either source code or executable form, except in compliance with the License.
# You may obtain a copy of the License at http://www.python.org/license.
#
# Software distributed under the License is distributed on an AS IS basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License
# for the specific language governing rights and limitations under the
# License.
#
# Written by Bram Cohen, Uoti Urpala, and John Hoffman
# Modified for neubot by Simone Basso <bassosimone@gmail.com>
#

import array
import random

counts = []
for i in xrange(256):
    t = 0
    for j in xrange(8):
        t = t + ((i >> j) & 1)
    counts.append(chr(t))
counts = ''.join(counts)

class Bitfield(object):
    def __init__(self, length, bitstring=None):
        self.length = length
        rlen, extra = divmod(length, 8)
        if bitstring is None:
            self.numfalse = length
            if extra:
                self.bits = array.array('B', chr(0) * (rlen + 1))
            else:
                self.bits = array.array('B', chr(0) * rlen)
        else:
            if extra:
                if len(bitstring) != rlen + 1:
                    raise ValueError("%s != %s" % (len(bitstring), rlen + 1))
                if (ord(bitstring[-1]) << extra) & 0xFF != 0:
                    raise ValueError("%s != %s" %
                                     ((ord(bitstring[-1]) << extra) & 0xFF, 0))
            else:
                if len(bitstring) != rlen:
                    raise ValueError("%s != %s" % (len(bitstring), rlen))
            self.numfalse = length - sum(array.array('B',
              bitstring.translate(counts)))
            if self.numfalse != 0:
                self.bits = array.array('B', bitstring)
            else:
                self.bits = None

    def __setitem__(self, index, val):
        assert val
        pos = index >> 3
        mask = 128 >> (index & 7)
        if self.bits[pos] & mask:
            return
        self.bits[pos] = self.bits[pos] | mask
        self.numfalse = self.numfalse - 1
        if self.numfalse == 0:
            self.bits = None

    def __getitem__(self, index):
        bits = self.bits
        if bits is None:
            return 1
        return bits[index >> 3] & 128 >> (index & 7)

    def __len__(self):
        return self.length

    def tostring(self):
        if self.bits is None:
            rlen, extra = divmod(self.length, 8)
            r = chr(0xFF) * rlen
            if extra:
                r = r + chr((0xFF << (8 - extra)) & 0xFF)
            return r
        else:
            return self.bits.tostring()

    def __getstate__(self):
        d = {}
        d['length'] = self.length
        d['s'] = self.tostring()
        return d

    def __setstate__(self, d):
        Bitfield.__init__(self, d['length'], d['s'])

def make_bitfield(numpieces):
    bitfield = Bitfield(numpieces)
    length = len(bitfield.bits)
    for idx in random.sample(range(length), int(length/2)):
        bitfield.bits[idx] = 255
    return bitfield

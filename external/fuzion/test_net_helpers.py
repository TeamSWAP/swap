#
# Copyright 2013 Fuzion
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import hashlib
import random

import net_helpers

def assertEq(a, b):
    if a == b:
        return
    print "ASSERTION FAILED!", a, "!=", b
    exit()

if __name__ == '__main__':
    packer = net_helpers.Packer()
    packets = []
    for i in range(1, 1024):
        packets.append(hashlib.md5(str(random.random())).hexdigest())
    stream = ""
    for p in packets:
        stream += packer.pack(p)
    def testPacker(x):
        packer = net_helpers.Packer()
        last = 0
        for i in range(0, len(stream), x):
            #print stream[last:last+x]
            packer.read(stream[last:last+x])
            last += x
        for i in range(0, len(packets)):
            assertEq(packer.popPacket(), packets[i])
    for i in range(1, 1024):
        print "TESTING %d..."%i,
        testPacker(i)
        print "OK"
    print "PASSED"

"""
   OpenWiMesh - Framework for Software Defined Wireless Mesh Networks
   Copyright (C) 2013-2014  GRADE - http://grade.dcc.ufba.br

   This file is part of OpenWiMesh.

   OpenWiMesh is free software: you can redistribute it and/or modify
   it under the terms of the GNU Affero General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   OpenWiMesh is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU Affero General Public License
   along with OpenWiMesh.  If not, see <http://www.gnu.org/licenses/>.

   Linking this library statically or dynamically with other modules is
   making a combined work based on this library.  Thus, the terms and
   conditions of the GNU Affero General Public License cover the whole
   combination.

   As a special exception, the copyright holders of this library give you
   permission to link this library with independent modules to produce an
   executable, regardless of the license terms of these independent
   modules, and to copy and distribute the resulting executable under
   terms of your choice, provided that you also meet, for each linked
   independent module, the terms and conditions of the license of that
   module.  An independent module is a module which is not derived from
   or based on this library.  If you modify this library, you may extend
   this exception to your version of the library, but you are not
   obligated to do so.  If you do not wish to do so, delete this
   exception statement from your version.
"""

class ACL():
    def __init__(self, default=True):
        self.default = default
        try:
            from acl_defs import BLACKLIST, WHITELIST
        except ImportError:
            BLACKLIST = {}
            WHITELIST = {}
        self.blacklist = BLACKLIST
        self.whitelist = WHITELIST

    def _add(self, acl_lists, receiver, sender, duplex=False):
        receiver = receiver.lower()
        sender = sender.lower()
        acl = acl_lists.get(receiver, [])
        if sender not in acl:
            acl.append(sender)
            acl_lists[receiver] = acl
        if duplex:
            self._add(acl_lists=acl_lists, receiver=sender, sender=receiver)

    def add_blacklist(self, receiver, sender, duplex=False):
        self._add(acl_lists=self.blacklist, receiver=receiver, sender=sender,
                duplex=duplex)

    def add_whitelist(self, receiver, sender, duplex=False):
        self._add(acl_lists=self.whitelist, receiver=receiver, sender=sender,
                duplex=duplex)

    def is_allowed(self, receiver, sender):
        if receiver is not None:
            receiver = receiver.lower()
        else:
            return False
        sender = sender.lower()
        if receiver in self.whitelist:
            whitelist = self.whitelist.get(receiver, [])
            return sender in whitelist
        elif receiver in self.blacklist:
            blacklist = self.blacklist.get(receiver, [])
            return sender not in blacklist
        else:
            return self.default


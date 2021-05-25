#!/usr/bin/python

# gen_niflib.py
#
# This script generates C++ code for Niflib.
#
# --------------------------------------------------------------------------
# Command line options
#
# -p /path/to/niflib : specifies the path where niflib can be found 
#
# -b : enable bootstrap mode (generates templates)
# 
# -i : do NOT generate implmentation; place all code in defines.h
#
# -a : generate accessors for data in classes
#
# -n <block>: generate only files which match the specified name
#
# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2005, NIF File Format Library and Tools
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****
# --------------------------------------------------------------------------

from nifxml import *
from distutils.dir_util import mkpath
import os
from os.path import join
import hashlib
import itertools

#
# global data
#

ROOT_DIR = r"c:\oss\SharpNif\SharpNif\Generated"

CTYPES = {'unsigned int': "uint",
          "unsigned short": "ushort",
          "Ref": "NiObject",
          "*": "Ptr",
          #"string": "NiString"
          }

def ctype(name):
    return CTYPES.get(name, name)



def generate_enums(is_flags):
    for enum in flag_types.itervalues() if is_flags else enum_types.itervalues():
        print("Generating %s" % (enum.name,))

        cf = CFile(join(ROOT_DIR, "Flags" if is_flags else "Enums", enum.cname + ".cs"), "w")

        cf.code("using System;")
        cf.code("namespace SharpNif")
        cf.code("{")

        if is_flags:
            cf.code("[Flags]")
        cf.code("public enum %s : %s" % (enum.cname, enum.storage))
        cf.code("{")

        for o in enum.options:
            cf.code("%s = %s," % (o.cname, o.value))

        cf.code("}")

        cf.code("public partial class NifReader")
        cf.code("{")
        cf.code("public void Read(ref %s data)" % (enum.cname,))
        cf.code("{")

        cf.code("%s tmp = default;" % (enum.storage,))
        cf.code("Read(ref tmp);")
        cf.code("data = (%s)tmp;" % (enum.cname,))

        cf.code("}")
        cf.code("}")

        cf.code("}")


def write_member_definitions(cf, block):
    for member in block.members:
        if member.is_duplicate:
            continue
        if member.arr1.lhs:
            if member.ctemplate:
                cf.code("internal %s<%s>[] _%s;" % (member.ctype, member.ctemplate, member.cname))
            else:
                cf.code("internal %s[] _%s;" % (member.ctype, member.cname))
        else:
            cf.code("internal %s _%s;" % (member.ctype, member.cname))

def write_io_overrides(cf, block):

    cf.code("public partial class NifReader")
    cf.code("{")

    if block.template:
        cf.code("public void Read<T>(ref %s<T> data)" % (block.cname,))
    else:
        cf.code("public void Read(ref %s data)" % (block.cname,))

    cf.code("{")

    def name_filter(s):
        if (s.isdigit()):
            return s
        return "data._" + member_name(s)

    if hasattr(block, "inherit") and block.inherit:
        cf.code("var parent = (%s)data;" % (block.inherit.cname,))
        cf.code("Read(ref parent);")
        cf.code("")

    for member in block.members:
        if member.arr1.lhs:
            if member.ctemplate:
                cf.code("data._%s = new %s<%s>[%s];" % (member.cname, member.ctype, member.ctemplate, member.arr1.code(name_filter=name_filter)))
            else:
                cf.code("data._%s = new %s[%s];" % (member.cname, member.ctype, member.arr1.code(name_filter=name_filter)))
            cf.code("for (var idx = 0; idx < %s; idx ++) Read(ref data._%s[idx]);" % (member.arr1.code(name_filter=name_filter), member.cname))
        elif member.ctype == "T":
            cf.code("Read<T>(ref data._%s);" % (member.cname,))
        else:
            cf.code("Read(ref data._%s);" % (member.cname,))
            cf.code("")

    cf.code("}")
    cf.code("}")

def generate_compounds():
    for compound in compound_types.itervalues():
        print("Generating Compound %s" % (compound.cname,))

        cf = CFile(join(ROOT_DIR, "Compounds", compound.cname + ".cs"), "w")

        cf.code("using System;")
        cf.code("namespace SharpNif")
        cf.code("{")

        if compound.template:
            cf.code("public struct %s<T>" % (compound.cname,))
        else:
            cf.code("public struct %s" % (compound.cname,))

        cf.code("{")

        write_member_definitions(cf, compound)

        cf.code("}")

        write_io_overrides(cf, compound)

        cf.code("}")

def generate_blocks():
    for block in block_types.itervalues():
        print("Generating Block %s" % (block.cname,))

        cf = CFile(join(ROOT_DIR, "Blocks", block.cname + ".cs"), "w")

        cf.code("using System;")
        cf.code("namespace SharpNif")
        cf.code("{")

        if block.inherit:
            cf.code("public class %s : %s" % (block.cname, block.inherit.cname))
        else:
            cf.code("public class %s" % (block.cname,))
        cf.code("{")

        write_member_definitions(cf, block)

        cf.code("}")

        write_io_overrides(cf, block);

        cf.code("}")


for blk in itertools.chain(block_types.itervalues(), compound_types.itervalues()):
    blk.cname = ctype(blk.cname)

    for member in blk.members:
        member.ctype = ctype(member.ctype)

for enum in itertools.chain(enum_types.itervalues(), flag_types.itervalues()):
    enum.storage = ctype(enum.storage)

generate_enums(True)
generate_enums(False)
generate_compounds()
generate_blocks()


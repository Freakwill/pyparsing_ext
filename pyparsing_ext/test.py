#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import pyparsing as pp
import pyparsing_ext as ppx


w = ppx.Wordx(lambda x: x in {'a', 'b', 'c', 'd'})
M = ppx.delimitedMatrix(w, ch1=' ', ch2=pp.Regex('\n+').leaveWhitespace())
p = M.parseString('a b\nc d')
print(p.asList())

s = '''[1]hehe
[2]hehe'''
print(ppx.enumeratedItems().parseString(s))
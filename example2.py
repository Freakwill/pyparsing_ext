#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import pyparsing as pp

from pyparsing_ext import *
from pyparsing_ext.pylang import *

# grammar
opTable = arithOpTable
OPUNC = pp.Word('$', '0123456789+-*/^&%<>=@!~:')
opTable.append({'token':OPUNC})

smallGrammar = ProgrammingGrammarParser(keywords=commonKeywords, 
    constants=[{'token':NUMBER, 'action':NumberAction}, {'token':STRING, 'action':StringAction}, {'token':pp.oneOf('True False'), 'action':BooleAction}], variables = [{'token':IDEN, 'action':VariableAction}], 
    operators=opTable, functions=[{'token':IDEN('function'), 'action':FunctionAction}, {'token':(PUNC('left'), PUNC('right')), 'action':BifixAction}])

# semantics
bifixDict = {('|', '|'): abs, ('[', '_]'): math.floor, ('[', '^]'): math.ceil}
smallDict = arithDict; smallDict.update(bifixDict)
pydict = {'len':len, 'abs':abs, 'min':min, 'max':max,'str':str,'sum':sum, 'tuple':tuple, 'any':any, 'all':all, 'tuple':tuple, 'list':list, 'dict':dict, 'int':int}
smallDict.update(pydict)

# language
smallpyLanguage = ProgrammingLanguage(name="SmallPython", grammar=smallGrammar, calculator=Calculator(dict_=smallDict))


file = 'test.txt'
print('parse source file:\n', file, '\nresult:')
smallpyLanguage.executeFile(file)
print('see the dictionary of variables:')
print(smallpyLanguage.calculator.context)

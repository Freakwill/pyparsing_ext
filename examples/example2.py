#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import pyparsing as pp

from pyparsing_ext import *
from pyparsing_ext.pylang import *

# grammar
opTable = arithOpTable
OPUNC = pp.Word('$~', '0123456789+-*/^&%<>=@!~:')
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
smallpyLanguage = ProgrammingLanguage(name="SmallPython", grammar=smallGrammar, calculator=Calculator(dictionary=smallDict))
smallpyLanguage.info = {
            'version': '0.0',
            'paths': [],
            'suffix': '.spy'}

file = 'test'
print(f'Parse source file:\n{file}{smallpyLanguage.info["suffix"]}\nresult:')
smallpyLanguage.executeFile(file)
print('The dictionary of variables:')
print(smallpyLanguage.calculator.context)


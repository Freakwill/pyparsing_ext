#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import math

from pyparsing_ext.pylang import *

bifixDict = {('|', '|'): abs, ('[', '_]'): math.floor, ('[', '^]'): math.ceil}
arithGrammar = GrammarParser(constants = [{'token':NUMBER, 'action':NumberAction}], variables = [{'token':IDEN, 'action':VariableAction}], operators=arithOpTable)
arithGrammar.functions.extend([{'token':('|', '|'),'arity':1, 'action':BifixAction}, {'token':('[', ']+'),'arity':1, 'action':BifixAction}, {'token':('[', ']-'),'arity':1, 'action':BifixAction}])
microDict = arithDict; microDict.update(bifixDict)
arithLanguage = Language(grammar=arithGrammar, calculator=Calculator(dict_=microDict))

arithLanguage.parse('x=1;')
print(arithLanguage.grammar.parse('1'))
print(arithLanguage.calculator.context)


microGrammar = ProgrammingGrammarParser(keywords=commonKeywords, constants = [{'token':NUMBER, 'action':NumberAction}, {'token':STRING, 'action':StringAction}, {'token':pp.oneOf('True False'), 'action':BoolAction}], variables = [{'token':IDEN, 'action':VariableAction}], operators=arithOpTable, functions=[{'token':IDEN('function'), 'action':FunctionAction}, {'token':(PUNC('left'), PUNC('right')), 'action':BifixAction}])
pydict = {'len':len, 'abs':abs, 'min':min, 'max':max,'str':str,'sum':sum, 'tuple':tuple, 'any':any, 'all':all, 'tuple':tuple, 'list':list, 'dict':dict, 'int':int}
microDict.update(pydict)
smallpyLanguage = ProgrammingLanguage(name="SmallPython", grammar=microGrammar, calculator=Calculator(dict_=microDict))

smallpyLanguage.parse('x=1;')
print(smallpyLanguage.grammar.parse('x=1;'))
smallpyLanguage('x=1;')
print(smallpyLanguage.calculator.context)
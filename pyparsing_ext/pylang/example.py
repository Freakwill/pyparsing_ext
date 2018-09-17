#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import math

from pyparsing_ext.pylang import *

bifixDict = {('|', '|'): abs, ('[', '_]'): math.floor, ('[', '^]'): math.ceil}
arithGrammar = GrammarParser(constants = [{'token':NUMBER, 'action':NumberAction}], variables = [{'token':IDEN, 'action':VariableAction}], operators=arithOpTable)
arithGrammar.functions.extend([{'token':('|', '|'),'arity':1, 'action':BifixAction}, {'token':('[', ']+'),'arity':1, 'action':BifixAction}, {'token':('[', ']-'),'arity':1, 'action':BifixAction}])
microDict = arithDict; microDict.update(bifixDict)
arithLanguage = Language(grammar=arithGrammar, calculator=Calculator(dict_=microDict))


print('Example 1:')
print('|-1| ->', arithLanguage.grammar.parse('|-1|'))



microGrammar = ProgrammingGrammarParser(keywords=commonKeywords, constants = [{'token':NUMBER, 'action':NumberAction}, {'token':STRING, 'action':StringAction}, {'token':pp.oneOf('True False'), 'action':BooleAction}], variables = [{'token':IDEN, 'action':VariableAction}], operators=arithOpTable, functions=[{'token':IDEN('function'), 'action':FunctionAction}, {'token':(PUNC('left'), PUNC('right')), 'action':BifixAction}])
pydict = {'len':len, 'abs':abs, 'min':min, 'max':max,'str':str,'sum':sum, 'tuple':tuple, 'any':any, 'all':all, 'tuple':tuple, 'list':list, 'dict':dict, 'int':int}
microDict.update(pydict)
smallpyLanguage = ProgrammingLanguage(name="SmallPython", grammar=microGrammar, calculator=Calculator(dict_=microDict))

print('Example 2:')
code = 'x=|-1|;\ny=x*2;'
print('parse:\n', code, '\nresult:')
smallpyLanguage(code)
print(smallpyLanguage.calculator.context)
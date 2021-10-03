#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import pyparsing as pp

from pyparsing_ext import *
from pyparsing_ext.pylang import *

# configuration
# syntax
arithSyntax = StandardParser(constants = [{'token':NUMBER, 'action':NumberAction}], variables = [{'token':IDEN, 'action':VariableAction}], operators=arithOpTable)
arithSyntax.functions.extend([{'token':('|', '|'),'arity':1, 'action':BifixAction}, {'token':('[', ']+'),'arity':1, 'action':BifixAction}, {'token':('[', ']-'),'arity':1, 'action':BifixAction}])

# semantics
bifixDict = {('|', '|'): abs, ('[', '_]'): math.floor, ('[', '^]'): math.ceil}
microDict = arithDict; microDict.update(bifixDict)

arithLanguage = Language(parser=arithSyntax, calculator=StandardCalculator(dictionary=microDict))

print(f"""Simple example:')

|-1| ->{arithLanguage.parse('|-1|')}
""")

print('Complicated example:')

# syntax
opTable = arithOpTable
OPUNC = pp.Word('$', '0123456789+-*/^&%<>=@!~:')
opTable.append({'token':OPUNC})

microSyntax = ProgrammingParser(
    keywords=commonKeywords, 
    constants=[{'token':NUMBER, 'action':NumberAction}, {'token':STRING, 'action':StringAction}, {'token':pp.oneOf('True False'), 'action':BooleAction}],
    variables=[{'token':IDEN, 'action':VariableAction}], 
    operators=opTable,
    functions=[{'token':IDEN('function'), 'action':FunctionAction}, {'token':(PUNC('left'), PUNC('right')), 'action':BifixAction}]
    )

# semantics
pydict = {'len':len, 'abs':abs, 'min':min, 'max':max,'str':str,'sum':sum, 'tuple':tuple, 'any':any, 'all':all, 'tuple':tuple, 'list':list, 'dict':dict, 'int':int}
microDict.update(pydict)

smallpyLanguage = ProgrammingLanguage(name="SmallPython", parser=microSyntax, calculator=StandardCalculator(dictionary=microDict))

if __name__ == '__main__':
    
    code = '''
    def x $ y=1 {
    z=x+y*2;
    return z;
    }

    print (-1 $ -2) < 3; # 3 < 3 is False
    '''
    print('parse source code:\n', code, '\nresult:')
    smallpyLanguage(code)
    print('see the dictionary of variables:')
    print(smallpyLanguage.calculator.context)



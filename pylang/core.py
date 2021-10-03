# -*- coding: utf-8 -*-
"""pyplang (make a language with pyparsing)

Application: text parsing
Require: pyparsing
-------------------------------
Path:
Author: William
"""

import operator
import copy

import pyparsing as pp

from pyparsing_ext import *

class Memory(dict):
    pass

# Languages


class BaseCalculator:
    """Base class for semantic calculator

    A semantic calculator could evaluate constants and variables in the language
    """
    def __init__(self, dictionary={}, context={}):
        """
        Keyword Arguments:
            dictionary {dict} -- semantic dictionary, interpretation of contexts (default: {{}})
            context {dict} -- evaluation of variables (default: {{}})
        """
        self.dictionary = dictionary
        self.context = context

        def __str__(self):
            return f"""
    Dictionary: 
        {self.dictionary}
    Context: 
        {self.context}"""

    def reset(self):
        self.context = {}

    def __getitem__(self, x):
        if x in self.dictionary:
            return self.dictionary[x]
        elif x in self.context:
            return self.context[x]
        else:
            raise NameError('I did not find `%s` in the dictionaries, you may not define it in advance.' % x)

    def __setitem__(self, x, v):
        if x in self.dictionary:
            raise Exception(f'{x} is a constant, whose value could not be changed!')
        self.context[x] = v

    def update(self, x_v):
        self.context.update(x_v)

    def copy(self):
        return self.__class__(self.dictionary, self.context.copy())

    def __enter__(self):
        return self.copy()

    def __exit__(self, *args, **kwargs):
        return True


class StandardCalculator(BaseCalculator):
    """Semantic calculator with control information

    Inherite this class to define the semantics of programming language
    """

    def __init__(self, dictionary={}, context={}, control=None):
        """
        Keyword Arguments:
            dictionary {dict} -- semantic dictionary, interpretation of contexts (default: {{}})
            context {dict} -- evaluation of variables (default: {{}})
            control {[type]} -- control information (default: {None})
        """
        super().__init__(dictionary, context)
        self.control = control
        self.maxloop = 5000
        self.useBuiltins = False

    def copy(self):
        return self.__class__(self.dictionary, self.context.copy(), self.control)

    def reset(self):
        super().reset()
        self.control = None

    def __call__(self, t, *args, **kwargs):
        """Get the value of t
        
        Arguments:
            t {str} -- term
            *args {} -- parameters
        
        Returns:
            value of t
        
        Raises:
            Exception -- [description]
            NameError -- [description]
        """
        arity = len(args) + len(kwargs)
        if t in self.context:
            v = self.context[t]
            if arity == 0:
                return v
            else:
                if isinstance(v, dict):
                    if arity in v:
                        return v[arity](*args, **kwargs)
                    else:
                        raise Exception('Notice the arity!')
                else:
                    return v(*args, **kwargs)
        elif t in self.dictionary:
            v = self.dictionary[t]
            if arity == 0:
                if isinstance(v, dict):
                    return v[2]
                else:
                    return v
            else:
                if isinstance(v, dict):
                    if arity in v:
                        return v[arity](*args, **kwargs)
                    else:
                        raise Exception('notice the arity!')
                else:
                    return v(*args, **kwargs)
        else:
            if self.useBuiltins:
                return eval(t)(*args, **kwargs)
            raise NameError('Did not find %s' % t)

    def eval(self, parseResult):
        pass

    def execute(self, parseResult):
        pass

    def __setstate__(self, state):
        self.dictionary, self.context, self.control = state['dictionary'], state['context'], state['control']

    def __getstate__(self):
        return {'dictionary': self.dictionary, 'context': self.context, 'control': self. control}


def _token(s):
    return pp.Literal(s) if isinstance(s, str) else s

class BaseParser:
    """ Base class for syntax parser
    
    Users must define `make` in subclass
    """
    expression = None

    def make(self, *args, **kwargs):
        raise NotImplementedError('define method `make` to create a parser based on pyparsing')
    
    def parse(self, s):
        if self.expression is None:
            self.make()
        return self.expression.parseString(s)[0]

    def matches(self, s):
        if self.expression is None:
            self.make()
        return self.expression.matches(s)

    def parseFile(self, filename):
        with open(filename, 'r') as fo:
            return self.parse(fo.read())

    def kill(self):
        self.expression = None


class StandardParser(BaseParser):
    '''Standard class for Syntax Parser
    '''
    def __init__(self, keywords={}, constants=[], variables=[], functions=None, operators=[]):
        '''Create Syntax Parser
        
        Arguments:
            keywords {dict of tokens} -- set of keywords
            constants {[tokens]} -- set of constants of a language
        
        Keyword Arguments:
            variables {[tokens]} -- valid expressions of variables of a language (default: {[]})
            functions {[tokens]} -- builtin functions of a language (default: {None})
            operators {[tokens]} -- operators of a language (default: {[]})
        '''
        self.keywords = keywords
        self.constants = constants
        self.variables = variables
        if functions is None:
            self.functions = [{'token':IDEN, 'action':FunctionAction}]
        else:
            self.functions = functions
        self.operators = operators

    def make(self, enablePackrat=True):
        self.constant = pp.MatchFirst([constant['token'].setParseAction(constant.get('action', ConstantAction)) for constant in self.constants])
        if self.variables:
            self.variable = pp.MatchFirst([variable['token'].setParseAction(variable.get('action', VariableAction)) for variable in self.variables])
            baseExpr = self.constant | self.variable
        else:
            self.variable = None
            baseExpr = self.constant

        EXP = pp.Forward()
        funcExpr = []
        unpackExpr = pp.Suppress('*') + EXP('content')
        unpackExpr.setParseAction(UnpackAction)
        for function in self.functions:
            if isinstance(function['token'], tuple) and len(function['token'])==2:
                # bifixNotation
                left, right = _token(function['token'][0]), _token(function['token'][1])
                if 'arity' in function:
                    if function['arity'] == 1:
                        funcExpr.append((left('left') + EXP('arg') +right('right')).setParseAction(function['action']))
                    else:
                        funcExpr.append((left('left') + ((EXP + COMMA) * (function['arity']-1) + EXP)('args') + right('right')).setParseAction(function['action']))
                else:
                    funcExpr.append((left('left') + pp.delimitedList(EXP)('args') +right('right')).setParseAction(function['action']))
            else:
                if isinstance(function['token'], str):
                    function['token'] = pp.Literal(function['token'])
                if 'arity' in function:
                    if function['arity'] == 1:
                        funcExpr.append((function['token']('function') + LPAREN + EXP('arg') + RPAREN).setParseAction(function['action']))
                    else:
                        funcExpr.append((function['token']('function') + LPAREN + ((EXP + COMMA) * (function['arity']-1) + EXP)('args') + RPAREN).setParseAction(function['action']))
                else:
                    funcExpr.append((function['token']('function') + LPAREN + pp.delimitedList(EXP)('args') + RPAREN).setParseAction(function['action']))
        funcExpr = pp.MatchFirst(funcExpr)

        tupleExpr = tupleExpression(EXP)('args')
        tupleExpr.setParseAction(TupleAction)
        # dictExpr = LBRACE + pp.ZeroOrMore(EXP('key') + COLON + EXP('value')) + RBRACE
        # dictExpr.setParseAction(DictAction)
    
        M = funcExpr | tupleExpr | baseExpr | LPAREN + EXP + RPAREN
        indexExpr = M('variable') + pp.OneOrMore(LBRACK + EXP + RBRACK)('index')
        indexExpr.setParseAction(IndexAction)
        EXP <<= pp.infixNotation(indexExpr | M, optable2oplist(self.operators))
        self.expression = EXP
        self.tupleExpr = tupleExpr
        # self.dictExpr = dictExpr
        if enablePackrat:
            self.expression.enablePackrat()
        # EXP = mixedExpression(baseExpr, funcExpr, flag=True, opList=optable2oplist(self.operators))

    @property
    def nakeTupleExpr(self):
        tupleExpr = (self.expression + COMMA + pp.delimitedList(self.expression) + pp.Optional(COMMA) | pp.Group(self.expression + COMMA))('args')
        tupleExpr.setParseAction(TupleAction)
        return tupleExpr

    def enableLambda(self, sep=pp.Suppress(':')):
        lambdaExpr = pp.Keyword('lambda') + pp.delimitedList(variable)('args') + sep + EXP('expression')
        self.functions.append({'token':lambdaExpr, 'action':LambdaAction})
        return self

    def enableLet(self, sep=pp.Suppress(':')):
        letExpr = pp.Keyword('let') + pp.delimitedList(variable + pp.Suppress('=') + EXP)('arg_vals')  + sep + EXP('expression')
        self.functions.append({'token':letExpr, 'action':LetAction})
        return self

    def __setstate__(self, state):
        self.keywords, self.constants, self.variables, self.functions, self.operators =\
         state['keywords'], state['constants'], state['variables'], state['functions'], state['operators']


class Language:
    '''Language
    a language contains two parts syntax parser and semantic calculator
    '''
    def __init__(self, name='Toy', parser=None, calculator=None):
        self.name = name
        self.parser = parser
        self.calculator = calculator

    def __str__(self):
        return 'Language <%s>' % self.name

    def make_parser(self):
        self.parser.make()

    def matches(self, s):
        return self.parser.matches(s)

    def parse(self, s):
        return self.parser.parse(s)

    def parseFile(self, filename):
        return self.parser.parseFile(filename)

    def eval(self, s):
        return self.parse(s).eval(calculator=self.calculator)

    def __call__(self, s):
        return self.eval(s)

    def __setstate__(self, state):
        self.name, self.parser, self.calculator = state['name'], state['parser'], state['calculator']

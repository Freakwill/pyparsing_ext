# -*- coding: utf-8 -*-
'''pyplang (make a language with pyparsing)

Application: text parsing
Require: pyparsing
-------------------------------
Path:
Author: William
'''

import operator

import pyparsing as pp

from pyparsing_ext import *

# Languages
class Calculator:
    """Semantic calculator
    """

    def __init__(self, dict_={}, context={}, control=None):
        """
        Keyword Arguments:
            dict_ {dict} -- semantic dictionary, interpretation of contexts (default: {{}})
            context {dict} -- evaluation of variables (default: {{}})
            control {[type]} -- control information (default: {None})
        """
        self.dict_ = dict_
        self.context = context
        self.control = control
        self.maxloop = 5000

    def copy(self):
        return Calculator(self.dict_, self.context.copy(), self.control)

    def reset(self):
        self.context = {}
        self.control = None

    def update(self, x_v):
        self.context.update(x_v)

    def __getitem__(self, x):
        if x in self.context:
            return self.context[x]
        elif x in self.dict_:
            return self.dict_[x]
        else:
            raise NameError('Did not find %s' % x)

    def __enter__(self):
        return self.copy()

    def __exit__(self, *args, **kwargs):
        return True

    def __call__(self, t, *args, **kwargs):
        """Get the value of c
        
        Arguments:
            t {str} -- term
            *args {} -- parameters
        
        Returns:
            [type] -- [description]
        
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
        elif t in self.dict_:
            v = self.dict_[t]
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
            raise NameError('Did not find %s' % t)

    def eval(self, parseResult):
        pass

    def execute(self, parseResult):
        pass

    def __setstate__(self, state):
        self.dict_, self.context, self.control = state['dict_'], state['context'], state['control']


class GrammarParser:
    '''Grammar Parser
    parse a string to a tree-like structure (wrapped by Actions)
    '''
    def __init__(self, keywords={}, constants=[], variables=[], functions=None, operators=[]):
        '''
        
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

    def make_parser(self):
        self.constant = pp.MatchFirst([constant['token'].setParseAction(constant.get('action', ConstantAction)) for constant in self.constants])
        if self.variables:
            self.variable = pp.MatchFirst([variable['token'].setParseAction(variable.get('action', VariableAction)) for variable in self.variables])
            baseExpr = self.constant | self.variable
        else:
            self.variable = None
            baseExpr = self.constant

        EXP = pp.Forward()
        funcExpr = []
        for function in self.functions:
            if isinstance(function['token'], tuple) and len(function['token'])==2:
                # bifixNotation
                left = pp.Literal(function['token'][0]) if isinstance(function['token'][0], str) else function['token'][0]
                right = pp.Literal(function['token'][1]) if isinstance(function['token'][1], str) else function['token'][0]
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
                    funcExpr.append((function['token']('function') + LPAREN+ pp.delimitedList(EXP)('args') + RPAREN).setParseAction(function['action']))
        funcExpr = pp.MatchFirst(funcExpr)
        tupleExpr = LPAREN + (pp.Group(pp.Optional(EXP + COMMA)) | (EXP + COMMA + pp.delimitedList(EXP) + pp.Optional(COMMA)))('items') + RPAREN
        tupleExpr.setParseAction(TupleAction)
        M = funcExpr | tupleExpr | baseExpr | LPAREN + EXP + RPAREN
        indexExpr = M('variable') + pp.OneOrMore(pp.Suppress('[') + EXP + pp.Suppress(']'))('index')
        indexExpr.setParseAction(IndexAction)
        EXP <<= pp.infixNotation(indexExpr | M, optable2oplist(self.operators))
        self.expression = EXP
        # EXP = mixedExpression(baseExpr, funcExpr, flag=True, opList=optable2oplist(self.operators))

    def enableLambda(self, sep=pp.Suppress(':')):
        lambdaExpr = pp.Keyword('lambda') + pp.delimitedList(variable)('args') + sep + EXP('expression')
        self.functions.append({'token':lambdaExpr, 'action':LambdaAction})
        return self

    def enableLet(self, sep=pp.Suppress(':')):
        letExpr = pp.Keyword('let') + pp.delimitedList(variable + pp.Suppress('=') + EXP)('arg_vals')  + sep + EXP('expression')
        self.functions.append({'token':letExpr, 'action':LetAction})
        return self

    def matches(self, s):
        if not hasattr(self, 'expression'):
            self.make_parser()
        return self.expression.matches(s)

    def parse(self, s):
        if not hasattr(self, 'expression'):
            self.make_parser()
        return self.expression.parseString(s)[0]

    def parseFile(self, filename):
        with open(filename, 'r') as fo:
            return self.parse(fo.read())

    def del_parser(self):
        del self.expression

    def __setstate__(self, state):
        self.keywords, self.constants, self.variables, self.functions, self.operators =\
         state['keywords'], state['constants'], state['variables'], state['functions'], state['operators']


class Language:
    '''Language'''
    def __init__(self, name='Toy', grammar=None, calculator=None):
        self.name = name
        self.grammar = grammar
        self.calculator = calculator

    def __str__(self):
        return 'Language <%s>' % self.name

    def make_parser(self):
        self.grammar.make_parser()

    def matches(self, s):
        return self.grammar.matches(s)

    def parse(self, s):
        return self.grammar.parse(s)

    def parseFile(self, filename):
        return self.grammar.parseFile(filename)

    def eval(self, s):
        return self.parse(s).eval(calculator=self.calculator)

    def __call__(self, s):
        return self.eval(s)

    def __setstate__(self, state):
        self.name, self.grammar, self.calculator = state['name'], state['grammar'], state['calculator']

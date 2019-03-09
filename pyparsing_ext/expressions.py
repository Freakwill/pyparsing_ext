#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyparsing as pp

from pyparsing_ext.core import *
from pyparsing_ext.actions import *


# helpers:
def enumeratedItems(baseExpr=None, form='[1]', **min_max):
    """Parser for enumerated items
    
    Examples:
    [1] abc
    [2] def

    ==> ['abc', 'def']
    """
    if form is None:
        form = '[1]'
    if '1' in form:
        no = pp.Regex(re.escape(form).replace('1','(?P<no>\\d+)')) #.setParseAction(lambda x:x.no)
    else:
        no = pp.Regex(re.escape(form))
    # no.suppress()
    if 'exact' in min_max and min_max['exact'] > 0:
        max_ = min_ = exact
    else:
        min_ = min_max.get('min', 0)
        max_ = min_max.get('max', None)
    if baseExpr is None:
        return (pp.Group(no + pp.SkipTo(pp.StringEnd() | no).setParseAction(_strip()))) * (min_, max_)
    else:
        return (pp.Group(no + baseExpr.setParseAction(_strip()))) * (min_, max_)

def _strip(ch=None):
    if ch is None:
        return lambda s, l, t: t[0].strip()
    else:
        return lambda s, l, t: t[0].strip(ch)


def delimitedMatrix(baseExpr=pp.Word(pp.alphanums), ch1=',', ch2=';'):
    r"""delimitedMatrix works like delimitedList

    2-order delimitedList

    Exmpale:
    'a b\nc d' 
    ==> [['a', 'b'], ['c', 'd']]
    """
    if ch1 == ch2:
        raise Exception('make sure ch1 != ch2')
    if isinstance(ch1, str):
        if ch1 is '':
            raise Exception('make sure ch1 is not empty')
        if iswhite(ch1):
            ch1 = pp.Literal(ch1).leaveWhitespace()
        else:
            ch1 = pp.Literal(ch1)
    if isinstance(ch2, str):
        if ch2 is '':
            raise Exception('make sure ch2 is not empty')
        if iswhite(ch2):
            ch2 = pp.Literal(ch2).leaveWhitespace()
        else:
            ch2 = pp.Literal(ch2)
    return pp.delimitedList(pp.Group(pp.delimitedList(baseExpr, ch1.suppress())), ch2.suppress())

def tupleExpression(baseExpr=pp.Word(pp.alphanums), lpar=LPAREN, rpar=RPAREN):
    """Tuple Expression
    
    Some valid expression:
    (1,), (), (), (1,2,3), (1,2,3,)
    """
    return lpar + ((baseExpr + COMMA + pp.delimitedList(baseExpr) + pp.Optional(COMMA)) | pp.Group(pp.Optional(baseExpr + COMMA))) + rpar


def tableExpression(baseExpr=pp.Word(pp.alphanums), sep=COLON, lpar=LBRACE, rpar=RBRACE):
    """Tuple Expression
    
    Some valid expression:
    (1,), (), (), (1,2,3), (1,2,3,)
    """
    return lpar + pp.delimitedList(baseExpr + sep + baseExpr) + rpar


# need to be improved
class MixedExpression(pp.ParseElementEnhance):
    """MixedExpression, oop verion of mixedExpression
    """

    def __init__(self, baseExpr, opList=[], lpar=LPAREN, rpar=RPAREN, *args, **kwargs):
        super(MixedExpression, self).__init__(baseExpr, *args, **kwargs)
        self.baseExpr = baseExpr
        self.opList = opList
        self.lpar = lpar
        self.rpar = rpar
        self.expr = pp.infixNotation(baseExpr, opList, lpar, rpar)

    def enableIndex(self, action=IndexOpAction):
        # index expression, x[start:stop:step]
        EXP = pp.Forward()
        SLICE = pp.Optional(EXP)('start') + COLON + pp.Optional(EXP)('stop') + pp.Optional(COLON + pp.Optional(EXP)('step'))
        indexop = LBRACK + (SLICE('slice') | EXP('index')) + RBRACK
        indexop.setParseAction(action)
        self.opList.insert(0, indexop)
        self.expr <<= pp.infixNotation(EXP, self.opList, self.lpar, self.rpar)

    def enableCallPlus(self, action=CallOpAction, flag=False):
        # call expression, x(...)
        EXP = self.expr
        KWARG = IDEN + pp.Suppress('=') + EXP
        if flag:
            STAR = pp.Suppress('*') + EXP
            DBLSTAR = pp.Suppress('**') + EXP
            callop = LPAREN + pp.Optional(pp.delimitedList(EXP))('args') + pp.Optional(pp.delimitedList(KWARG | STAR))('kwargs') + pp.Optional(DBLSTAR) + RPAREN
        else:
            callop = LPAREN + pp.Optional(pp.delimitedList(EXP))('args') + pp.Optional(pp.delimitedList(KWARG))('kwargs') + RPAREN
        callop.setParseAction(action)
        self.opList.insert(0, callop)
        self.expr <<= pp.infixNotation(self.baseExpr, self.opList, self.lpar, self.rpar)

    def enableDot(self, action=DotOpAction):
        # dot expression, x.a
        EXP = self.expr
        dotop = pp.Suppress('.') + IDEN('attr')
        dotop.setParseAction(action)
        self.opList.insert(0, dotop)
        self.expr <<= pp.infixNotation(self.baseExpr, self.opList, self.lpar, self.rpar)


    def enableAll(self, actions=None, flag=False):
        self.enableIndex()
        self.enableCall(flag)
        self.enableDot()


def mixedExpression(baseExpr, func=None, flag=False, opList=[], lpar=LPAREN, rpar=RPAREN):
    """Mixed expression, more powerful then operatorPrecedence

    It calls operatorPrecedence.
    
    Arguments:
        func: function of baseExpr (can be distincted by first token)
        flag: for parsing the expressions: a(x) a[x] a.x
        others are same with infixedNotation

    Return:
        ParserElementEnhance

    
    Example:
    ------
    integer = pp.pyparsing_common.signed_integer
    varname = pp.pyparsing_common.identifier

    arithOplist = [('-', 1, pp.opAssoc.RIGHT),
        (pp.oneOf('* /'), 2, pp.opAssoc.LEFT),
        (pp.oneOf('+ -'), 2, pp.opAssoc.LEFT)]

    def func(EXP):
        return pp.Group('<' + EXP + pp.Suppress(',') + EXP +'>')| pp.Group('||' + EXP + '||') | pp.Group('|' + EXP + '|') | pp.Group(IDEN + '(' + pp.delimitedList(EXP) + ')')
    baseExpr = integer | varname
    EXP = mixedExpression(baseExpr, func=func, opList=arithOplist)

    a = EXP.parseString('5*g(|-3|)+<4,5> + f(6)')
    print(a)
    # [[[5, '*', ['g', '(', ['|', ['-', 3], '|'], ')']], '+', ['<', 4, 5, '>'], '+', ['f', '(', 6, ')']]]
    """
    
    EXP = pp.Forward()
    if flag:
        # expression as a[d].b(c)
        SLICE = pp.Optional(EXP)('start') + COLON + pp.Optional(EXP)('stop') + pp.Optional(COLON + pp.Optional(EXP)('step'))
        indexop = LBRACK + (SLICE('slice') | EXP('index')) + RBRACK
        indexop.setParseAction(IndexOpAction) # handle with x[y]
        KWARG = IDEN + pp.Suppress('=') + EXP
        # STAR = pp.Suppress('*') + EXP; DBLSTAR = pp.Suppress('**') + EXP
        callop = LPAREN + pp.Optional(pp.delimitedList(EXP))('args') + pp.Optional(pp.delimitedList(KWARG))('kwargs') + RPAREN
        callop.setParseAction(CallOpAction)  # handle with f(x)
        dotop = pp.Suppress('.') + IDEN('attr')
        dotop.setParseAction(DotOpAction)    # handle with x.y
        opList.insert(0, (indexop | callop | dotop, 1, pp.opAssoc.LEFT, ICDAction))
    
    if func:
        if isinstance(func, pp.ParserElement):
            f = pp.Group(func + LPAREN + pp.delimitedList(EXP) + RPAREN)
            block = f | baseExpr
        else:  # func is callable
            block = func(EXP) | baseExpr
        EXP <<= pp.infixNotation(block, opList, lpar, rpar)
    else:
        EXP <<= pp.infixNotation(baseExpr, opList, lpar, rpar)
    return EXP


def logicterm(constant=DIGIT, variable=IDEN, function=IDEN, lambdaterm=False):
    # f(x,y...) | const | x
    if lambdaterm:
        function = function | lambdaterm(variable, lambdaKeyword='lambda')
    t = pp.Forward()
    t <<= (function('function') + LPAREN + pp.delimitedList(t)('args') + RPAREN).setParseAction(FunctionAction) | (constant | variable).setParseAction(AtomAction)
    return t


def lambdaterm(variable=IDEN, lambdaKeyword='lambda'):
    # lambda variable: expression
    t = pp.Forward()
    t <<= pp.Suppress(lambdaKeyword) + pp.delimitedList(variable)('args') + (t | logicterm(constant=DIGIT, variable=IDEN, function=None))('term')
    t.setParseAction(LambdaAction)
    return t


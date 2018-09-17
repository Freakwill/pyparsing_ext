#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import pyparsing as pp
from pyparsing_ext.actions import *

arithOplist = [('**', 2, pp.opAssoc.RIGHT, RightBinaryOperatorAction),
    (pp.oneOf('+ - ~'), 1, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.oneOf('* / // %'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.oneOf('+ -'), 2, pp.opAssoc.LEFT, BinaryOperatorAction)]


pyOplist = arithOplist + [('&', 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    ('^', 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    ('|', 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('is') | pp.Keyword('is not'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('in') | pp.Keyword('not in'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.oneOf('< <= > >= == !='), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('not'), 1, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.Keyword('and'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('or'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    ((pp.Keyword('if'), pp.Keyword('else')), 3, pp.opAssoc.RIGHT, TernaryOperatorAction)]

# logic:
logicOplist = [(pp.Keyword('not'), 1, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.Keyword('and'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('or'), 2, pp.opAssoc.LEFT, BinaryOperatorAction)]


class Operator(object):
    '''Operator'''
    
    def __init__(self, symbol, arity=2, assoc=pp.opAssoc.LEFT, action=None):
        '''[summary]
        
        [description]
        
        Arguments:
            symbol {str} -- the symbol of operator
        
        Keyword Arguments:
            arity {int}: arity of the operator
            assoc: assoc method
            action {BaseAction}: action
        '''
        self.symbol = symbol
        self.arity = arity
        self.assoc = assoc
        self.action = action

    def __getitem__(self, k):
        return (self.symbol, self.arity, self.assoc, self.action)[k]
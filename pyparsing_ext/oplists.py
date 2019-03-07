#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import pyparsing as pp
from pyparsing_ext.actions import *

arithOplist = [('**', 2, pp.opAssoc.RIGHT, RightBinaryOperatorAction),
    (pp.oneOf('+ - ~'), 1, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.oneOf('* / // %'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.oneOf('+ -'), 2, pp.opAssoc.LEFT, BinaryOperatorAction)]

setOplist = [('&', 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    ('^', 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    ('|', 2, pp.opAssoc.LEFT, BinaryOperatorAction)]

# logic:
boolOplist = [(pp.Keyword('not'), 1, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.Keyword('and'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('or'), 2, pp.opAssoc.LEFT, BinaryOperatorAction)]

logicOplist = boolOplist

pyOplist = arithOplist + setOplist + [
    (pp.Keyword('is') | pp.Keyword('is not'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.Keyword('in') | pp.Keyword('not in'), 2, pp.opAssoc.LEFT, BinaryOperatorAction),
    (pp.oneOf('< <= > >= == !='), 2, pp.opAssoc.LEFT, BinaryOperatorAction)] + logicOplist + [
    ((pp.Keyword('if'), pp.Keyword('else')), 3, pp.opAssoc.RIGHT, TernaryOperatorAction)]

cOplist = arithOplist + setOplist + [
    (pp.Keyword('&'), 2, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.OneOrMore('*'), 2, pp.opAssoc.RIGHT, UnaryOperatorAction),
    (pp.oneOf('< <= > >= == !='), 2, pp.opAssoc.LEFT, BinaryOperatorAction)] + logicOplist + [
    ((pp.Keyword('?'), pp.Keyword(':')), 3, pp.opAssoc.RIGHT, TernaryOperatorAction)]

class Operator(object):
    """Operator, esp. Math operators +-*/"""
    
    def __init__(self, symbol, arity=2, assoc=pp.opAssoc.LEFT, action=None):
        """
        Arguments:
            symbol {str|pp.ParserElement|pair} -- the symbol of operator
        
        Keyword Arguments:
            arity {int}: arity of the operator
            assoc: assoc method
            action {BaseAction}: action
        """
        self.symbol = symbol
        self.arity = arity
        self.assoc = assoc
        self.action = action

    def __getitem__(self, k):
        return (self.symbol, self.arity, self.assoc, self.action)[k]

def optable2oplist(optable):
    '''list of operator-dict to list of operators (as in pyparsing)
    operator-dict = {'token':'+', 'arity':2, 'assoc':'left', 'action':BinaryOperatorAction}
    '''
    oplist = []
    for op in optable:
        if isinstance(op, (str, pp.ParserElement)):
            oplist.append((op, 2, pp.opAssoc.LEFT, BinaryOperatorAction))
        elif isinstance(op, tuple):
            if len(op) == 3:
                if op[1] == 2:
                    oplist.append(op + (BinaryOperatorAction,))
                elif op[1] == 1:
                    oplist.append(op + (UnaryOperatorAction,))
                elif op[1] == 3:
                    oplist.append(op + (TernaryOperatorAction,))
            oplist.append(op)
        else: # op is a dict
            if 'arity' not in op:
                op.update(arity=2)
            if 'assoc' not in op:
                if op['arity'] == 1:
                    op.update(assoc=pp.opAssoc.RIGHT)
                else:
                    op.update(assoc=pp.opAssoc.LEFT)
            else:
                if op['assoc'] in {'left', 'Left', 'l', 'L'}:
                    op.update(assoc=pp.opAssoc.LEFT)
                elif op['assoc'] in {'right', 'Right', 'r', 'R'}:
                    op.update(assoc=pp.opAssoc.RIGHT)
            if 'action' not in op:
                if op['arity'] == 1:
                    action = UnaryOperatorAction
                elif op['arity'] == 2:
                    if op['assoc'] == pp.opAssoc.LEFT:
                        action = BinaryOperatorAction
                    elif op['assoc'] == pp.opAssoc.RIGHT:
                        action = RightBinaryOperatorAction
                elif op['arity'] == 3:
                    action = TernaryOperatorAction
                oplist.append((op['token'], op['arity'], op['assoc'], action))
            else:
                oplist.append((op['token'], op['arity'], op['assoc'], op['action']))
    return oplist


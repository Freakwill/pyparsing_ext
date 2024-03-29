#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import pyparsing as pp

from pyparsing_ext import *

# advanced functitons
def isatomic(pe):
    '''whether ParserElement pe is atomic (is an atom):
    a token is atomic
    enhancement of an atom is atomic
    expression consisting of only one atom is atomic'''
    if pe.checkRecursion([]):
        return False
    if isinstance(pe, pp.Token):
        return True
    elif isinstance(pe, _Enhance):
        return isatomic(pe.expr)
    elif isinstance(pe, pp.ParseExpression):
        if len(pe.exprs) ==1:
            return isatomic(pe.exprs[0])
        else:
            return False
    else:
        return False

def ismonomial(pe, product=(pp.And, pp.Each)):
    # exmpale: a + b + c where a, b, c are atomic as in polynomials
    if pe.checkRecursion([]):
        return False
    if isatomic(pe):
        return True
    elif isinstance(pe, _Enhance):
        return ismonomial(pe.expr)
    elif isinstance(pe, product):
        return all(ismonomial(expr) for expr in pe.exprs)
    else:
        return False


def expand(pe, aslist = False):
    pe.streamline()
    if isinstance(pe, (pp.And, pp.Each)):
        if pe.exprs:
            x = expand(pe.exprs[0], True)
            for expr in pe.exprs[1:]:
                x = [xi + a for xi in x for a in expand(expr, True)]
    elif isinstance(pe, (pp.Or, pp.MatchFirst)):
        x = []
        for expr in pe.exprs:
            x.extend(expand(expr, True))
    elif isinstance(pe, _Enhance):
        x = expand(pe.expr, True)
    else: # x is monomal
        x = [pe]

    x = [xi.streamline() for xi in x]
    if aslist:
        return x
    else:
        if len(x)==1:
            return x[0]
        else:
            return pp.MatchFirst(x)

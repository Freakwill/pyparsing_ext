#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import pyparsing as pp

# classes for actions
class BaseAction:
    '''Base class for parsing action classes
    '''
    def __init__(self, instring='', loc=0, tokens=[], *args, **kwargs):
        self.tokens = tokens
        self.instring = instring
        self.loc = loc

    def has(self, name):
        return name in self.tokens

    def __len__(self):
        return len(self.tokens)

    def __eq__(self, other):
        if isinstance(other, BaseAction):
            return self.tokens == other.tokens
        else:
            return self.tokens == other

    def __repr__(self):
        return ' '.join(map(str, self.tokens))

    def __call__(self, *args, **kwargs):
        # if eval defined in action
        return self.eval(*args, **kwargs)

    def eval(self, *args, **kwargs):
        # evaluate it
        pass

    def execute(self, *args, **kwargs):
        pass

class VarOpAction(BaseAction):
    # for operators with variables
    pass


class CallOpAction(VarOpAction):
    '''x(args, kwargs=values) where (args, kwargs=values) is an operator and x is the corresponding operand
    distinguished with f(x)
    '''
    def __init__(self, tokens):
        super(IndexOpAction, self).__init__(tokens)
        self.args = tokens.args if self.has('args') else ()
        self.kwargs = dict(zip(tokens.kwargs[::2], tokens.kwargs[1::2])) if self.has('kwargs') else {}


class DotOpAction(VarOpAction):
    # x.attr
    def __init__(self, tokens):
        super(IndexOpAction, self).__init__(tokens)
        self.attr = tokens.attr

    def eval(self, calculator):
        return self.attr.eval(calculator)

class IndexOpAction(VarOpAction):
    # x[start:stop]
    def __init__(self, tokens):
        super(IndexOpAction, self).__init__(tokens)
        if self.has('slice'):
            slc = tokens.slice
            self.start = slc.start if 'start' in slc else None
            self.stop = slc.stop if 'stop' in slc else None
            self.step = slc.step if 'step' in slc else None
        else:
            self.index = tokens.index

    def eval(self, calculator):
        if self.has('slice'):
            return slice(self.start.eval(calculator), self.stop.eval(calculator), self.step.eval(calculator))
        else:
            return self.index.eval(calculator)


# operators, arithmetic, mathematics, logic:
def _tosx(x):
    return x if isinstance(x, str) else x.sexpr()

# actions for expressions
class FunctionAction(BaseAction):
    '''action class for function function(args)
       properties: 
       function: a function
       args: the arguments of the function'''
    def __init__(self, tokens):
        super(FunctionAction, self).__init__(tokens)
        if 'function' in tokens:
            self.function = tokens.function
        if 'args' in tokens:
            self.args = tokens.args

    def __eq__(self, other):
        if isinstance(other, FunctionAction):
            return self.args == other.args and self.function == other.function
        else:
            return self.args == other[1:] and self.function == other[0]

    def __repr__(self):
        return "%s(%s)"%(self.function, ', '.join(map(str, self.args)))

    def sexpr(self):
        return "(%s %s)"%(_tosx(self.function) , ' '.join(_tosx(arg) for arg in self.args))

    def arity(self):
        return len(self.args)

    def eval(self, calculator):
        # calculator(self.function, *self.args)
        return calculator(self.function, *(arg.eval(calculator) for arg in self.args))


class OperatorAction(FunctionAction):
    pass

 
class BifixAction(FunctionAction):
    '''action class for bifix operator such as 
    |x|=abs(x) or ||x||=norm(x) or <x,y>=inner product of x and y;
    bifix operator has function of parentheses
    parentheses in the expression (<x, y>) is tedious'''
    def __init__(self, tokens):
        super(BifixAction, self).__init__(tokens)
        if self.has('args'):
            self.args = tokens.args
        else:
            self.args = [tokens.arg]
        self.function = (tokens.left, tokens.right)


class InfixOperatorAction(OperatorAction):
    # action class for operators used in operatorPrecedence
    def __init__(self, tokens):
        super(InfixOperatorAction, self).__init__(tokens[0])


class UnaryOperatorAction(InfixOperatorAction):
    # action class for unary operators used in operatorPrecedence
    def __init__(self, tokens):
        super(UnaryOperatorAction, self).__init__(tokens)
        self.function, self.args = self.tokens[0], (self.tokens[1],)
        self.operand = self.tokens[1]

    def eval(self, calculator):
        # calculator(self.function, *self.args)
        return calculator(self.function, self.operand.eval(calculator))

class RightUnaryOperatorAction(UnaryOperatorAction):
    pass

class LeftUnaryOperatorAction(UnaryOperatorAction):
    '''action class for unary operators used in operatorPrecedence
    such as a*, a' '''
    def __init__(self, tokens):
        super(UnaryOperatorAction, self).__init__(tokens)
        self.function, self.args = self.tokens[1], (self.tokens[0],)
        self.operand = self.tokens[0]

class ICDAction(LeftUnaryOperatorAction):
    '''action for index, call and dot:
    a[...], a(...), a.xxx where a is an operand'''
    def __init__(self, tokens):
        super(ICDAction, self).__init__(tokens)
        self.ops = self.tokens[1:]
        self.operand = self.tokens[0]

    def eval(self, calculator):
        retval = self.operand.eval(calculator)
        for op in self.ops:
            if isinstance(op, IndexOpAction):
                retval = retval[op.eval(calculator)]
            elif isinstance(op, CallOpAction):
                args = (arg.eval(calculator) for args in op.args)
                kwargs = {k:v.eval(calculator) for k, v in op.kwargs.items()}
                retval = retval(*args, **kwargs)
            elif isinstance(op, DotOpAction):
                retval = getattr(retval, op.eval(calculator))
        return retval


class BinaryOperatorAction(InfixOperatorAction):
    # action class for binary operators used in operatorPrecedence
    def __init__(self, tokens):
        super(BinaryOperatorAction, self).__init__(tokens)
        tokens = tokens[0]
        self.args = self.tokens[0::2]
        if len(set(self.tokens[1::2]))==1:
            self.ishybrid = False
            self.function = self.tokens[1]
        else:
            self.ishybrid = True
            self.function = self.tokens[1::2]

    def prefix(self):
        if not self.ishybrid:
            return "%s(%s)" %(self.function, ', '.join(map(str, self.args)))
        else:
            return "(%s)(%s)" %(', '.join(self.function), ', '.join(map(str, self.args)))

    def __repr__(self):
        if not self.ishybrid:
            return (' %s '%self.function).join(map(str, self.args))
        else:
            s = str(self.args[0])
            for k, f in enumerate(self.function):
                s += ' %s %s'%(f, self.args[k])
            return s

    def sexpr(self):
        if not self.ishybrid:
            return "(%s %s)" %(_tosx(self.function), ' '.join(_tosx(arg) for arg in self.args))
        else:
            return "((%s) %s)" %(', '.join(self.function), ' '.join(map(_tosx, self.args)))

    def eval(self, calculator):
        # calculator(self.function, *self.args)
        args = tuple(arg.eval(calculator) for arg in self.args)
        if self.ishybrid:
            ret = calculator(self.function[0])(args[0], args[1])
            for f, arg in zip(self.function[1:], self.args[2:]):
                ret = calculator(f)(ret, arg)
            return ret
        else:
            return functools.reduce(calculator(self.function), args)


class LeftBinaryOperatorAction(BinaryOperatorAction):
    pass


class RightBinaryOperatorAction(BinaryOperatorAction):

    def eval(self, calculator):
        args = tuple(arg.eval(calculator) for arg in self.args)
        if self.ishybrid:
            ret = calculator(self.function[-1])(args[-2], args[-1])
            for f, arg in zip(self.function[-2::-1], args[-3::-1]):
                ret = calculator(f)(arg, ret)
            return ret
        else:
            f = calculator(self.function)
            ret = f(args[-2], args[-1])
            for arg in args[-3::-1]:
                ret = f(arg, ret)
            return ret

class CompareAction(BinaryOperatorAction):
    # action for comparison
    def eval(self, calculator):
        args = tuple(arg.eval(calculator) for arg in self.args)
        if self.ishybrid:
            for k, f in enumerate(self.function):
                f = calculator(self.function)
                if not f(args[k], args[k+1]):
                    return False
            return True
        else:
            f = calculator(self.function)
            for k in range(len(args)-1):
                if not f(args[k], args[k+1]):
                    return False
            return True


class TernaryOperatorAction(OperatorAction):
    # action class for ternary operators used in operatorPrecedence
    def __init__(self, tokens):
        super(TernaryOperatorAction, self).__init__(tokens)
        tokens = tokens[0]
        self.function = self.tokens[1], self.tokens[3]
        self.args = self.tokens[0], self.tokens[2], self.tokens[4]

    def __repr__(self):
        return "(%s, %s)(%s)" %(self.function[0], self.function[1], ', '.join(map(str, self.args)))

    def sexpr(self):
        return "((%s, %s) %s)" %(self.function[0], self.function[1], ', '.join(map(str, self.args)))


class Operator(object):
    '''Operator has 4 (principal) propteries
    symbol: the symbol of operator
    arity: arity
    assoc: assoc method
    action: action'''
    def __init__(self, symbol, arity=2, assoc=pp.opAssoc.LEFT, action=None):
        self.symbol = symbol
        self.arity = arity
        self.assoc = assoc
        self.action = action

    def __getitem__(self, k):
        return (self.symbol, self.arity, self.assoc, self.action)[k]


class LambdaAction(BaseAction):
    # action class for lambda expression used in operatorPrecedence
    def __init__(self, tokens):
        super(LambdaAction, self).__init__(tokens)
        self.args, self.expr = tokens.args, tokens.expression
        self.lambdaKeyword='lambda'

    def __repr__(self):
        return "%s %s: %s"%(self.lambdaKeyword, ', '.join(map(str, self.args)), self.expr)

    def sexpr(self):
        return "(%s (%s) %s)"%(self.lambdaKeyword, ' '.join(map(str, self.args)), self.expr.sexpr())

    def eval(self, calculator):
        localcalculator = calculator.copy()
        def f(*args):
            localcalculator.update({arg:v for arg, v in zip(self.args, args)})
            return self.expr.eval(localcalculator)
        return f


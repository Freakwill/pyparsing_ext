#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import functools

import pyparsing as pp

# classes for actions
class BaseAction:
    '''Base class for parsing action classes
    '''
    def __init__(self, instring='', loc=0, tokens=[]):
        self.tokens = tokens
        self.instring = instring
        self.loc = loc

    def __contains__(self, name):
        return name in self.tokens

    def __getitem__(self, key):
        return getattr(self.tokens, key)

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
    def __init__(self, instring='', loc=0, tokens=[]):
        super(IndexOpAction, self).__init__(instring, loc, tokens)
        self.args = tokens.args if 'args' in self else ()
        self.kwargs = dict(zip(tokens.kwargs[::2], tokens.kwargs[1::2])) if 'kwargs' in self else {}


class DotOpAction(VarOpAction):
    # x.attr
    def __init__(self, instring='', loc=0, tokens=[]):
        super(IndexOpAction, self).__init__(instring, loc, tokens)
        self.attr = tokens.attr

    def eval(self, calculator):
        return self.attr.eval(calculator)

class IndexOpAction(VarOpAction):
    # x[start:stop]
    def __init__(self, instring='', loc=0, tokens=[]):
        super(IndexOpAction, self).__init__(instring, loc, tokens)
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
    def __init__(self, instring='', loc=0, tokens=[]):
        super(FunctionAction, self).__init__(instring, loc, tokens)
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

 
class BifixAction(FunctionAction):
    '''Action class for bifix operator such as 
    |x|=abs(x) or ||x||=norm(x) or <x,y>=inner product of x and y;
    bifix operator has effect of parentheses;
    parentheses in the expression (<x, y>) is tedious
    '''
    def __init__(self, instring='', loc=0, tokens=[]):
        super(BifixAction, self).__init__(instring, loc, tokens)
        if self.has('args'):
            self.args = tokens.args
        else:
            self.args = [tokens.arg]
        self.function = (tokens.left, tokens.right)

class OperatorAction(FunctionAction):
    pass

class InfixOperatorAction(OperatorAction):
    # action class for operators used in operatorPrecedence
    pass


class UnaryOperatorAction(InfixOperatorAction):
    # action class for unary operators used in operatorPrecedence
    def __init__(self, instring='', loc=0, tokens=[]):
        super(UnaryOperatorAction, self).__init__(instring, loc, tokens)
        self.function, self.args = self.tokens[0], (self.tokens[1],)
        self.operand = self.tokens[1]

    def eval(self, calculator):
        # calculator(self.function, *self.args)
        return calculator(self.function, self.operand.eval(calculator))

class RightUnaryOperatorAction(UnaryOperatorAction):
    pass

class LeftUnaryOperatorAction(UnaryOperatorAction):
    '''action class for unary operators used in operatorPrecedence
    such as x*, x' '''
    def __init__(self, instring='', loc=0, tokens=[]):
        super(UnaryOperatorAction, self).__init__(instring, loc, tokens)
        self.function, self.args = self.tokens[1], (self.tokens[0],)
        self.operand = self.tokens[0]

class ICDAction(LeftUnaryOperatorAction):
    '''action for index, call and dot:
    a[...], a(...), a.xxx where a is treated as an operand'''
    def __init__(self, instring='', loc=0, tokens=[]):
        super(ICDAction, self).__init__(instring, loc, tokens)
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
    def __init__(self, instring='', loc=0, tokens=[]):
        super(BinaryOperatorAction, self).__init__(instring, loc, tokens)
        self.args = self.tokens[0::2]
        if len(set(self.tokens[1::2]))==1:
            self.ishybrid = False
            self.function = self.tokens[1]
        else:
            self.ishybrid = True
            self.function = self.tokens[1::2]
        self.associative = True

    def prefix(self):
        if not self.ishybrid and self.associative:
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


class TernaryOperatorAction(InfixOperatorAction):
    # action class for ternary operators used in operatorPrecedence
    def __init__(self, instring='', loc=0, tokens=[]):
        super(TernaryOperatorAction, self).__init__(instring, loc, tokens)
        tokens = tokens[0]
        self.function = self.tokens[1], self.tokens[3]
        self.args = self.tokens[0], self.tokens[2], self.tokens[4]

    def __repr__(self):
        return "(%s, %s)(%s)" %(self.function[0], self.function[1], ', '.join(map(str, self.args)))

    def sexpr(self):
        return "((%s, %s) %s)" %(self.function[0], self.function[1], ', '.join(map(str, self.args)))


class LambdaAction(BaseAction):
    # action class for lambda expression used in operatorPrecedence
    def __init__(self, instring='', loc=0, tokens=[]):
        super(LambdaAction, self).__init__(instring, loc, tokens)
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


class IndexAction(BaseAction):
    # action class for index expression
    def __init__(self, tokens):
        super(IndexAction, self).__init__(tokens)
        self.index = tokens.index
        self.variable = tokens.variable

    def __repr__(self):
        return "%s[%s]" %(self.variable, ']['.join(map(str, self.index)))

    def sexpr(self):
        return "(%s, %s, %s)" %('get', self.variable, ', '.join(map(str, self.index)))

    def eval(self, calculator):
        ret = self.variable.eval(calculator)
        for ind in self.index:
            ret = ret[int(ind.eval(calculator))]
        return ret

class SliceExprAction(BaseAction):
    # action class for slice expression
    def __init__(self, tokens):
        super(SliceExprAction, self).__init__(tokens)
        self.slice = tokens.slice
        self.variable = tokens.variable

    def __repr__(self):
        return "%s[%s]" %(self.variable, ']['.join(map(str, self.slice)))

    def sexpr(self):
        return "(%s, %s, %s)" %('get', self.variable, ', '.join(map(str, self.slice)))

    def eval(self, calculator):
        ret = self.variable.eval(calculator)
        for ind in self.slice:
            ret = ret[int(ind.eval(calculator))]
        return ret

class QuantifierAction(OperatorAction):
    '''action class for quantifiers
    forall x A(x) where quantifier = forall, varaibles = (x,), operand (of the quantifier) = A(x)
    '''
    def __init__(self, tokens):
        super(QuantifierAction, self).__init__(tokens)
        self.quantifier, self.variables = self.tokens.quantifier, self.tokens.variables
        self.operand = self.tokens[-1]

    def __repr__(self):
        return "%s %s (%s)" %(self.quantifier, ', '.join(map(str, self.variables)), self.operand)

    def sexpr(self):
        return "(%s (%s) %s)" %(self.quantifier, ', '.join(map(tosx, self.variables)), self.operand.sexpr())

# tuple, set
class TupleAction(FunctionAction):
    # action class for atomic term
    def __init__(self, tokens):
        super(TupleAction, self).__init__(tokens)
        self.function = 'tuple'
        self.args = tokens.items

    def eval(self, calculator):
        return tuple(arg.eval(calculator) for arg in self.args)


class SetAction(FunctionAction):
    # action class for set
    def __init__(self, tokens):
        super(TupleAction, self).__init__(tokens)
        self.function = 'set'
        self.args = tokens.items

    def eval(self, calculator):
        return set(arg.eval(calculator) for arg in self.args)


# More advanced actions
# atomic expression
class AtomAction(BaseAction):
    # action class for atomic term
    def __init__(self, tokens):
        super(AtomAction, self).__init__(tokens)
        self.content = tokens[0]

    def __eq__(self, other):
        if isinstance(other, AtomAction):
            return self.content == other.content
        else:
            return self.content == other

    def __repr__(self):
        return str(self.content)

    def sexpr(self):
        return str(self.content)


class VariableAction(AtomAction):
    # action class for variable
    def __init__(self, tokens):
        super(VariableAction, self).__init__(tokens)

    def __hash__(self):
        return hash(self.content)

    def eval(self, calculator):
        if self.content in calculator.context:
            return calculator[self.content]
        else:
            raise Exception('%s could not be evaluated!'%self.content)


class ConstantAction(AtomAction):
    # action class for constant
    def __init__(self, tokens):
        super(ConstantAction, self).__init__(tokens)

    def eval(self, calculator):
        return calculator.dict_[self.content]

class NoneAction(AtomAction):
    # action class for none (null)
    pass

class NumberAction(AtomAction):
    # action class for number
    def __init__(self, tokens):
        super(NumberAction, self).__init__(tokens)

    def eval(self, calculator):
        import decimal
        return decimal.Decimal(self.content)

class IntegerAction(AtomAction):
    # action class for integer
    def __init__(self, tokens):
        super(IntegerAction, self).__init__(tokens)

    def eval(self, calculator):
        return int(self.content)


class BoolAction(AtomAction):
    # action class for boolean value
    pass


class StringAction(AtomAction):
    # action class for string

    def eval(self, calculator):
        return self.content

    def __repr__(self):
        return '"%s"'%self.content



class LetAction(BaseAction):
    # action class for unary operator used in operatorPrecedence
    def __init__(self, tokens):
        super(LetAction, self).__init__(tokens)
        self.args, self.values, self.expr = tokens.args[::2], tokens.args[1::2], tokens.expression
        self.letKeyword = 'let'

    def __repr__(self):
        return "%s %s=%s: %s" %(self.letKeyword, ', '.join(map(str, self.args)), ', '.join(map(str, self.args)), self.expr)

    def sexpr(self):
        return "(%s (%s) (%s) %s)" %(self.letKeyword, ' '.join(map(str, self.args)), ' '.join(map(str, self.args)), self.expr.sexpr())

    def eval(self, calculator):
        localcalculator = calculator.copy()
        localcalculator.update({arg:val for arg, val in zip(self.args, self.values)})
        return self.expr.eval(localcalculator)


# actions for programming
class CommandAction(BaseAction):
    '''action for command such as assignment'''
    # def __call__(self, calculator):
    #     return self.execute(calculator)

    def execute(self, calculator):
        return calculator

    def __repr__(self):
        if self.has('keyword'):
            return self.tokens.keyword
        else:
            return self.tokens[0]


class ControlAction(CommandAction):
    # action for contral flow
    pass

class BreakAction(ControlAction):
    def execute(self, calculator):
        calculator.control = 'break'


class ContinueAction(ControlAction):
    def execute(self, calculator):
        calculator.control = 'continue'


class ReturnAction(ControlAction):
    def __init__(self, tokens):
        super(ReturnAction, self).__init__(tokens)
        self.retval = tokens.retval

    def __repr__(self):
        if self.has('keyword'):
            return '%s %s'%(self.tokens.keyword, self.retval)
        else:
            return '%s %s'%(self.tokens[0], self.retval)

    def execute(self, calculator):
        calculator.control = 'return'
        calculator.retval = self.retval.eval(calculator)

class PassAction(CommandAction):
    pass

class PrintAction(CommandAction):
    def __init__(self, tokens):
        super(PrintAction, self).__init__(tokens)
        self.args = tokens.args

    def __repr__(self):
        if self.has('keyword'):
            return '%s %s'%(self.tokens.keyword, ', '.join(map(str, self.args)))
        else:
            return '%s %s'%(self.tokens[0], ', '.join(map(str, self.args)))

    def execute(self, calculator):
        for arg in self.args:
            print(arg.eval(calculator), end='')
        print()

class DeleteAction(CommandAction):
    def __init__(self, tokens):
        super(DeleteAction, self).__init__(tokens)
        self.args = tokens.args

    def __repr__(self):
        if self.has('keyword'):
            return '%s %s'%(self.tokens.keyword, ', '.join(map(str, self.args)))
        else:
            return '%s %s'%(self.tokens[0], ', '.join(map(str, self.args)))

    def execute(self, calculator):
        for arg in self.args:
            del calculator.context[arg]


class EmbedAction(CommandAction):
    def __init__(self, tokens):
        super(EmbedAction, self).__init__(tokens)
        self.code = tokens.code

    def __repr__(self):
        if self.has('keyword'):
            return '%s {%s}'%(self.tokens.keyword, self.code)
        else:
            return '%s {%s}'%(self.tokens[0], self.code)

    def execute(self, calculator):
        exec(self.code, globals(), calculator.context)


# class LoadAction(CommandAction):
#     def __init__(self, tokens):
#         super(LoadAction, self).__init__(tokens)
#         self.path = tokens.path

#     def __repr__(self):
#         if self.has('keyword'):
#             return '%s %s'%(self.tokens.keyword, self.path)
#         else:
#             return '%s %s'%(self.tokens[0], self.path)

#     def execute(self):
#         with open(self.path) as fo:
#             s = fo.read()
#         return s

class AssignmentAction(CommandAction):
    '''action for assignment like x = expr'''
    def __init__(self, tokens):
        super(AssignmentAction, self).__init__(tokens)
        self.variable = tokens.variable.content
        self.expression = tokens.expression

    def execute(self, calculator):
        value = self.expression.eval(calculator)
        calculator.update({self.variable:value})

    def __repr__(self):
        return '%s = %s'%(self.variable, self.expression)

class IfAction(CommandAction):
    '''action for if statement'''
    def __init__(self, tokens):
        super(IfAction, self).__init__(tokens)
        self.condition = tokens.condition
        self.program = tokens.program

    def execute(self, calculator):
        if self.condition.eval(calculator):
            self.program.execute(calculator)


    def __repr__(self):
        return 'if %s {%s}'%(self.condition, self.program)

class WhileAction(CommandAction):
    '''action for while statement'''
    def __init__(self, tokens):
        super(WhileAction, self).__init__(tokens)
        self.condition = tokens.condition
        self.program = tokens.program

    def execute(self, calculator):
        ML = calculator.maxloop
        while self.condition(calculator):
            if ML == 0:
                raise Exception('reach the maximal looping')
            else:
                ML -= 1
            self.program.execute(calculator)
            if calculator.control == 'break':
                calculator.control = None
                break
            elif calculator.control == 'continue':
                calculator.control = None
                continue
            elif calculator.control == 'return':
                break

    def __repr__(self):
        return 'while %s {%s}'%(self.condition, self.program)

class IfelseAction(CommandAction):
    '''action for if-elif-else statement'''
    def __init__(self, tokens):
        super(IfelseAction, self).__init__(tokens)
        self.conditions = tokens.conditions[:]
        self.programs = tokens.programs[:]
        self.elseprogram = tokens.elseprogram

    def execute(self, calculator):
        for c, p in zip(self.conditions, self.programs):
            if c.eval(calculator):
                p.execute(calculator)
                break
        else:
            self.elseprogram.execute(calculator)


class ForAction(CommandAction):
    pass

class DefAction(CommandAction):
    ''''''
    def __init__(self, tokens):
        super(DefAction, self).__init__(tokens)
        if self.has('function'):
            self.function = tokens.function.content
        else:
            self.function = tokens.left, tokens.right
        self.args = tokens.args[:]
        self.program = tokens.program

    def execute(self, calculator):
        with calculator as loc:
            def f(*args):
                loc.update({arg.content:v for arg, v in zip(self.args, args)})
                self.program.execute(loc)
                return loc.retval
        calculator.update({self.function:f})


    def __repr__(self):
        if self.has('function'):
            return 'def %s(%s) {%s}'%(self.function, ', '.join(map(str, self.args)), self.program)
        else:
            return 'def %s(%s)%s {%s}'%(self.function[0], ', '.join(map(str, self.args)), self.function[1], self.program)

class ProgramSequenceAction(CommandAction):
    '''action for program; program; program...'''
    def __init__(self, tokens):
        super(ProgramSequenceAction, self).__init__(tokens)
        self.program = tokens[:]

    def execute(self, calculator):
        for cmd in self.program:
            context = cmd.execute(calculator)
            if calculator.control in {'break', 'continue', 'return'}:
                break

    def __repr__(self):
        return ';\n'.join(map(str, self.program))


def optable2oplist(optable):
    '''list of operator-dict to list of operators (as in pyparsing)
    operator-dict = {'token':'+', 'arity':2, 'assoc':'left', 'action':BinaryOperatorAction}
    '''
    oplist = []
    for op in optable:
        if isinstance(op, (str, pp.ParserElement)):
            oplist.append((op, 2, pp.opAssoc.LEFT, BinaryOperatorAction))
            continue
        elif isinstance(op, tuple):
            if len(op) == 3:
                if op[1] == 2:
                    oplist.append(op + (BinaryOperatorAction,))
                elif op[1] == 1:
                    oplist.append(op + (UnaryOperatorAction,))
                elif op[1] == 3:
                    oplist.append(op + (TernaryOperatorAction,))
            oplist.append(op)
            continue
        if 'arity' not in op:
            op.update(arity=2)
            n = 2
        else:
            n = op['arity']
        if 'assoc' not in op:
            if n == 1:
                op.update(assoc=pp.opAssoc.RIGHT)
            else:
                op.update(assoc=pp.opAssoc.LEFT)
        else:
            if op['assoc'] in {'left', 'Left', 'l', 'L'}:
                op.update(assoc=pp.opAssoc.LEFT)
            elif op['assoc'] in {'right', 'Right', 'r', 'R'}:
                op.update(assoc=pp.opAssoc.RIGHT)
        if 'action' not in op:
            if n == 1:
                action = UnaryOperatorAction
            elif n == 2:
                if op['assoc'] == pp.opAssoc.LEFT:
                    action = BinaryOperatorAction
                elif op['assoc'] == pp.opAssoc.RIGHT:
                    action = RightBinaryOperatorAction
            elif n == 3:
                action = TernaryOperatorAction
            oplist.append((op['token'], n, op['assoc'], action))
        else:
            oplist.append((op['token'], n, op['assoc'], op['action']))
    return oplist

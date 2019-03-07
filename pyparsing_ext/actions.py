#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import functools

import pyparsing as pp

# classes for actions
class BaseAction:
    '''Base class for parsing action classes
    '''
    names = ()
    def __init__(self, instring='', loc=0, tokens=[]):
        self.tokens = tokens
        self.instring = instring
        self.loc = loc
        for name in self.names:
            if name in tokens:
                setattr(self, name, getattr(tokens, name))

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
        if 'slice' in self:
            slc = tokens.slice
            self.start = slc.start if 'start' in slc else None
            self.stop = slc.stop if 'stop' in slc else None
            self.step = slc.step if 'step' in slc else None
        else:
            self.index = tokens.index

    def eval(self, calculator):
        if 'slice' in self:
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
    names = ('function', 'args')

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
        if 'args' in self:
            self.args = tokens.args
        else:
            self.args = [tokens.arg]
        self.function = (tokens.left, tokens.right)

class OperatorAction(FunctionAction):
    pass

class InfixOperatorAction(OperatorAction):
    # action class for operators used in infixNotation
    def __init__(self, instring='', loc=0, tokens=[]):
        '''
        The result of infixNotation is a list of list [[...]], hence
        we take self.tokens = tokens[0]
        '''
        super(InfixOperatorAction, self).__init__(instring, loc, tokens)
        self.tokens = tokens[0]


class UnaryOperatorAction(InfixOperatorAction):
    # action class for unary operators used in infixNotation
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
    '''action class for unary operators used in infixNotation
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
    # action class for binary operators used in infixNotation
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
    # action class for ternary operators used in infixNotation
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
    # action class for lambda expression used in infixNotation
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
    names = ('index', 'variable')

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
    name = ('slice', 'varaible')

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
    def __init__(self, instring='', loc=0, tokens=[]):
        super(QuantifierAction, self).__init__(instring, loc, tokens)
        self.quantifier, self.variables = self.tokens.quantifier, self.tokens.variables
        self.operand = self.tokens[-1]

    def __repr__(self):
        return "%s %s (%s)" %(self.quantifier, ', '.join(map(str, self.variables)), self.operand)

    def sexpr(self):
        return "(%s (%s) %s)" %(self.quantifier, ', '.join(map(tosx, self.variables)), self.operand.sexpr())

# tuple, set
class TupleAction(FunctionAction):
    # action class for atomic term
    function = 'tuple'
    def __init__(self, instring='', loc=0, tokens=[]):
        super(TupleAction, self).__init__(instring, loc, tokens)
        self.args = tokens.items

    def eval(self, calculator):
        return tuple(arg.eval(calculator) for arg in self.args)


class SetAction(FunctionAction):
    # action class for set
    function = 'set'
    def __init__(self, instring='', loc=0, tokens=[]):
        super(SetAction, self).__init__(instring, loc, tokens)
        self.args = tokens.items

    def eval(self, calculator):
        return set(arg.eval(calculator) for arg in self.args)


class DictAction(FunctionAction):
    # action class for set
    function = 'dict'
    names = ('keys', 'values')

    def eval(self, calculator):
        return dict(arg.eval(calculator) for arg in self.args)


# More advanced actions
# atomic expression
class AtomAction(BaseAction):
    # action class for atomic term
    def __init__(self, instring='', loc=0, tokens=[]):
        super(AtomAction, self).__init__(instring, loc, tokens)
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

    def eval(self, calculator):
        return self.content


class VariableAction(AtomAction):
    # action class for variable

    def __hash__(self):
        return hash(self.content)

    def eval(self, calculator):
        if self.content in calculator.context:
            return calculator[self.content]
        else:
            raise Exception('%s could not be evaluated!'%self.content)

class TypeAction(VariableAction):
    pass


class ConstantAction(AtomAction):
    # action class for constant

    def eval(self, calculator):
        return calculator.dict_[self.content]

class NoneAction(AtomAction):
    # action class for none (null)
    pass

class NumberAction(AtomAction):
    # action class for number

    def eval(self, calculator):
        import decimal
        return decimal.Decimal(self.content)

class IntegerAction(AtomAction):
    # action class for integer

    def eval(self, calculator):
        return int(self.content)


class BooleAction(IntegerAction):
    # action class for boolean value
    pass


class StringAction(AtomAction):
    # action class for string

    def __repr__(self):
        return '"%s"'%self.content


class LetAction(BaseAction):
    # action class for let-expression
    letKeyword = 'let'
    def __init__(self, instring='', loc=0, tokens=[]):
        super(LetAction, self).__init__(instring, loc, tokens)
        self.args, self.values, self.expr = tokens.args[::2], tokens.args[1::2], tokens.expression

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
    args = ()

    def execute(self, calculator):
        return calculator

    def __repr__(self):
        if 'keyword' in self:
            return '%s %s'%(self.tokens.keyword, ', '.join(map(str, self.args)))
        else:
            return '%s %s'%(self.tokens[0], ', '.join(map(str, self.args)))


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
    '''Action for return statement
    
    It is an action for return statement `return x`, x will saved in `.retval` of tokens.
    Executing the statement makes the calculator in the control state "return", and
    the return value will be saved in the calculator.
    
    Extends:
        ControlAction
    '''
    def __init__(self, instring='', loc=0, tokens=[]):
        super(ReturnAction, self).__init__(instring, loc, tokens)
        self.args = tokens.retval

    def execute(self, calculator):
        calculator.control = 'return'
        calculator.retval = self.args.eval(calculator)


class PassAction(CommandAction):
    pass


class PrintAction(CommandAction):
    def __init__(self, instring='', loc=0, tokens=[]):
        super(PrintAction, self).__init__(instring, loc, tokens)
        self.args = tokens.args

    def execute(self, calculator):
        for arg in self.args:
            print(arg.eval(calculator), end=' ')
        print()

class DeleteAction(CommandAction):
    def __init__(self, instring='', loc=0, tokens=[]):
        super(DeleteAction, self).__init__(instring, loc, tokens)
        self.args = tokens.args

    def execute(self, calculator):
        for arg in self.args:
            del calculator.context[arg]


class EmbedAction(CommandAction):
    def __init__(self, instring='', loc=0, tokens=[]):
        super(EmbedAction, self).__init__(instring, loc, tokens)
        self.code = tokens.code

    def __repr__(self):
        if 'keyword' in self:
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
    '''action for assignment like x = expr:type'''
    def __init__(self, instring='', loc=0, tokens=[]):
        super(AssignmentAction, self).__init__(instring, loc, tokens)
        self.variable = tokens.variable
        self.expression = tokens.expression
        if 'type' in tokens:
            self.type = tokens.type

    def execute(self, calculator):
        value = self.expression.eval(calculator)
        if hasattr(self, 'type'):
            assert isinstance(value, self.type), 'Type of %s is not %s' % (self.variable, self.type)
        calculator.update({self.variable.content:value})

    def __repr__(self):
        return '%s = %s'%(self.variable, self.expression)

class IfAction(CommandAction):
    '''action for if statement'''
    def __init__(self, instring='', loc=0, tokens=[]):
        super(IfAction, self).__init__(instring, loc, tokens)
        self.condition = tokens.condition
        self.program = tokens.program

    def execute(self, calculator):
        if self.condition.eval(calculator):
            self.program.execute(calculator)


    def __repr__(self):
        return 'if %s {%s}'%(self.condition, self.program)

class WhileAction(IfAction):
    '''action for while statement'''

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
        return 'while %s\n{%s}'%(self.condition, self.program)

class IfelseAction(CommandAction):
    '''action for if-elif-else statement'''
    def __init__(self, instring='', loc=0, tokens=[]):
        super(IfelseAction, self).__init__(instring, loc, tokens)
        self.conditions = tokens.conditions[:]
        self.programs = tokens.programs[:]
        if 'elseprogram' in tokens:
            self.elseprogram = tokens.elseprogram

    def execute(self, calculator):
        for c, p in zip(self.conditions, self.programs):
            if c.eval(calculator):
                p.execute(calculator)
                break
        else:
            self.elseprogram.execute(calculator)

    def __repr__(self):
        ifsen = 'if %s\n    {%s}\n'%(self.conditions[0], self.programs[0])
        for c, p in zip(self.conditions[1:], self.programs[1:]):
            ifsen += 'elif %s\n    {%s}\n' % (c, p)
        ifsen += 'else\n    {%s}\n' % self.elseprogram


class ForAction(WhileAction):
    def execute(self, calculator):
        ML = calculator.maxloop
        for _ in self.range_.eval(calculator):
            calculator.update({self.loopingVar: _})
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
        return 'for %s in %s\n{%s}'%(self.loopingVar, self.range_, self.program)

class DefAction(CommandAction):
    '''
    Action for definition of functions
    '''
    def __init__(self, instring='', loc=0, tokens=[]):
        super(DefAction, self).__init__(instring, loc, tokens)
        if 'function' in self:
            self.function = tokens.function.content
            self.args = tokens.args[:]
        elif 'operator' in self:
            self.function = tokens.operator
            self.args = (tokens.arg1, tokens.arg2)
        else:
            self.function = tokens.left, tokens.right
            self.args = tokens.args[:]
        self.program = tokens.program


    def execute(self, calculator):
        with calculator as loc:
            def f(*args):
                loc.update({arg.name:arg.default.eval(calculator) for arg in self.args if 'default' in arg})
                loc.update({arg.name:v for arg, v in zip(self.args, args)})
                self.program.execute(loc)
                return loc.retval
        calculator.update({self.function:f})


    def __repr__(self):
        if 'function' in self:
            return 'def %s(%s) {%s}'%(self.function, ', '.join(map(str, self.args)), self.program)
        elif 'operator' in self:
            return 'def %s %s %s {%s}'%(self.args[0], self.function, self.args[1], self.program)
        else:
            return 'def %s(%s)%s {%s}'%(self.function[0], ', '.join(map(str, self.args)), self.function[1], self.program)


class ArgumentAction(BaseAction):
    def __init__(self, instring='', loc=0, tokens=[]):
        super(ArgumentAction, self).__init__(instring, loc, tokens)
        self.name = tokens.name
        if 'default' in self:
            self.default = tokens.default


class ProgramSequenceAction(CommandAction):
    '''action for program; program; program...'''
    def __init__(self, instring='', loc=0, tokens=[]):
        super(ProgramSequenceAction, self).__init__(instring, loc, tokens)
        self.program = tokens[:]

    def execute(self, calculator):
        for cmd in self.program:
            context = cmd.execute(calculator)
            if calculator.control in {'break', 'continue', 'return'}:
                break

    def __repr__(self):
        return ';\n'.join(map(str, self.program))

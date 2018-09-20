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
    '''Semantic calculator
    dict_: semantic dictionary
    context: interpretation of variables
    control: control information'''

    def __init__(self, dict_={}, context={}, control=None):
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
        # get the value (interpretation) of variables
        return self.context[x]

    def __enter__(self):
        return self.copy()

    def __exit__(self, *args, **kwargs):
        return True

    def __call__(self, c, *args):
        # get the value of constants
        arity = len(args)
        if c in self.context:
            v = self[c]
            if arity == 0:
                return v
            else:
                if isinstance(v, dict):
                    if arity in v:
                        return v[arity]
                    else:
                        raise Exception('notice the arity!')
                else:
                    return v(*args)

        if c in self.dict_:
            v = self.dict_[c]
            if arity == 0:
                if isinstance(v, dict):
                    return v[2]
                else:
                    return v
            else:
                if isinstance(v, dict):
                    if arity in v:
                        return v[arity](*args)
                    else:
                        raise Exception('notice the arity!')
                else:
                    return v(*args)

        raise NameError('did not find %s'%str(c))

    def eval(self, parseResult):
        pass

    def execute(self, parseResult):
        pass


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
                left = pp.Literal(function['token'][0]) if isinstance(function['token'][0], str) else function['token'][0]
                right = pp.Literal(function['token'][1]) if isinstance(function['token'][1], str) else function['token'][0]
                if 'arity' in function:
                    if function['arity'] == 1:
                        funcExpr.append((left('left') + EXP('arg') +right('right')).setParseAction(function['action']))
                    else:
                        funcExpr.append((left('left') + ((EXP + COMMA) * (function['arity']-1) + EXP)('args') +right('right')).setParseAction(function['action']))
                else:
                    funcExpr.append((left('left') + pp.delimitedList(EXP)('args') +right('right')).setParseAction(function['action']))
            else:
                if isinstance(function['token'], str):
                    function['token'] = pp.Literal(function['token'])
                if 'arity' in function:
                    if function['arity'] == 1:
                        funcExpr.append((function['token']('function') + LPAREN + EXP('arg') + RPAREN).setParseAction(function['action']))
                    else:
                        funcExpr.append((function['token']('function') + LPAREN+ ((EXP + COMMA) * (function['arity']-1) + EXP)('args') + RPAREN).setParseAction(function['action']))
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
        # EXP = mixedExpression(baseExpr, funcExpr, True, optable2oplist(self.operators))

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
        return self.parse(s).eval(calculator = self.calculator)

    def __call__(self, s):
        return self.eval(s)

    def __getstate__(self):
        return self.name, self.grammar, self.calculator

    def __setstate__(self, state):
        self.name, self.grammar, self.calculator = state

arithOpTable = [{'token':'^','assoc':'right'}, {'token':pp.oneOf('+ -'),'arity':1}, pp.oneOf('* /'), pp.oneOf('+ -'), {'token':pp.oneOf('== != < > <= >='), 'action': CompareAction}]
logicOpTable = [{'token':'~', 'arity':1, 'action':UnaryOperatorAction}, {'token':'&', 'action':BinaryOperatorAction}, {'token':'|', 'action':BinaryOperatorAction}]
arithDict = {'True':True, 'False':False, '+': {1:operator.pos, 2:operator.add}, '*': operator.mul, '-':{1:operator.neg, 2:operator.sub}, '/':operator.truediv, '^':operator.pow, '==':operator.eq, '!=':operator.ne, '<':operator.lt, '>':operator.gt, '<=':operator.le, '>=':operator.ge}


class LogicGrammarParser(GrammarParser):
    # Grammar of Logic Language
    def __init__(self, constants=[{'token':NUMBER, 'action':NumberAction}, {'token':pp.quotedString, 'action':StringAction}], variables=[{'token':IDEN, 'action':VariableAction}], quantifier=pp.Keyword('forall') | pp.Keyword('exist')):
        atomicProposition = expression + pp.oneOf('= < > <= >=') + expression
        operators = arithOpTable \
        + [{'token':quantifier('quantifier') + pp.delimitedList(variable)('variables'), 'arity':1, 'action':QuantifierAction}] \
        + logicOpTable
        grammar = GrammarParser(constants, variables, functions=[], operators=operators)
        super(LogicLanguage, self).__init__(grammar)
        self.quantifier = quantifier

commonKeywords = {'if':pp.Keyword('if'), 'elif':pp.Keyword('elif'), 'else':pp.Keyword('else'), 'while':pp.Keyword('while'), 'break':pp.Keyword('break'), 'continue':pp.Keyword('continue'), 'return':pp.Keyword('return'), 'pass':pp.Keyword('pass'), 'def':pp.Keyword('def'), 'print':pp.Keyword('print')}

class ProgrammingGrammarParser(GrammarParser):
    '''programming Language
    '''

    def make_parser(self):
        super(ProgrammingGrammarParser, self).make_parser()
        variable = self.variables[0]['token']
        expression = self.expression
        # parser for program
        self.program = pp.Forward()
        programWithControl = pp.Forward()
        expressionStatement = expression + SEMICOLON
        assignmentStatement = variable('variable') + pp.Suppress('=') + expression('expression') + SEMICOLON
        assignmentStatement.setParseAction(AssignmentAction)
        # define if while break pass statements
        # Keywords = {'if':'if', 'while':'while', 'break':'break', 'pass':'pass', 'def':'def'}
        breakStatement = self.keywords['break']('keyword') + SEMICOLON
        breakStatement.setParseAction(BreakAction)
        continueStatement = self.keywords['continue']('keyword') + SEMICOLON
        continueStatement.setParseAction(ContinueAction)
        passStatement = self.keywords['pass']('keyword') + SEMICOLON
        passStatement.setParseAction(PassAction)
        printStatement = self.keywords['print']('keyword') + pp.delimitedList(expression)('args') + SEMICOLON
        printStatement.setParseAction(PrintAction)
        returnStatement = self.keywords['return']('keyword') + expression('retval') + SEMICOLON
        returnStatement.setParseAction(ReturnAction)

        # atomicStatement = assignmentStatement | breakStatement | continueStatement | passStatement | printStatement | returnStatement
        # block = atomicStatement | LBRACE + self.program + RBRACE

        ifStatement = self.keywords['if']('keyword') + expression('condition') + LBRACE + self.program('program') + RBRACE
        ifStatement.setParseAction(IfAction)
        ifStatementWithControl = self.keywords['if']('keyword') + expression('condition') + LBRACE + programWithControl('program') + RBRACE
        ifStatementWithControl.setParseAction(IfAction)
        # if condition {program} pp.ZeroOrMore(elif condition {program}) else {program}
        # IfelseAction
        whileStatement = self.keywords['while']('keyword') + expression('condition') + LBRACE + programWithControl('program') + RBRACE
        whileStatement.setParseAction(WhileAction)       
        defStatement = self.keywords['def']('keyword') + (variable('function') + LPAREN + pp.delimitedList(variable)('args') + RPAREN | PUNC('left') + pp.delimitedList(variable)('args') + PUNC('right')) + LBRACE + self.program('program') + RBRACE
        defStatement.setParseAction(DefAction)
        self.statements = [ifStatement, whileStatement, defStatement, returnStatement, passStatement, printStatement, assignmentStatement, expressionStatement, LBRACE + self.program + RBRACE]
        statement = pp.MatchFirst(self.statements)
        controlStatements = [breakStatement, continueStatement, ifStatementWithControl, LBRACE + programWithControl + RBRACE]
        statementWithControl = pp.MatchFirst(self.statements + controlStatements)
        programWithControl <<= pp.OneOrMore(statementWithControl).setParseAction(ProgramSequenceAction)
        loadStatement = pp.Keyword('load')('keyword').suppress() + pp.restOfLine('path')
        self.program <<= pp.ZeroOrMore(loadStatement)('loading') + pp.OneOrMore(statement).setParseAction(ProgramSequenceAction)
        self.comment = pp.pythonStyleComment
        self.program.ignore(self.comment)

    def setComment(self, commentStyle='Python'):
        if not hasattr(self, 'program'):
            self.make_parser()
        if self.comment in self.program.ignoreExprs:
            self.program.ignoreExprs.remove(self.comment)
        if commentStyle in {'Python', 'python'}:
            self.comment = pp.pythonStyleComment
        elif commentStyle in {'c', 'C'}:
            self.comment = pp.cStyleComment
        elif commentStyle in {'c++', 'C++'}:
            self.comment = pp.cppStyleComment
        elif commentStyle in {'c\\c++','C\\C++','c\\C++','C\\c++'}:
            self.comment = pp.cppStyleComment | pp.cStyleComment
        else:
            matlabStyleComment = pp.Regex(r"%.*").setName("Matlab (Latex) style comment")
            self.comment = matlabStyleComment
        self.program.ignore(self.comment)

    def parse(self, s):
        if not hasattr(self, 'program'):
            self.make_parser()
        return self.program.parseString(s, parseAll=True)[0]


class ProgrammingLanguage(Language):
    '''programming Language
    '''
    def __init__(self, name='Toy', version='0.0', *args, **kwargs):
        super(ProgrammingLanguage, self).__init__(*args, **kwargs)
        self.version = version

    def make(self):
        grammar = ProgrammingGrammarParser()
        calculator = None
        return ProgrammingLanguage(name=name, grammar=grammar, calculator=calculator)

    def execute(self, s):
        ret = self.parse(s)
        if 'loading' in ret:
            for path in ret.loading:
                self.executeFile(path.strip())
        ret.execute(self.calculator)

    def executeFile(self, filename):
        ret = self.parseFile(filename)
        if 'loading' in ret:
            for path in ret.loading:
                self.executeFile(path.strip())
        ret = ret[-1]
        ret.execute(self.calculator)

    def __call__(self, s):
        self.execute(s)

    def cmdline(self):
        # command line for the programming language
        import time
        print('Welcome. I am %s v%s. It is %s now.'%(self.name, self.verion, time.ctime()))
        prompt = '>>> '
        newlinePrompt = '... '
        while True:
            s = input(prompt)
            if s == 'quit':
                self.calculator.reset()
                break
            if self.matches(s):
                try:
                    ret = self.eval(s)
                    print(ret)
                except Exception as ex:
                    print(ex)
            else:
                while not self.program.matches(s):
                    ss = input(newlinePrompt)
                    if ss == '':
                        raise Exception('command could not be executed!')
                    s += ss
                else:
                    try:
                        self.execute(s)
                    except Exception as ex:
                        print(ex)

    def view(self):
        for k, v in self.calculator.context.items():
            print("%s: %s"%(k, v))
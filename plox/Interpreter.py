from plox.LoxCallable import LoxCallable
from .Expr import *
from .TokenType import *
from .RuntimeError import *
from .Util import runtimeError
from .Stmt import *
from .Environment import Environment

from typing import List

class Interpreter(ExprVisitor, StmtVisitor):
    def __init__(self):
        self.hadRuntimeError = False
        self.environment = Environment()

    def interpret(self, statements: List[Stmt]):
        try:
            # value = self.evaluate(expr)
            # if isinstance(value, str):
            #     value = f'"{value}"'
            # print(value)
            for stmt in statements:
                self.execute(stmt)
        except RuntimeError as e:
            runtimeError(e)
            self.hadRuntimeError = True

    def execute(self, statement: Stmt):
        statement.accept(self)

    def executeBlock(self, statements:List[Stmt], environment: Environment):
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def visitVarStmt(self,stmt:Var):
        value = None
        if stmt.initializer:
            value = self.evaluate(stmt.initializer)
        self.environment.define(stmt.name.lexeme, value)

    def visitLiteralExpr(self,expr: Literal):
        return expr.value

    def visitLogicalExpr(self, expr: Logical):
        left = self.evaluate(expr.left)
        if expr.operator.type == TokenType.OR:
            if self.isTruthy(left):
                return left
        else:
            if not self.isTruthy(left):
                return left
        return self.evaluate(expr.right)

    def evaluate(self, expr: Expr):
        return expr.accept(self)

    def visitExpressionStmt(self,stmt:Expression):
        self.evaluate(stmt.expression)

    def visitIfStmt(self, stmt: If):
        if self.isTruthy(self.evaluate(stmt.condition)):
            self.execute(stmt.thenBranch)
        else:
            self.execute(stmt.elseBranch)
    
    def visitWhileStmt(self, stmt: While):
        while self.isTruthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)
        
    def visitPrintStmt(self,stmt:Print):
        value = self.evaluate(stmt.expression)
        print(value)

    def visitBlockStmt(self,stmt:Block):
        self.executeBlock(stmt.statements, Environment(self.environment))
        return

    def visitGroupingExpr(self,expr:Grouping):
        return self.evaluate(expr.expression)

    def checkNumberOperands(self, operator, *operands):
        allFloats = True
        for operand in operands:
            allFloats &= isinstance(operand, float)
        if allFloats:
            return
        raise RuntimeError(operator, 'Operand must be a number')

    def isTruthy(self, obj):
        if isinstance(obj, bool):
            return obj
        elif obj is None:
            return False
        return True

    def visitUnaryExpr(self,expr:Unary):
        right = self.evaluate(expr.right)

        if expr.operator is TokenType.MINUS:
            self.checkNumberOperands(expr.operator, right)
            right = right * -1.0
        elif expr.operator is TokenType.BANG:
            right = not self.isTruthy(right)

        return right

    def visitCallExpr(self, expr: Call):
        callee = self.evaluate(expr.callee)
        args = list()
        for arg in expr.args:
            args.append(self.evaluate(arg))
        
        if not isinstance(callee, LoxCallable):
            raise RuntimeError(expr.paren, "Can only call functions and classes")
        
        fun: LoxCallable = callee
        if len(args) != fun.arity():
            raise RuntimeError(
                expr.paren, 
                f'Expected {fun.arity()} arguments got {len(args)}.')
        
        return fun.call(self, args)

    def visitVariableExpr(self,expr:Variable):
        return self.environment.get(expr.name)

    def visitAssignExpr(self,expr:Assign):
        value = self.evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    def visitBinaryExpr(self,expr:Binary):
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        opType = expr.operator.type
        if opType is TokenType.GREATER:
            self.checkNumberOperands(opType, left, right)
            return left > right
        elif opType is TokenType.GREATER_EQUAL:
            self.checkNumberOperands(opType, left, right)
            return left >= right
        elif opType is TokenType.LESS:
            self.checkNumberOperands(opType, left, right)
            return left < right
        elif opType is TokenType.LESS_EQUAL:
            self.checkNumberOperands(opType, left, right)
            return left <= right
        elif opType is TokenType.MINUS:
            self.checkNumberOperands(opType, left, right)
            return left - right
        elif opType is TokenType.PLUS:
            isTwoNumbers = isinstance(left, float) and isinstance(right, float)
            isTwoStrings = isinstance(left, str) and isinstance(right, str)
            if not (isTwoStrings or isTwoNumbers):
                raise RuntimeError(opType, "Operands must be two strings or two numbers")
            return left + right
        elif opType is TokenType.SLASH:
            self.checkNumberOperands(opType, left, right)
            if right == 0:
                raise RuntimeError(opType, "Divide by zero is not allowed")
            return left / right
        elif opType is TokenType.STAR:
            self.checkNumberOperands(opType, left, right)
            return left * right
        elif opType is TokenType.BANG_EQUAL:
            # print(f"left == right = {left == right}")
            return not (left == right)
        elif opType is TokenType.EQUAL_EQUAL:
            return (left == right)
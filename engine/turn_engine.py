# -*- coding: utf-8 -*-
"""Gestione riutilizzabile dell'assegnazione manuale del turno."""

class TurnEngine(object):
    VALID_SYMBOLS = ('X', 'O')

    def __init__(self, assigned_symbol=None, assignment_count=0):
        self.assigned_symbol = assigned_symbol
        self.assignment_count = assignment_count

    def award_turn(self, symbol):
        if symbol not in self.VALID_SYMBOLS:
            return False, 'Simbolo non valido.'
        self.assigned_symbol = symbol
        self.assignment_count += 1
        return True, ''

    def can_play(self, symbol):
        return self.assigned_symbol == symbol

    def consume_turn(self):
        consumed = self.assigned_symbol
        self.assigned_symbol = None
        return consumed

    def to_dict(self):
        return {
            'assigned_symbol': self.assigned_symbol,
            'assignment_count': self.assignment_count
        }

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        return cls(data.get('assigned_symbol'), data.get('assignment_count', 0))

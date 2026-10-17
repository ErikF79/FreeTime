# -*- coding: utf-8 -*-
"""Regole riutilizzabili per le varianti dei giochi FreeTime."""

class GameRuleSet(object):
    CLASSIC = 'classic'
    EARNED_TURN = 'earned_turn'
    DESTRUCTIVE = 'destructive'

    def __init__(self, ruleset_id, name, description,
                 alternate_turns=True, turn_must_be_earned=False,
                 removal_enabled=False, max_removals_per_player=0,
                 enabled=False):
        self.ruleset_id = ruleset_id
        self.name = name
        self.description = description
        self.alternate_turns = alternate_turns
        self.turn_must_be_earned = turn_must_be_earned
        self.removal_enabled = removal_enabled
        self.max_removals_per_player = max_removals_per_player
        self.enabled = enabled

    def to_dict(self):
        return {
            'ruleset_id': self.ruleset_id,
            'name': self.name,
            'description': self.description,
            'alternate_turns': self.alternate_turns,
            'turn_must_be_earned': self.turn_must_be_earned,
            'removal_enabled': self.removal_enabled,
            'max_removals_per_player': self.max_removals_per_player,
            'enabled': self.enabled
        }

    @classmethod
    def classic(cls):
        return cls(cls.CLASSIC, 'Classico',
                   'Alternanza tradizionale tra X e O.',
                   alternate_turns=True, enabled=True)

    @classmethod
    def earned_turn(cls):
        return cls(cls.EARNED_TURN, 'Turno conquistato',
                   'Il turno viene assegnato dopo una prova o un obiettivo.',
                   alternate_turns=False, turn_must_be_earned=True,
                   enabled=True)

    @classmethod
    def destructive(cls):
        return cls(cls.DESTRUCTIVE, 'Distruttivo',
                   'Inserisci il tuo simbolo oppure rimuovi quello avversario.',
                   alternate_turns=True, removal_enabled=True,
                   max_removals_per_player=2, enabled=True)

    @classmethod
    def catalog(cls):
        return [cls.classic(), cls.earned_turn(), cls.destructive()]

    @classmethod
    def get(cls, ruleset_id):
        for item in cls.catalog():
            if item.ruleset_id == ruleset_id:
                return item
        return None

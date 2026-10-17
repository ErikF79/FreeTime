# -*- coding: utf-8 -*-
class GameMode(object):
    VS_PC='vs_pc'; DUEL='duel'; TOURNAMENT='tournament'; TEAM='team'
    LABELS={VS_PC:'Contro il PC',DUEL:'Coppia',TOURNAMENT:'Torneo',TEAM:'A squadre'}
    @classmethod
    def is_valid(cls,value): return value in cls.LABELS

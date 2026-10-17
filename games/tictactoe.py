# -*- coding: utf-8 -*-
from games.base_game import BaseGame
from games.game_ruleset import GameRuleSet
from engine.turn_engine import TurnEngine

class TicTacToeGame(BaseGame):
    WINNING_LINES=((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))

    def __init__(self,ruleset_id=GameRuleSet.CLASSIC):
        BaseGame.__init__(self,'tictactoe','Tris','La classica sfida su griglia 3 per 3.','Strategia',2,2,'XO','ready')
        self.ruleset=GameRuleSet.get(ruleset_id) or GameRuleSet.classic()
        self.reset()

    def reset(self):
        self.board=['']*9
        self.current_symbol='X' if not self.ruleset.turn_must_be_earned else None
        self.status='active'; self.winner=''; self.winning_line=[]; self.moves=0
        self.turn_engine=TurnEngine()
        self.removals_used={'X':0,'O':0}

    def award_turn(self,symbol):
        if not self.ruleset.turn_must_be_earned:
            return False,'Questo RuleSet usa turni automatici.'
        if self.status!='active': return False,'La partita è conclusa.'
        ok,msg=self.turn_engine.award_turn(symbol)
        if ok: self.current_symbol=symbol
        return ok,msg

    def opponent(self,symbol): return 'O' if symbol=='X' else 'X'

    def removals_left(self,symbol):
        if not self.ruleset.removal_enabled: return 0
        return max(0,self.ruleset.max_removals_per_player-self.removals_used.get(symbol,0))

    def can_remove(self,cell,symbol=None):
        symbol=symbol or self.current_symbol
        return (self.ruleset.removal_enabled and self.status=='active' and
                isinstance(cell,int) and 0<=cell<=8 and
                self.removals_left(symbol)>0 and self.board[cell]==self.opponent(symbol))

    def remove_opponent(self,cell):
        if self.status!='active': return False,'La partita è conclusa.'
        symbol=self.current_symbol
        if not self.ruleset.removal_enabled: return False,'La cancellazione non è prevista da questo RuleSet.'
        if self.removals_left(symbol)<=0: return False,'Hai già utilizzato le due cancellazioni disponibili.'
        if not isinstance(cell,int) or cell<0 or cell>8: return False,'Cella non valida.'
        if self.board[cell]!=self.opponent(symbol): return False,'Puoi cancellare solo un simbolo avversario.'
        self.board[cell]=''; self.removals_used[symbol]=self.removals_used.get(symbol,0)+1; self.moves+=1
        self.switch_after_action()
        return True,''

    def make_move(self,cell):
        if self.status!='active': return False,'La partita è conclusa.'
        if self.ruleset.turn_must_be_earned and not self.current_symbol:
            return False,'Il gestore deve prima assegnare il turno.'
        if not isinstance(cell,int) or cell<0 or cell>8: return False,'Cella non valida.'
        if self.board[cell]: return False,'La cella è già occupata.'
        symbol=self.current_symbol; self.board[cell]=symbol; self.moves+=1
        line=self.check_winner(symbol)
        if line:
            self.status='won'; self.winner=symbol; self.winning_line=list(line)
        elif self.ruleset.turn_must_be_earned:
            if self.board_full(): self.status='draw'
            else: self.turn_engine.consume_turn(); self.current_symbol=None
        else:
            self.switch_after_action()
        return True,''

    def switch_after_action(self):
        if self.status!='active': return
        if self.ruleset.alternate_turns:
            self.current_symbol=self.opponent(self.current_symbol)
        if self.board_full() and not self.has_destructive_action(self.current_symbol):
            self.status='draw'

    def has_destructive_action(self,symbol):
        return self.removals_left(symbol)>0 and self.opponent(symbol) in self.board

    def board_full(self): return all(self.board)

    def check_winner(self,symbol):
        for line in self.WINNING_LINES:
            if all(self.board[i]==symbol for i in line): return line
        return None

    def is_draw(self): return self.status=='draw'
    def available_moves(self): return [i for i,v in enumerate(self.board) if not v]

    def export_state(self):
        return {'board':self.board,'current_symbol':self.current_symbol,'status':self.status,
                'winner':self.winner,'winning_line':self.winning_line,'moves':self.moves,
                'ruleset_id':self.ruleset.ruleset_id,'turn_engine':self.turn_engine.to_dict(),
                'removals_used':self.removals_used}

    @classmethod
    def from_state(cls,state):
        game=cls(state.get('ruleset_id',GameRuleSet.CLASSIC)); game.board=list(state.get('board',['']*9))
        game.current_symbol=state.get('current_symbol'); game.status=state.get('status','active')
        game.winner=state.get('winner',''); game.winning_line=list(state.get('winning_line',[])); game.moves=state.get('moves',0)
        game.turn_engine=TurnEngine.from_dict(state.get('turn_engine'))
        game.removals_used=dict(state.get('removals_used',{'X':0,'O':0}))
        return game

# -*- coding: utf-8 -*-
from games.base_game import BaseGame
from games.game_ruleset import GameRuleSet
from engine.turn_engine import TurnEngine

class Connect4Game(BaseGame):
    ROWS=6; COLUMNS=7
    def __init__(self,ruleset_id=GameRuleSet.CLASSIC):
        BaseGame.__init__(self,'connect4','Forza 4','Allinea quattro pedine in orizzontale, verticale o diagonale.','Strategia',2,2,'4','ready')
        self.ruleset=GameRuleSet.get(ruleset_id) or GameRuleSet.classic(); self.reset()
    def reset(self):
        self.board=[['' for _ in range(self.COLUMNS)] for _ in range(self.ROWS)]
        self.current_symbol='X' if not self.ruleset.turn_must_be_earned else None
        self.status='active';self.winner='';self.winning_cells=[];self.moves=0;self.turn_engine=TurnEngine();self.removals_used={'X':0,'O':0}
    def opponent(self,s):return 'O' if s=='X' else 'X'
    def award_turn(self,symbol):
        if not self.ruleset.turn_must_be_earned or self.status!='active':return False,'Turno non assegnabile.'
        ok,msg=self.turn_engine.award_turn(symbol)
        if ok:self.current_symbol=symbol
        return ok,msg
    def removals_left(self,symbol):
        if not self.ruleset.removal_enabled:return 0
        return max(0,self.ruleset.max_removals_per_player-self.removals_used.get(symbol,0))
    def find_available_row(self,column):
        if not isinstance(column,int) or column<0 or column>=self.COLUMNS:return None
        for row in range(self.ROWS-1,-1,-1):
            if not self.board[row][column]:return row
        return None
    def is_column_full(self,column):return self.find_available_row(column) is None
    def available_columns(self):return [c for c in range(self.COLUMNS) if not self.is_column_full(c)]
    def drop_piece(self,column):
        if self.status!='active':return False,'La partita è conclusa.'
        if self.ruleset.turn_must_be_earned and not self.current_symbol:return False,'Assegna prima il turno.'
        row=self.find_available_row(column)
        if row is None:return False,'La colonna è piena o non valida.'
        symbol=self.current_symbol;self.board[row][column]=symbol;self.moves+=1
        line=self.check_winner(symbol)
        if line:self.status='won';self.winner=symbol;self.winning_cells=line
        elif self.board_full() and not self.ruleset.removal_enabled:self.status='draw'
        else:self.finish_action()
        return True,''
    def removable_cells(self,symbol=None):
        symbol=symbol or self.current_symbol
        if not self.ruleset.removal_enabled or self.removals_left(symbol)<=0:return []
        enemy=self.opponent(symbol)
        return [[r,c] for r in range(self.ROWS) for c in range(self.COLUMNS) if self.board[r][c]==enemy]
    def remove_opponent(self,row,column):
        if self.status!='active':return False,'La partita è conclusa.'
        symbol=self.current_symbol
        if not self.ruleset.removal_enabled:return False,'La cancellazione non è disponibile.'
        if self.removals_left(symbol)<=0:return False,'Hai esaurito le due cancellazioni.'
        if not isinstance(row,int) or not isinstance(column,int) or row<0 or row>=self.ROWS or column<0 or column>=self.COLUMNS:return False,'Cella non valida.'
        if self.board[row][column]!=self.opponent(symbol):return False,'Puoi rimuovere soltanto una pedina avversaria.'
        self.board[row][column]='';self.compact_column(column);self.removals_used[symbol]=self.removals_used.get(symbol,0)+1;self.moves+=1
        own=self.check_winner(symbol);enemy=self.check_winner(self.opponent(symbol))
        if own:self.status='won';self.winner=symbol;self.winning_cells=own
        elif enemy:self.status='won';self.winner=self.opponent(symbol);self.winning_cells=enemy
        else:self.finish_action()
        return True,''
    def compact_column(self,column):
        values=[self.board[r][column] for r in range(self.ROWS) if self.board[r][column]]
        blanks=self.ROWS-len(values)
        for r in range(self.ROWS):self.board[r][column]='' if r<blanks else values[r-blanks]
    def finish_action(self):
        if self.status!='active':return
        if self.ruleset.turn_must_be_earned:self.turn_engine.consume_turn();self.current_symbol=None
        else:self.current_symbol=self.opponent(self.current_symbol)
        if self.board_full() and not self.removable_cells(self.current_symbol):self.status='draw'
    def board_full(self):return all(self.board[r][c] for r in range(self.ROWS) for c in range(self.COLUMNS))
    def check_winner(self,symbol):
        for row in range(self.ROWS):
            for col in range(self.COLUMNS):
                for dr,dc in ((0,1),(1,0),(1,1),(1,-1)):
                    cells=[[row+dr*k,col+dc*k] for k in range(4)]
                    if all(0<=r<self.ROWS and 0<=c<self.COLUMNS and self.board[r][c]==symbol for r,c in cells):return cells
        return []
    def export_state(self):return {'board':self.board,'current_symbol':self.current_symbol,'status':self.status,'winner':self.winner,'winning_cells':self.winning_cells,'moves':self.moves,'ruleset_id':self.ruleset.ruleset_id,'turn_engine':self.turn_engine.to_dict(),'removals_used':self.removals_used}
    @classmethod
    def from_state(cls,state):
        g=cls(state.get('ruleset_id',GameRuleSet.CLASSIC));g.board=[list(x) for x in state.get('board',[])];g.current_symbol=state.get('current_symbol');g.status=state.get('status','active');g.winner=state.get('winner','');g.winning_cells=[list(x) for x in state.get('winning_cells',[])];g.moves=state.get('moves',0);g.turn_engine=TurnEngine.from_dict(state.get('turn_engine'));g.removals_used=dict(state.get('removals_used',{'X':0,'O':0}));return g

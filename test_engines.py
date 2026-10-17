from engine.game_modes import GameMode
from engine.match_engine import Match,MatchEngine
from engine.team_engine import Team,TeamEngine
assert TeamEngine.validate(Team('Blu',['p1']),{'p1'})==[]
assert MatchEngine.validate(Match('tictactoe',GameMode.DUEL,['p1','p2']))==[]
print('TEAM ENGINE: PASS');print('MATCH ENGINE: PASS');print('MODALITA: 4')

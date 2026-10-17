from games.tictactoe import TicTacToeGame
from games.game_ruleset import GameRuleSet

g=TicTacToeGame(GameRuleSet.EARNED_TURN)
assert g.current_symbol is None
assert not g.make_move(0)[0]
assert g.award_turn('X')[0]
assert g.make_move(0)[0]
assert g.board[0]=='X' and g.current_symbol is None
assert g.award_turn('X')[0]
assert g.make_move(1)[0]
assert g.board[1]=='X' and g.current_symbol is None
assert g.award_turn('O')[0]
assert g.make_move(4)[0]
assert g.board[4]=='O'
assert g.award_turn('X')[0]
assert g.make_move(2)[0]
assert g.status=='won' and g.winner=='X'
print('EARNED TURN GAMEPLAY: PASS')

from games.tictactoe import TicTacToeGame
from games.game_ruleset import GameRuleSet

g=TicTacToeGame(GameRuleSet.DESTRUCTIVE)
assert g.ruleset.removal_enabled
assert g.removals_left('X')==2 and g.removals_left('O')==2
assert g.make_move(0)[0]          # X places, O turn
assert g.make_move(4)[0]          # O places, X turn
assert g.remove_opponent(4)[0]    # X removes O, O turn
assert g.board[4]=='' and g.removals_left('X')==1
assert g.make_move(4)[0]          # O places again, X turn
assert g.remove_opponent(4)[0]    # X second removal
assert g.removals_left('X')==0
assert g.make_move(4)[0]          # O places, X turn
assert not g.remove_opponent(4)[0]
assert g.board[4]=='O'
# own symbol cannot be removed
g2=TicTacToeGame(GameRuleSet.DESTRUCTIVE)
g2.make_move(0)                   # X, now O
assert not g2.remove_opponent(1)[0]
# Verify valid O removal after X symbol exists
assert g2.remove_opponent(0)[0]
assert g2.board[0]=='' and g2.current_symbol=='X'
print('DESTRUCTIVE GAMEPLAY: PASS')

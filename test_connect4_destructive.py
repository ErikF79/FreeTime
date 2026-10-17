from games.connect4 import Connect4Game
from games.game_ruleset import GameRuleSet

g = Connect4Game(GameRuleSet.DESTRUCTIVE)
assert g.removals_left('X') == 2
assert g.removals_left('O') == 2

assert g.drop_piece(0)[0]             # X in basso
assert g.drop_piece(0)[0]             # O sopra, turno X
assert g.remove_opponent(4, 0)[0]     # X rimuove O
assert g.board[5][0] == 'X'
assert g.board[4][0] == ''
assert g.removals_left('X') == 1
assert g.current_symbol == 'O'

assert g.remove_opponent(5, 0)[0]     # O rimuove X
assert g.board[5][0] == ''
assert g.removals_left('O') == 1
assert g.current_symbol == 'X'

assert g.drop_piece(1)[0]             # X
assert g.drop_piece(1)[0]             # O, turno X
assert g.remove_opponent(4, 1)[0]     # seconda rimozione X
assert g.removals_left('X') == 0

# Predisposizione controllata: X non può effettuare una terza rimozione.
g.current_symbol = 'X'
g.board[5][2] = 'O'
assert not g.remove_opponent(5, 2)[0]
assert g.board[5][2] == 'O'

state = g.export_state()
h = Connect4Game.from_state(state)
assert h.removals_used == g.removals_used
assert h.board == g.board
print('CONNECT4 DESTRUCTIVE: PASS')

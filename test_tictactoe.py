from games.tictactoe import TicTacToeGame

g=TicTacToeGame(); assert g.board==['']*9
assert g.make_move(0)[0]; assert g.current_symbol=='O'
assert not g.make_move(0)[0]
g=TicTacToeGame()
for c in (0,3,1,4,2): assert g.make_move(c)[0]
assert g.status=='won' and g.winner=='X' and g.winning_line==[0,1,2]
g=TicTacToeGame()
for c in (0,1,2,4,3,5,7,6,8): assert g.make_move(c)[0]
assert g.status=='draw'
print('TICTACTOE ENGINE: PASS')

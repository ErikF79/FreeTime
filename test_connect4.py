from games.connect4 import Connect4Game

g=Connect4Game()
assert len(g.board)==6 and len(g.board[0])==7
assert g.drop_piece(0)[0] and g.board[5][0]=='X'
assert g.drop_piece(0)[0] and g.board[4][0]=='O'
# horizontal X win
g=Connect4Game()
for c in (0,0,1,1,2,2,3): assert g.drop_piece(c)[0]
assert g.status=='won' and g.winner=='X' and g.winning_cells==[[5,0],[5,1],[5,2],[5,3]]
# vertical X win
g=Connect4Game()
for c in (0,1,0,1,0,1,0): assert g.drop_piece(c)[0]
assert g.status=='won' and g.winner=='X'
# diagonal rising X win
g=Connect4Game()
for c in (0,1,1,2,4,2,2,3,4,3,5,3,3): assert g.drop_piece(c)[0]
assert g.status=='won' and g.winner=='X'
# full column rejected
g=Connect4Game()
for _ in range(6): assert g.drop_piece(6)[0]
assert not g.drop_piece(6)[0]
# export/import
a=g.export_state(); b=Connect4Game.from_state(a); assert b.board==g.board and b.moves==g.moves
print('CONNECT4 ENGINE: PASS')

from player_lifecycle import *
from achievement_engine import unlocked_for
p=[{'id':'1','name':' Mario   Rossi '}]
assert migrate_players(p) and p[0]['enabled'];assert find_by_name(p,'mario rossi');toggle_player(p,'1');assert enabled_players(p)==[];assert find_by_name(p,'MARIO ROSSI')
r=[{'participant_ids':['1'],'winner_id':'1','status':'won','game_id':'tictactoe'}];assert unlocked_for('1',r)[0]['id']=='first_win'
print('V0.9B PLAYER LIFECYCLE: PASS')

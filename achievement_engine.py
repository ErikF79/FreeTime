DEFINITIONS=(('first_win','Primo successo','Vinci la prima partita'),('ten_games','Primi dieci','Gioca 10 partite'),('fifty_games','Veterano','Gioca 50 partite'),('tris_master','Maestro del Tris','Vinci 10 partite a Tris'),('connect4_master','Campione Forza 4','Vinci 10 partite a Forza 4'))
def unlocked_for(pid,results):
 played=[r for r in results if pid in r.get('participant_ids',[])];wins=[r for r in played if r.get('winner_id')==pid]
 checks={'first_win':len(wins)>=1,'ten_games':len(played)>=10,'fifty_games':len(played)>=50,'tris_master':len([r for r in wins if r.get('game_id')=='tictactoe'])>=10,'connect4_master':len([r for r in wins if r.get('game_id')=='connect4'])>=10}
 return [{'id':i,'name':n,'description':d} for i,n,d in DEFINITIONS if checks[i]]

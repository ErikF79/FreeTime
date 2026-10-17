import uuid
from datetime import datetime
from engine.game_modes import GameMode
class Match(object):
 def __init__(self,game_id,mode,participant_ids=None,team_ids=None):self.match_id=uuid.uuid4().hex;self.game_id=game_id;self.mode=mode;self.participant_ids=list(participant_ids or []);self.team_ids=list(team_ids or []);self.status='configured';self.created_at=datetime.now().isoformat(timespec='seconds')
 def to_dict(self):return {'id':self.match_id,'game_id':self.game_id,'mode':self.mode,'participant_ids':self.participant_ids,'team_ids':self.team_ids,'status':self.status,'created_at':self.created_at}
class MatchEngine(object):
 @staticmethod
 def validate(m):
  e=[]
  if not m.game_id:e.append('Seleziona un gioco.')
  if not GameMode.is_valid(m.mode):e.append('Modalità non valida.');return e
  p=len(m.participant_ids);t=len(m.team_ids)
  if m.mode==GameMode.VS_PC and p!=1:e.append('Contro il PC richiede un giocatore.')
  elif m.mode==GameMode.DUEL and p!=2:e.append('La modalità Coppia richiede due giocatori.')
  elif m.mode==GameMode.TOURNAMENT and p<3:e.append('Il Torneo richiede almeno tre giocatori.')
  elif m.mode==GameMode.TEAM and t<2:e.append('La modalità A squadre richiede almeno due squadre.')
  return e

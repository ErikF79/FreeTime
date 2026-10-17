import uuid
class Team(object):
 def __init__(self,name,player_ids=None,team_id=None,score=0):self.team_id=team_id or uuid.uuid4().hex;self.name=name.strip();self.player_ids=list(player_ids or []);self.score=score
 def to_dict(self):return {'id':self.team_id,'name':self.name,'player_ids':self.player_ids,'score':self.score}
class TeamEngine(object):
 @staticmethod
 def validate(t,ids):
  e=[]
  if not t.name:e.append('Il nome della squadra è obbligatorio.')
  if not t.player_ids:e.append('Seleziona almeno un giocatore.')
  if any(x not in ids for x in t.player_ids):e.append('La squadra contiene giocatori non disponibili.')
  return e

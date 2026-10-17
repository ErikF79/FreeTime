def normalized_name(value): return ' '.join((value or '').strip().lower().split())
def migrate_players(players):
 changed=False
 for p in players:
  if 'enabled' not in p:p['enabled']=True;changed=True
 return changed
def find_by_name(players,name):
 target=normalized_name(name);return next((p for p in players if normalized_name(p.get('name'))==target),None)
def enabled_players(players):return [p for p in players if p.get('enabled',True)]
def toggle_player(players,pid):
 for p in players:
  if p.get('id')==pid:p['enabled']=not p.get('enabled',True);return p
 return None

# -*- coding: utf-8 -*-
class BaseGame(object):
    def __init__(self,game_id,name,description,category,min_players,max_players,icon,status='planned'):
        self.game_id=game_id; self.name=name; self.description=description
        self.category=category; self.min_players=min_players; self.max_players=max_players
        self.icon=icon; self.catalog_status=status
    def player_label(self):
        if self.min_players==self.max_players: return '{0} giocatori'.format(self.min_players)
        return '{0}-{1} giocatori'.format(self.min_players,self.max_players)

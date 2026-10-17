from games.connect4 import Connect4Game
from games.game_ruleset import GameRuleSet
g=Connect4Game(GameRuleSet.EARNED_TURN);assert g.current_symbol is None;assert not g.drop_piece(0)[0];assert g.award_turn('X')[0];assert g.drop_piece(0)[0];assert g.current_symbol is None;assert g.award_turn('X')[0];assert g.drop_piece(1)[0];print('CONNECT4 EARNED TURN: PASS')

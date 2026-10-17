from games.game_ruleset import GameRuleSet
items=GameRuleSet.catalog()
assert len(items)==3
assert items[0].enabled is True
assert items[1].turn_must_be_earned is True
assert items[2].removal_enabled is True
assert items[2].max_removals_per_player==2
print('GAMERULESET: PASS')

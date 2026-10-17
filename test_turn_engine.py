from engine.turn_engine import TurnEngine
engine=TurnEngine()
assert engine.assigned_symbol is None
assert engine.award_turn('X')[0]
assert engine.can_play('X') and not engine.can_play('O')
assert engine.consume_turn()=='X'
assert engine.assigned_symbol is None
assert engine.award_turn('O')[0]
assert engine.assignment_count==2
assert not engine.award_turn('Z')[0]
print('TURN ENGINE: PASS')

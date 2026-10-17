import os
import sys
import tempfile
import types

class DummyFlask(object):
    def __init__(self, *args, **kwargs):
        self.secret_key = None
    def route(self, *args, **kwargs):
        def decorator(function):
            return function
        return decorator

flask_stub = types.ModuleType('flask')
flask_stub.Flask = DummyFlask
flask_stub.flash = lambda *args, **kwargs: None
flask_stub.redirect = lambda value: value
flask_stub.render_template = lambda *args, **kwargs: None
flask_stub.request = types.SimpleNamespace(args={}, form={})
flask_stub.session = {}
flask_stub.url_for = lambda endpoint, **kwargs: endpoint
flask_stub.Response = object
flask_stub.send_file = lambda *args, **kwargs: None
flask_stub.jsonify = lambda *args, **kwargs: None
sys.modules['flask'] = flask_stub

import app as module

players = [
    {'id': 'p1', 'name': 'Erik'},
    {'id': 'p2', 'name': 'Samuele'}
]
results = [
    {'participant_ids': ['p1', 'p2'], 'winner_id': 'p1', 'status': 'won'},
    {'participant_ids': ['p1', 'p2'], 'winner_id': None, 'status': 'draw'}
]
old_players = module.PLAYERS
fd, path = tempfile.mkstemp(suffix='.json')
os.close(fd)
try:
    module.PLAYERS = path
    module.save(path, players)
    board = module.leaderboard_data(results)
    assert board[0]['id'] == 'p1'
    assert board[0]['points'] == 4
    assert board[1]['points'] == 1
    assert module.result_points(results[1], 'p2') == 1
    print('V0.9 ANALYTICS: PASS')
finally:
    module.PLAYERS = old_players
    os.remove(path)

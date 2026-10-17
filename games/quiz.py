# -*- coding: utf-8 -*-
from games.base_game import BaseGame

class QuizGame(BaseGame):
    def __init__(self):
        BaseGame.__init__(self, 'quiz', 'Quizzone',
                           'Rispondi alle domande a squadre o singolarmente: quante ne indovini?',
                           'Cultura generale', 1, 8, 'QZ', 'ready')
        self.question = ''
        self.options = []
        self.correct_index = None
        self.status = 'active'
        self.turn_index = 0
        self.participant_ids = []
        self.scores = {}
        self.questions_played = 0
        self.last_message = ''

    def setup(self, participant_ids, mode='classico'):
        self.status = 'active'
        self.mode = mode
        self.turn_index = 0
        self.participant_ids = list(participant_ids)
        self.scores = {pid: 0 for pid in self.participant_ids}
        self.questions_played = 0
        self.question = ''
        self.options = []
        self.correct_index = None
        self.last_message = ''

    def current_player(self):
        if not self.participant_ids: return None
        return self.participant_ids[self.turn_index % len(self.participant_ids)]

    def advance_turn(self):
        if self.participant_ids:
            self.turn_index = (self.turn_index + 1) % len(self.participant_ids)

    def load_question(self, content):
        if content:
            self.question = content.get('question', '')
            self.options = list(content.get('options', []))
            self.correct_index = content.get('correct_index')
            return True
        self.question = ''
        self.options = []
        self.correct_index = None
        return False

    def answer(self, index):
        if self.status != 'active': return False, 'La manche è conclusa.'
        pid = self.current_player()
        correct = (index == self.correct_index)
        if correct and pid: self.scores[pid] = self.scores.get(pid, 0) + 1
        self.questions_played += 1
        self.last_message = 'Esatto!' if correct else 'Risposta sbagliata.'
        if not (self.mode == 'turno_conquistato' and correct):
            self.advance_turn()
        return correct, self.last_message

    def export_state(self):
        return {'question': self.question, 'options': self.options, 'correct_index': self.correct_index,
                'status': self.status, 'mode': getattr(self,'mode','classico'),
                'turn_index': self.turn_index, 'participant_ids': self.participant_ids,
                'scores': self.scores, 'questions_played': self.questions_played, 'last_message': self.last_message}

    @classmethod
    def from_state(cls, state):
        game = cls()
        game.question = state.get('question', '')
        game.options = list(state.get('options', []))
        game.correct_index = state.get('correct_index')
        game.status = state.get('status', 'active')
        game.mode = state.get('mode', 'classico')
        game.turn_index = state.get('turn_index', 0)
        game.participant_ids = list(state.get('participant_ids', []))
        game.scores = dict(state.get('scores', {}))
        game.questions_played = state.get('questions_played', 0)
        game.last_message = state.get('last_message', '')
        return game

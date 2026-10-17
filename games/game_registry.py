from games.tictactoe import TicTacToeGame
from games.connect4 import Connect4Game
from games.wheel import WheelGame
from games.memory import MemoryGame
from games.mastermind import MastermindGame
from games.hangman import HangmanGame
from games.charades import CharadesGame
from games.sequence import SequenceGame
from games.quiz import QuizGame
from games.crossword import CrosswordGame

def get_game_info():
    result=[]
    for g in (TicTacToeGame(),Connect4Game(),WheelGame(),MemoryGame(),MastermindGame(),
              HangmanGame(),CharadesGame(),SequenceGame(),QuizGame(),CrosswordGame()):
        result.append({'game_id':g.game_id,'name':g.name,'description':g.description,
                       'category':g.category,'icon':g.icon,'status':g.catalog_status,
                       'player_label':g.player_label()})
    return result

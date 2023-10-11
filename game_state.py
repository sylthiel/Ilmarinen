import chess


class GameState:
    def __init__(self, fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'):
        # self.fen = fen
        self.board = chess.Board(fen)

    def get_legal_moves(self):
        return self.board.legal_moves

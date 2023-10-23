import chess.pgn

with open('ocgdb_query_dump.pgn') as pgn:
    while True:
        game = chess.pgn.read_game(pgn)
        print(game)

        break
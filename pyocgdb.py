from typing import List, Dict, Any, Optional
import asyncio


class OpenChessGameDatabase:
    def __init__(self):
        self.databases = {}

    @staticmethod
    def create_cli_args(executable: str, command: Optional[str] = None, *args, **kwargs):
        """
        :param executable: the path to the executable
        :param command: the inital command
        :param args:
        :param kwargs:
        :return: parsed list of the command and each of its arguments
        """
        cli_args = [executable, command] if command is not None else [executable]
        for arg in args:
            if isinstance(arg, (list, set, tuple)):
                # 'list-like' objects, just extend the cli_args
                cli_args.extend(arg)
            elif isinstance(arg, (dict,)):
                # 'dict-like' objects, flatten key-value pairs into individual strings
                for key, value in arg.items():
                    cli_args.append(str(key))
                    if value is not None:
                        cli_args.append(str(value))
            else:
                # 'simpleton' objects, just append them to cli_args
                cli_args.append(str(arg))

        for key, arg in kwargs.items():
            if isinstance(arg, (list, set, tuple)):
                # 'list-like' objects, just extend the cli_args
                cli_args.append(f"-{key}")
                cli_args.extend(arg)
            elif isinstance(arg, (dict,)):
                # 'dict-like' objects, flatten key-value pairs into individual strings
                # dict-line objects are not expected to make use of the dict parameter name
                # so options = options={'cpu':4, 'o': 'moves2'}
                # should become "-cpu", "4", "-o", "moves2"
                # instead of "options", "-cpu", "4" ...
                for k, v in arg.items():
                    cli_args.append(f"-{str(k)}")
                    if v is not None:
                        # this checks is done for options that do not require a value
                        # like -discardcomments
                        cli_args.append(str(v))
            else:
                cli_args.append(f"-{key}")
                cli_args.append(str(arg))

        return cli_args

    async def create(self, pgn_files: List[str], file_name: str, options: Dict[str, Any] = None):
        args = OpenChessGameDatabase.create_cli_args('ocgdb', '-create',
                                                     pgn=pgn_files,
                                                     db=file_name, options=options)
        print(args)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        return stdout, stderr, process.returncode

    def merge(self, pgn_files: List[str], options: Dict[str, Any] = None):
        pass

    def export(self, destination_pgn: str):
        pass

    def duplicate_check(self, options: Dict[str, Any] = None):
        pass

    def benchmark(self):
        pass

    def get_game(self, game_id: int):
        pass

    async def execute_query_async(self, fen: Optional[str], db: str, destination: str = 'ocgdb_query_dump.pgn'):
        # obviously placeholder
        arguments = OpenChessGameDatabase.create_cli_args('ocgdb',
                                                          options={
                                                              'cpu': 4,
                                                              'db': db,
                                                              'q': f"fen[{fen}]",
                                                              'r': destination
                                                          })
        print(' '.join(arguments))
        process = await asyncio.create_subprocess_exec(
            *arguments,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        return stdout, stderr, process.returncode


class Query:
    def __init__(self, **kwargs):
        pass

    def construct(self):
        #  find all positions having 3 White Queens
        # Q = 3
        #  3 White Queens, written in inverted way
        # 3 = Q
        #  Find all positions having two Black Rooks in the middle squares
        # r[e4, e5, d4, d5] = 2
        #  White Pawns in d4, e5, f4, g4, Black King in b7
        # P[d4, e5, f4, g4] = 4 and kb7
        #  black Pawns in column b, row 5, from square a2 to d2 must be smaller than 4
        # p[b, 5, a2 - d2] < 4
        #  Black Pawns in column c more than 1
        # pc > 1
        #  White Pawns in row 3 from 2
        # P3 >= 2
        #  Two Bishops in column c, d, e, f
        # B[c-f] + b[c-f] = 2
        #  There are 5 white pieces in row 6
        # white6 = 5
        #  There are 5 white pieces in row 6 - another way to write
        # white[6] = 5
        #  total back pieces in columns from a to c is more than 8
        # black[a-c] > 8
        #  Find by a fen string
        # fen[r2qkb1r1p2npppp3p34Pb22BB4P71P3PPPRN1Q1RK1 b kq - 0 12]
        #  Find by some fen strings
        # fen[rnbqkbnrpp2pppp2p53pP33P48PPP2PPPRNBQKBNR b KQkq - 0 3,
        # rn1qkbnrpp2pppp2p53pPb23P45N2PPP2PPPRNBQKB1R b KQkq - 1 4]
        return

    def execute(self):
        pass


async def main():
    h = OpenChessGameDatabase()
    out, err, code = await h.create(pgn_files=['nepo.pgn'],
                                    file_name='nepo2.ocgdb.db3',
                                    options={
                                        'cpu': 4,
                                        'o': 'moves2'
                                    })
    print(out)
    print(err)
    print(code)

    sicilian_defense = 'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2'
    out, err, code = await h.execute_query_async(sicilian_defense, 'nepo.ocgdb.db3')
    print (out, err, code)
    # printing or processing result here


asyncio.run(main())

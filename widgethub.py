from enum import Enum
from typing import Callable
from uuid import uuid4
import chess, chess.pgn


class Event(Enum):
    GameMove = "GameMove"
    BoardMove = "BoardMove"
    BoardChange = "BoardChange"


class EventValidator:
    def __init__(self):
        # placeholder values
        self.validations = {
            Event.GameMove:
                {'move': chess.Move},
            # Event.BoardMove:
            #     {'move': chess.Move},
            Event.BoardChange:
                {'board': chess.Board}
        }

    def validate_event(self, event: Event, **kwargs):
        if event not in self.validations:
            raise ValueError('Unknown event')

        # Get the expected validations for the event
        expected = self.validations[event]

        # Check each provided argument against the expected validations
        for arg_name, arg_val in kwargs.items():
            if arg_name not in expected:
                raise ValueError('Unexpected argument: ' + arg_name)

            expected_type = expected[arg_name]

            if not isinstance(arg_val, expected_type):
                raise ValueError('Argument {0} is of type {1}, expected {2}'.format(
                    arg_name, type(arg_val).__name__, expected_type.__name__))

        return True


class WidgetHub:
    """
    This widget is a sort of hub for all other widgets connected to it.
    It allows class instances to subscribe to event types and provide an associated method to call
    To handle that event
    """
    def __init__(self):
        self.uuid = str(uuid4())
        self.event_types = []
        self.subscribers = {event: [] for event in Event}
        self.validator = EventValidator()

    def register_listener(self, listener, function_association: dict[Event, Callable]):
        """
        :param listener: API subscriber
        :param function_association: Dictionary of "Ilmarinen.Event": "Handler function"
        :return:
        """
        for function in function_association:
            if isinstance(function, Event):
                if function in self.subscribers:
                    self.subscribers[function].append((listener, function_association[function]))
            else:
                raise ValueError(f"Function {function} is not an event type registered with this hub."
                                 f"\nRegistered events: {[x for x in Event]}")

    def produce_event(self, event: Event, **kwargs):
        try:
            return self.validator.validate_event(event, **kwargs)
        except Exception as e:
            print(f'Produce event failed with {str(e)}')

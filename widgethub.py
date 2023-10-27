from aenum import Enum
from typing import Callable
from uuid import uuid4
import chess, chess.pgn

# import Ilmarinen.chess_board_widget


class Event(Enum):
    GameMove = "GameMove"
    BoardMove = "BoardMove"
    BoardChange = "BoardChange"
    BoardCreated = "BoardCreated"
    GameLoad = "GameLoad"
    GameLoaded = "GameLoaded"
    GameTraversal = "GameTraversal"
    DatabaseSearch = "DatabaseSearch"
    DatabaseSearchCompleted = "DatabaseSearchCompleted"
    ArrowLeft = "ArrowLeft"
    ArrowRight = "ArrowRight"
    # replace Event logic due to switching to aenum.Enum allowing extend_enum()


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

    def listener_exists(self, event: Event):
        return len(self.subscribers[event])

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
                                 f"\nRegistered events: {[x for x in self.subscribers]}")

    async def produce_event_async(self, event: Event, **kwargs):
        try:
            print(f"Producing {event} with {kwargs}")
            for subscriber, function in self.subscribers[event]:
                # print(f"Invoking {function} for subscriber {subscriber}")
                await function(**kwargs)
        except Exception as e:
            print(f'Produce {event} event failed with {str(e)}')

    def produce_event(self, event: Event, **kwargs):
        # print(f"Current listeners:")
        # print(f"Registered events: {[x for x in self.subscribers]}")
        # for event_type in self.subscribers:
        #     print(f"Event type: {event_type}")
        #     for listener, function in self.subscribers[event_type]:
        #         print(f"Listener {listener} subscribed with function {function}")
        # print(self.subscribers)
        try:
            print(f"Producing {event} with {kwargs}")
            for subscriber, function in self.subscribers[event]:
                # print(f"Invoking {function} for subscriber {subscriber}")
                function(**kwargs)
        except Exception as e:
            print(f'Produce {event} event failed with {str(e)}')

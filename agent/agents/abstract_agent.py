from abc import ABC, abstractmethod
from chirpy.core.state import State
from chirpy.core.user_attributes import UserAttributes

apology_string = 'Sorry, I\'m having a really hard time right now. ' + \
'I have to go, but I hope you enjoyed our conversation so far. ' + \
'Have a good day!'

class ResponseBuilder(ABC):
    """
    ResponseBuilder
    """

    @abstractmethod
    def build(self, response: str, reprompt: str, end_session_flag: bool, current_state, conversation_id) -> dict:
        """

        :param response:
        :param reprompt:
        :param end_session_flag:
        :param current_state:
        :param conversation_id:
        :return:
        """
        pass

class Agent(ABC):
    """
    Base class for Agent.
    """

    def __init__(self):
        """
        Implementations must initialize the following.
        """
        self.response_builder: ResponseBuilder = None
        self.last_state: dict = None
        self.current_state: dict = None
        self.user_attributes: dict = {'user_id': None,
                                      'session_id': None,
                                      'user_timezone': None,
                                      'history': None,
                                      'entity_tracker': None,
                                      'turn_num': None}
    
    @abstractmethod
    def get_response_builder(self) -> ResponseBuilder:
        return self.response_builder

    @abstractmethod
    def persist(self, state:State, user_attributes:UserAttributes) -> None:
        pass

    @abstractmethod
    def should_launch(self) -> bool:
        pass
    
    @abstractmethod
    def should_end_session(self) -> bool:
        pass

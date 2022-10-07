from typing import Optional

from chirpy.core.response_generator.state import *

@dataclass
class State(BaseState):
	cur_food_entity: Optional['WikiEntity'] = None
	cur_supernode: Optional = None

	food__exists_word_food: bool = False
	food__exists_known_food: bool = False
	food__user_fav_food_not_yet_ack: bool = False
	food__needs_comment_on_food_type: bool = False
	food__needs_factoid: bool = False
	food__needs_open_ended: bool = False
	food__needs_exit: bool = False


@dataclass
class ConditionalState(BaseConditionalState):
	cur_food_entity: Optional['WikiEntity'] = NO_UPDATE
	cur_supernode: Optional = NO_UPDATE
	prompt_treelet: Optional[str] = NO_UPDATE

	food__exists_word_food: bool = False
	food__exists_known_food: bool = False
	food__user_fav_food_not_yet_ack: bool = False
	food__needs_comment_on_food_type: bool = False
	food__needs_factoid: bool = False
	food__needs_open_ended: bool = False
	food__needs_exit: bool = False

from typing import Optional

from chirpy.core.response_generator.state import *

@dataclass
class State(BaseState):
	cur_food_entity: Optional['WikiEntity'] = None
	cur_supernode: Optional = None

	acknowledge_fav_food: bool = False
	cur_entity_known_food: bool = False
	entry_entity_is_food: bool = False
	exit_food: bool = False
	food_type_exists: bool = False
	need_factoid: bool = False
	open_ended: bool = False


@dataclass
class ConditionalState(BaseConditionalState):
	cur_food_entity: Optional['WikiEntity'] = NO_UPDATE
	cur_supernode: Optional = NO_UPDATE
	prompt_treelet: Optional[str] = NO_UPDATE

	acknowledge_fav_food: bool = False
	cur_entity_known_food: bool = False
	entry_entity_is_food: bool = False
	exit_food: bool = False
	food_type_exists: bool = False
	need_factoid: bool = False
	open_ended: bool = False

	"""
	entry_entity_is_word_food: bool = False
	entry_entity_is_known_food: bool = False
	
	activates_intro: bool = False
	activates_comment_on_fav_food: bool = False
	activates_factoid: bool = False
	activates_open_ended: bool = False
	activates_exit: bool = False
	"""
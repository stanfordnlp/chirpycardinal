from chirpy.response_generators.one_turn_hack.regex_templates import *
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION


def is_game_or_music_request(rg, utterance):
    """
    Check if the user is requesting that we play a game with them or play a song for them
    :param utterance:
    :return:
    """
    request_play_slots = RequestPlayTemplate().execute(utterance)
    not_request_play_slots = NotRequestPlayTemplate().execute(utterance)
    current_state = rg.state_manager.current_state
    cur_entity = current_state.entity_tracker.cur_entity
    prev_bot_utt = current_state.history[-1] if len(current_state.history) >= 1 else ''
    did_not_ask_user_activity = "what do you like to do" not in prev_bot_utt.lower()
    found_musical_entity = False
    if current_state.entity_tracker.cur_entity_initiated_by_user_this_turn(current_state):
        for ent_group in [ENTITY_GROUPS_FOR_CLASSIFICATION.musician, ENTITY_GROUPS_FOR_CLASSIFICATION.musical_group,
                          ENTITY_GROUPS_FOR_CLASSIFICATION.musical_work]:
            if ent_group.matches(cur_entity):
                found_musical_entity = True

    return did_not_ask_user_activity and ((request_play_slots is not None and found_musical_entity) or
                        (request_play_slots is not None and not_request_play_slots is None))


from chirpy.response_generators.food.yaml_files.handlers.handler_helpers import *

def handler_nlu_processing(rg, state_manager):
    handler_flags = { 'user_asked_about_weather': False,
                      'user_asked_about_time': False,
                      'user_requested_repetition': False,
                      'user_wants_name_correction': False,
                      'user_requested_name': False,
                      'user_got_cutoff': False,
                      'user_asked_for_our_age': False,
                      'user_requested_clarification': False,
                      'user_asked_ablities_question': False,
                      'user_asked_personal_question': False,
                      'user_interrupted': False,
                      'user_said_chatty_phrase': False,
                      'user_asked_for_story': False,
                      'user_shared_personal_problem': False,
                      'user_said_anything': False,
                      }

    initiative_handlers = { 'user_asked_about_weather': (lambda: user_asked_about_weather(state_manager)),
                      'user_asked_about_time': (lambda: user_asked_about_time(state_manager)),
                      'user_requested_repetition': (lambda: user_requested_repetition(state_manager)),
                      'user_wants_name_correction': (lambda: user_wants_name_correction(state_manager)),
                      'user_requested_name': (lambda: user_requested_name(state_manager)),
                      'user_got_cutoff': (lambda: user_got_cutoff(state_manager)),
                      'user_asked_for_our_age': (lambda: user_asked_for_our_age(state_manager)),
                      'user_requested_clarification': (lambda: user_requested_clarification(state_manager)),
                      'user_asked_ablities_question': (lambda: user_asked_ablities_question(state_manager)),
                      'user_asked_personal_question': (lambda: user_asked_personal_question(state_manager)),
                      'user_interrupted': (lambda: user_interrupted(state_manager)),
                      'user_said_chatty_phrase': (lambda: user_said_chatty_phrase(state_manager)),
                      'user_asked_for_story': (lambda: user_asked_for_story(state_manager)),
                      'user_shared_personal_problem': (lambda: user_shared_personal_problem(state_manager)),
                      'user_said_anything': (lambda: user_said_anything(state_manager)),
                      }

    for initiative_flag, initiative_handler in initiative_handlers.items():
        logger.error(f"{initiative_flag}: {initiative_handler()}")
        if initiative_handler():
            handler_flags[initiative_flag] = initiative_handler()
            break

    return handler_flags

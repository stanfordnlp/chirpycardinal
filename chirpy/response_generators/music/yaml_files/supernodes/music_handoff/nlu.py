from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.utils import WikiEntityInterface
from chirpy.response_generators.music.music_helpers import ResponseType
from chirpy.response_generators.music.state import ConditionalState
from chirpy.response_generators.music.regex_templates.name_favorite_song_template import NameFavoriteSongTemplate
import chirpy.response_generators.music.response_templates.general_templates as templates

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'cur_song_ent_exists': False,
        'song_slots_exists': False,
        'thats': False,
        'didnt_know': False,
        'answered_no': False,
        'answered_yes': False,
        'question': False,
        'opinion': False,
        'til_only': False,
        'catch_all': False
    }

    cur_song_ent, cur_singer_ent = rg.get_song_and_singer_entity()
    song_slots = NameFavoriteSongTemplate().execute(utterance)
    # First, if user mentions a song we try to compliment it
    if cur_song_ent:
        flags['cur_song_ent_exists'] = True
    elif song_slots is not None and 'favorite' in song_slots:
        flags['song_slots_exists'] = True
    elif ResponseType.THATS in response_types and state.just_used_til:
        flags['thats'] = True
    elif ResponseType.DIDNT_KNOW in response_types and state.just_used_til:
        flags['didnt_know'] = True
    elif ResponseType.NEGATIVE in response_types or \
         ResponseType.NO in response_types or \
         ResponseType.DONT_KNOW in response_types:
        flags['answered_no'] = True
    elif ResponseType.POSITIVE in response_types or \
         ResponseType.YES in response_types:
        flags['answered_yes'] = True
    elif ResponseType.QUESTION in response_types:
        flags['question'] = True
    elif ResponseType.OPINION in response_types:
        flags['opinion'] = True
    elif state.just_used_til:
        flags['til_only'] = True
    else:
        flags['catch_all'] = True

    return flags


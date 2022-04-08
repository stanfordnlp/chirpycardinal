import logging

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

logger = logging.getLogger('chirpylogger')


class HandoffTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'music_handoff'
        self.can_prompt = False

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        response = self.choose([
            'That\'s great!',
            'Awesome!',
            'Cool!',
        ])

        cur_song_ent, cur_singer_ent = self.get_music_entity()
        song_slots = NameFavoriteSongTemplate().execute(utterance)
        # First, if user mentions a song we try to compliment it
        if cur_song_ent:
            response = self.choose(templates.compliment_user_song_choice())
        elif song_slots is not None and 'favorite' in song_slots:
            response = self.choose(templates.compliment_user_song_choice())
        elif ResponseType.THATS in response_types and state.just_used_til:
            response = self.choose(RESPONSE_TO_THATS)
        elif ResponseType.DIDNT_KNOW in response_types and state.just_used_til:
            response = self.choose(RESPONSE_TO_DIDNT_KNOW)
        elif ResponseType.NEGATIVE in response_types or \
             ResponseType.NO in response_types or \
             ResponseType.DONT_KNOW in response_types:
            response = self.choose([
                'It\'s okay!',
                'Don\'t worry about it!',
            ])
        elif ResponseType.POSITIVE in response_types or \
             ResponseType.YES in response_types:
            response = self.choose([
                'I know, right?',
                "It's great that you do!",
            ])
        elif ResponseType.QUESTION in response_types:
            response = self.choose([
                'Oh I\'m not too sure about that.',
                'Ah I\'m not sure, I\'ll need to check about that.',
                'Oh hmm, I\'m not too sure about that.',
                'Oh dear I don\'t know, I\'ll need to find out.',
            ])
        elif ResponseType.OPINION in response_types:
            response = self.choose([
                'Yeah I totally agree with that!',
                'Me too!',
                'Absolutely!',
            ])
        elif state.just_used_til:
            response = self.choose([
                'I thought that was an interesting tidbit!',
                'I hope you found that interesting!',
            ])

        response, needs_prompt, next_treelet_str = self.rg.try_talking_about_fav_song_else_exit(response)
        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                         next_treelet_str=next_treelet_str)
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
                                   cur_entity=None, conditional_state=conditional_state)

    def get_music_entity(self):
        def is_song(ent):
            return ent and WikiEntityInterface.is_in_entity_group(ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_work)
        def is_singer(ent):
            return ent and WikiEntityInterface.is_in_entity_group(ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musician)
        cur_entity = self.rg.get_current_entity()
        entity_linker_results = self.rg.state_manager.current_state.entity_linker
        song, singer = None, None
        entities = []
        if cur_entity: entities.append(cur_entity)
        if len(entity_linker_results.high_prec): entities.append(entity_linker_results.high_prec[0].top_ent)
        if len(entity_linker_results.threshold_removed): entities.append(entity_linker_results.threshold_removed[0].top_ent)
        if len(entity_linker_results.conflict_removed): entities.append(entity_linker_results.conflict_removed[0].top_ent)
        for e in entities:
            if is_song(e) and song is None: song = e
            elif is_singer(e) and singer is None: singer = e
        return song, singer

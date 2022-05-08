"""
MUSIC RG
"""
import logging
from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.response_generators.music.regex_templates.word_lists import KEYWORD_MUSIC
import chirpy.response_generators.music.treelets as treelets
import chirpy.response_generators.music.music_helpers as helpers
from chirpy.response_generators.music.music_helpers import ResponseType, tags
from chirpy.response_generators.music.state import State, ConditionalState
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.entity_linker.entity_linker_simple import link_span_to_entity
from chirpy.response_generators.music.utils import MusicBrainzInterface

logger = logging.getLogger('chirpylogger')


class MusicResponseGenerator(ResponseGenerator):
    name = "MUSIC"
    def __init__(self, state_manager) -> None:

        # self.introductory_treelet = treelets.IntroductoryTreelet(self)
        # self.handle_opinion_treelet = treelets.HandleOpinionTreelet(self)
        # self.get_song_treelet = treelets.GetSongTreelet(self)
        # self.ask_singer_treelet = treelets.AskSingerTreelet(self)
        # self.get_singer_treelet = treelets.GetSingerTreelet(self)
        # self.ask_song_treelet = treelets.AskSongTreelet(self)
        # self.get_instrument_treelet = treelets.GetInstrumentTreelet(self)
        # self.handoff_treelet = treelets.HandoffTreelet(self)
        self.god_treelet = treelets.GodTreelet(self)

        self.treelets = {
            treelet.name: treelet for treelet in [
                self.god_treelet
            ]
        }

        self.musicbrainz = MusicBrainzInterface()

        super().__init__(state_manager, treelets=self.treelets, can_give_prompts=True, state_constructor=State,
                         conditional_state_constructor=ConditionalState,
                         trigger_words=KEYWORD_MUSIC,
                        )


    def identify_response_types(self, utterance):
        response_types = super().identify_response_types(utterance)

        if helpers.is_music_keyword(self, utterance):
            response_types.add(ResponseType.MUSIC_KEYWORD)
        if helpers.is_positive(self, utterance):
            response_types.add(ResponseType.POSITIVE)
        if helpers.is_negative(self, utterance):
            response_types.add(ResponseType.NEGATIVE)
        if helpers.is_opinion(self, utterance):
            response_types.add(ResponseType.OPINION)
        if helpers.is_freq_answer(self, utterance):
            response_types.add(ResponseType.FREQ)
        if helpers.is_music_response(self, utterance):
            response_types.add(ResponseType.MUSIC_RESPONSE)

        return response_types

    def update_state_if_chosen(self, state, conditional_state):
        state = super().update_state_if_chosen(state, conditional_state)
        if state.cur_song_str and state.cur_song_str not in state.discussed_entities:
            state.discussed_entities.append(state.cur_song_str)
        if state.cur_singer_str and state.cur_singer_str not in state.discussed_entities:
            state.discussed_entities.append(state.cur_singer_str)
        return state

    def update_state_if_not_chosen(self, state, conditional_state):
        state = super().update_state_if_not_chosen(state, conditional_state)
        return state

    def get_song_meta(self, song_name, singer_name=None):
        if ' by ' in song_name:
            song_name, singer_name = song_name.split(' by ')
        metadata = self.musicbrainz.get_song_meta(song_name, singer_name)
        if metadata:
            for t, talkable_t in tags.items():
                if t in metadata['tags']:
                    metadata['tags'] = [talkable_t]
                    return metadata
        return metadata

    def get_singer_genre(self, singer_name):
        genre = self.musicbrainz.get_singer_genre(singer_name)
        return genre

    def get_songs_by_musician(self, musician_name):
        return self.musicbrainz.get_top_songs_by_musician(musician_name)

    def get_song_entity(self, string):
        return link_span_to_entity(string, self.state_manager.current_state,
            expected_type=ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_work)

    def get_musician_entity(self, string):
        return link_span_to_entity(string, self.state_manager.current_state,
            expected_type=ENTITY_GROUPS_FOR_EXPECTED_TYPE.musician)

    @staticmethod
    def try_talking_about_fav_song_else_exit(response=''):
        """
        No favorite for now, since we already have a favorite movie.
        Not sure if we want Chirpy to keep talking about itself.
        """
        return response, True, 'exit'

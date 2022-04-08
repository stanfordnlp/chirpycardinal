import logging

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult
from chirpy.response_generators.music.state import ConditionalState
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.music_helpers import ResponseType

logger = logging.getLogger('chirpylogger')


class AskSongTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'music_ask_song'
        self.can_prompt = False

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get Response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        cur_singer_str = self.rg.state.cur_singer_str
        cur_singer_ent = self.rg.state.cur_singer_ent
        cur_song_str = None
        cur_song_ent = None

        response = self.choose([
            'That\'s great!',
            'Awesome!',
            'Cool!',
        ])
        if ResponseType.THATS in response_types and state.just_used_til:
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
        response += ' '

        top_songs = self.rg.get_songs_by_musician(cur_singer_str)
        if top_songs: cur_song_str = top_songs[0]
        if cur_song_str:
            cur_song_ent = self.rg.get_song_entity(cur_song_str)
            response += self.choose([
                f'As a fan of {cur_singer_str}, I must say that my favorite song is {cur_song_str}. Do you like that too?',
                f'Oh I really love {cur_song_str} by {cur_singer_str}! How about you? Do you like it as well?',
            ])
            next_treelet_str = self.rg.handoff_treelet.name
        else:
            response += f'{cur_singer_str} seems to be really talented! Do you like any other songs by {cur_singer_str}?'
            next_treelet_str = self.rg.handoff_treelet.name

        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str=next_treelet_str,
                                             cur_singer_str=cur_singer_str,
                                             cur_singer_ent=cur_singer_ent,
                                             cur_song_str=cur_song_str,
                                             cur_song_ent=cur_song_ent,
                                             )
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
                                       cur_entity=cur_song_ent or cur_singer_ent, conditional_state=conditional_state)

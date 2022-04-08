import logging
import random
import re

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.regex_templates.name_favorite_song_template import NameFavoriteSongTemplate
from chirpy.response_generators.music.utils import WikiEntityInterface
from chirpy.response_generators.wiki2.wiki_utils import get_til_title
import chirpy.response_generators.music.response_templates.general_templates as templates
from chirpy.response_generators.music.state import ConditionalState
from chirpy.response_generators.music.music_helpers import ResponseType

logger = logging.getLogger('chirpylogger')


class GetSongTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'music_get_song'
        self.can_prompt = True
        self.trigger_entity_groups = [ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_work]

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get Response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        cur_song_ent = None
        cur_song_str = None
        cur_singer_str = None
        response = None
        just_used_til = False

        if state.prev_treelet_str == self.name:
            if ResponseType.NO in response_types or ResponseType.NEGATIVE in response_types:
                response = self.choose([
                    'I\'m sorry I must have heard you wrongly. How about we discuss something else.',
                ])
                response, needs_prompt, next_treelet_str = self.rg.try_talking_about_fav_song_else_exit(response)
            else:
                if ResponseType.THATS in response_types and state.just_used_til:
                    response = self.choose(RESPONSE_TO_THATS)
                elif ResponseType.DIDNT_KNOW in response_types and state.just_used_til:
                    response = self.choose(RESPONSE_TO_DIDNT_KNOW)
                # Comment on genre
                response, metadata = self.comment_genre(state.cur_song_str, state.cur_singer_str, response)
                cur_singer_str = metadata['artist']
                next_treelet_str = self.rg.ask_singer_treelet.name
        else:
            cur_song_ent, cur_singer_ent = self.get_music_entity()
            if cur_song_ent:
                cur_song_str = cur_song_ent.talkable_name
                cur_song_str = re.sub(r'\(.*?\)', '', cur_song_str)
                response = self.choose(templates.compliment_user_song_choice())
                tils = get_til_title(cur_song_ent.name)
                if len(tils):
                    logger.primary_info(f'Found TILs {tils}')
                    til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
                    response += ' ' + templates.til(til)
                    next_treelet_str = self.name
                    just_used_til = True
                else:
                    if cur_singer_ent:
                        response, metadata = self.comment_song(cur_song_str, cur_singer_ent.talkable_name)
                    else:
                        response, metadata = self.comment_song(cur_song_str)
                    if metadata is None:
                        response, needs_prompt, next_treelet_str = self.get_fallback()
                    else:
                        cur_singer_str = metadata['artist']
                        next_treelet_str = self.name
            elif cur_singer_ent:
                # We end up here if we detect a singer but no song e.g. user says "Any song by Katy Perry"
                logger.warning('Redirecting to get_singer_treelet')
                return self.rg.get_singer_treelet.get_response()
            elif ResponseType.DONT_KNOW in response_types:
                response = 'I understand. I like different songs depending on how I\'m feeling and I don\'t really have a favorite either.'
                response, needs_prompt, next_treelet_str = self.rg.try_talking_about_fav_song_else_exit(response)
            elif ResponseType.NO in response_types or ResponseType.NOTHING in response_types:
                response = 'Oh it\'s okay, maybe you will find a song that touches your heart one day!'
                response, needs_prompt, next_treelet_str = self.rg.try_talking_about_fav_song_else_exit(response)
            else:
                # Try to parse song name from utterance
                song_slots = NameFavoriteSongTemplate().execute(utterance)
                if song_slots is not None and 'favorite' in song_slots:
                    cur_song_str = song_slots['favorite']
                    cur_song_ent = self.rg.get_song_entity(cur_song_str)
                    response = self.choose(templates.compliment_user_song_choice())
                    if cur_song_ent:
                        tils = get_til_title(cur_song_ent.name)
                        if len(tils):
                            logger.primary_info(f'Found TILs {tils}')
                            til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
                            response += ' ' + templates.til(til)
                            next_treelet_str = self.name
                            just_used_til = True
                        else:
                            cur_song_str = re.sub(r'\(.*?\)', '', cur_song_ent.talkable_name)
                            response, metadata = self.comment_song(cur_song_str, response=response)
                            if metadata is None:
                                response, needs_prompt, next_treelet_str = self.get_fallback()
                            else:
                                cur_singer_str = metadata['artist']
                                next_treelet_str = self.name
                    else:
                        response, metadata = self.comment_song(cur_song_str, response=response)
                        if metadata is None:
                            response, needs_prompt, next_treelet_str = self.get_fallback()
                        else:
                            cur_singer_str = metadata['artist']
                            next_treelet_str = self.name

        # Fallback if all else fails
        if response is None:
            response, needs_prompt, next_treelet_str = self.get_fallback()

        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str=next_treelet_str,
                                             just_used_til=just_used_til)
        if cur_song_str is not None:
            conditional_state.cur_song_str = cur_song_str
        if cur_song_ent is not None:
            conditional_state.cur_song_ent = cur_song_ent
        if cur_singer_str is not None:
            conditional_state.cur_singer_str = cur_singer_str
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
                                       cur_entity=cur_song_ent, conditional_state=conditional_state)

    def get_prompt(self, **kwargs):
        # Might activate due to trigger entity
        state, utterance, response_types = self.get_state_utterance_response_types()
        cur_song_ent, cur_singer_ent = self.get_music_entity()
        if cur_song_ent:
            
            cur_song_str = cur_song_ent.talkable_name
            cur_song_str = re.sub(r'\(.*?\)', '', cur_song_str)
            
            prompt_text = f'It\'s interesting that you mentioned {cur_song_str}.'
            prompt_text += ' ' + self.choose(templates.compliment_user_song_choice())

            cur_singer_str = None
            if cur_singer_ent:
                cur_singer_str = cur_singer_ent.talkable_name
                cur_singer_str = re.sub(r'\(.*?\)', '', cur_singer_str)

            tils = get_til_title(cur_song_ent.name)
            if len(tils):
                til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
                prompt_text += ' ' + templates.til(til)
                just_used_til = True
            else:
                prompt_text, metadata = self.comment_song(cur_song_str, cur_singer_str, response=prompt_text)
                if metadata is None:
                    # We fail to recognize the song, better not to prompt
                    return None
                cur_singer_str = metadata['artist']
                just_used_til = False
            prompt_type = PromptType.CURRENT_TOPIC
            next_treelet_str = self.name

            conditional_state = ConditionalState(have_prompted=True,
                                                 prev_treelet_str=self.name,
                                                 next_treelet_str=next_treelet_str,
                                                 just_used_til=just_used_til)
            if cur_song_str is not None:
                conditional_state.cur_song_str = cur_song_str
            if cur_song_ent is not None:
                conditional_state.cur_song_ent = cur_song_ent
            if cur_singer_str is not None:
                conditional_state.cur_singer_str = cur_singer_str
        
            return PromptResult(text=prompt_text, prompt_type=prompt_type, state=state, cur_entity=cur_song_ent,
                                conditional_state=conditional_state)

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

    def comment_song(self, song_name, singer_name=None, response=None):
        """
        Make a relevant comment about the song
        and end with a followup question.
        """
        logger.primary_info(f'Commenting on {song_name}, {singer_name}')
        metadata = self.rg.get_song_meta(song_name, singer_name)
        if metadata:
            comment = random.choice([
                f'Oh yeah, {metadata["song"]} is a song by {metadata["artist"]} released in {metadata["year"]} right?',
                f'{metadata["song"]} was released by {metadata["artist"]} in {metadata["year"]} right?',
            ])
            if response is None: response = comment
            else: response = f'{response} {comment}'
        else:
            response = None
        return response, metadata

    def comment_genre(self, song_name, singer_name=None, response=None):
        genre_comments = {
            'rock': '{genre} songs are just the best. You can really connect with the sound and even feel like you are part of the action, nodding your head and just immersing yourself in the beat.',
            'electronic': 'I really love the selection of synthetic instruments used in {genre} music. They give it this unique sound that I don\'t think I\'ve ever heard before with other genres.',
            'pop': 'I love listening to just catchy tunes that are easy on the ears. {genre} music seems to have just enough of a beat to it to keep you interested without being overbearing.',
            'jazz': 'I like {genre} best when I am in the mood for something with smooth subtle energy filled with twists and turns. I love how the genre is so improvised and impromptu.',
            'punk': '{genre} music has a unique energy to it that gets me really excited. Most of the time, it is fast paced and energetic, you really can feel the energy just oozing out of the guitars.',
            'techno': 'I think the best way to describe {genre} music is to listen to it. There is always a beat that simply captivates you and compels you to stand up and start moving along.',
            'classical': 'I love how in {genre} music, you are able to piece together the story without the need for lyrics. It is a universal experience that transcends language.',
            'hip-hop': '{genre} can make you think of the smallest of things, and then take you on an intense emotional journey that just immerses you in everything going on around.',
            'folk': 'I love the unique sound of {genre} music. It is unlike any other genre and is characterized by a very pure sound.',
        }
        logger.primary_info(f'Commenting on genre for {song_name}, {singer_name}')
        metadata = self.rg.get_song_meta(song_name, singer_name)
        comment = None
        if metadata and len(metadata['tags']) and metadata['tags'][0] is not None:
            tag = metadata['tags'][0].lower()
            for genre, comment in genre_comments.items():
                if tag in genre:
                    comment = comment.format(genre=tag) + ' Do you like listening to {tag} music in general?'
                    break
            if comment is None:
                comment = f'Wow you sound like you are a fan of {metadata["tags"][0]} music. Is that right?'
            if response is None: response = comment
            else: response = f'{response} {comment}'
        elif metadata:
            logger.warning(f'No tags for {song_name} found.')
            comment = self.choose([
                'Nice! Which is your favorite part of the song?',
                'Sounds great! Do you have a part of the song that you like the most?',
            ])
            if response is None: response = comment
            else: response = f'{response} {comment}'
        else:
            logger.warning('This should have been caught in the previous turn.')
        return response, metadata

    def get_fallback(self):
        response = 'Oh I don\'t seem to recognize that song.'
        response, needs_prompt, next_treelet_str = self.rg.try_talking_about_fav_song_else_exit(response)
        return response, needs_prompt, next_treelet_str

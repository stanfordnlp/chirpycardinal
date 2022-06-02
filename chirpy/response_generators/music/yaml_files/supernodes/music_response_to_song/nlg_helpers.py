import random

from chirpy.core.response_generator import nlg_helper
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW

@nlg_helper
def thats_response(rg):
    return rg.state_manager.current_state.choose_least_repetitive(RESPONSE_TO_THATS)

@nlg_helper
def didnt_know_response(rg):
    return rg.state_manager.current_state.choose_least_repetitive(RESPONSE_TO_DIDNT_KNOW)

@nlg_helper
def comment_genre(rg, song_name, singer_name=None, response=None):
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
    comment = None
    metadata = rg.get_song_meta(song_name, singer_name)
    if metadata and len(metadata['tags']) and metadata['tags'][0] is not None:
        tag = metadata['tags'][0].lower()
        for genre, comment in genre_comments.items():
            if tag in genre:
                comment = comment.format(genre=tag) + f' Do you like listening to {tag} music in general?'
                break
        if comment is None:
            comment = f'Wow you sound like you are a fan of {metadata["tags"][0]} music. Is that right?'
        if response is None: response = comment
        else: response = f'{response} {comment}'
    elif metadata:
        comment = random.choice([
            'Nice! Which is your favorite part of the song?',
            'Sounds great! Do you have a part of the song that you like the most?',
        ])
        if response is None: response = comment
        else: response = f'{response} {comment}'
    # else:
    #     logger.warning('This should have been caught in the previous turn.')
    return response
from collections import Counter
import logging
from functools import lru_cache
import os
import random
import re
import psycopg2

from chirpy.core.entity_linker.entity_groups import EntityGroup, ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name, link_span_to_entity

from chirpy.response_generators.wiki.wiki_utils import overview_entity


LOWER_CASE_TITLE_WORDS = ['a', 'an', 'the', 'and', 'or', 'of', 'to', 'with', 'without']


# MusicBrainz
HOST ='localhost'
DATABASE = 'musicbrainz'
PORT = 5432
USER = os.environ.get('POSTGRES_USER')
PASSWORD = os.environ.get('POSTGRES_PASSWORD')


logger = logging.getLogger('chirpylogger')


REPEAT_THRESHOLD = 2


class MusicEntity:

    def __init__(self, kid=None, pref_label=None, wiki_entity=None):
        self.kid = kid
        self.pref_label = pref_label
        self.wiki_entity = wiki_entity

    def __repr__(self):
        return "MusicEntity: {}, {}, {}".format(self.kid, self.pref_label, self.wiki_entity)


class KnowledgeInterface:

    def __init__(self):
        # self.knowledge_interface = AlexaKnowledgeGraphInterface()
        self.knowledge_interface = MusicBrainzInterface()

    def get_song_entity_by_musician(self, musician_name):
        song_entities = self.knowledge_interface.get_song_entities_by_musician(musician_name)
        if song_entities:
            maximum_comparisons = 5
            random.shuffle(song_entities)
            song_entity = WikiEntityInterface.get_most_popular_music_entity(song_entities, maximum_comparisons=maximum_comparisons)
            return song_entity
        return None

    def get_musician_entity_by_song(self, song_name):
        musician_entities = self.knowledge_interface.get_musician_entities_by_song(song_name)
        musician_entity = WikiEntityInterface.get_most_popular_music_entity(musician_entities)
        if musician_entity:
            if WikiEntityInterface.is_in_entity_group(musician_entity.wiki_entity,
                                                      WikiEntityInterface.EntityGroup.MUSICIAN):
                return musician_entity
        return None


class MusicBrainzInterface:

    PLACEHOLDER = 'PLACEHOLDER'

    class Query:
        SONG_BY_MUSICIAN = """\
            select release.name as release_name 
            from musicbrainz.artist_credit 
            inner join musicbrainz.release on artist_credit.id = release.artist_credit 
            where artist_credit.name = 'PLACEHOLDER';
            """
        MUSICIAN_BY_SONG = """\
            select artist_credit.name as artist_name
            from musicbrainz.artist_credit 
            inner join musicbrainz.release on artist_credit.id = release.artist_credit 
            where release.name = 'PLACEHOLDER';
        """

    def __init__(self):
        self.conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            database=DATABASE,
            user=USER,
            password=PASSWORD
        )
        self.cur = self.conn.cursor()

    def get_musician_entities_by_song(self, song_name):
        song_name = WikiEntityInterface.make_title(song_name)
        query = MusicBrainzInterface.Query.MUSICIAN_BY_SONG
        query = query.replace(MusicBrainzInterface.PLACEHOLDER, song_name)
        musician_entities = self.get_results(query)
        return musician_entities

    def get_song_entities_by_musician(self, musician_name):
        musician_name = WikiEntityInterface.make_title(musician_name)
        query = MusicBrainzInterface.Query.SONG_BY_MUSICIAN
        query = query.replace(MusicBrainzInterface.PLACEHOLDER, musician_name)
        song_entities = self.get_results(query)
        return song_entities

    def get_results(self, query):
        self.cur.execute(query)
        results = self.cur.fetchall()
        results = [r[0] for r in results]
        results = Counter(results).most_common(5) # TODO
        results = [r[0] for r in results]
        parantheses_removal_pattern = '\([^)]*\)'
        results = [re.sub(parantheses_removal_pattern, '', r).strip() for r in results]
        results = [MusicEntity(pref_label=name) for name in results]
        return results


class WikiEntityInterface:

    ENTITY_PLACEHOLDER = 'ENTITY'

    class PageName:
        BAND = 'Musical ensemble'
        MUSICIAN = 'Musician'
        SONG = 'Song'
        MUSIC = 'Music'
        INSTRUMENT = 'Musical instrument'

    class EntityType:
        BAND = 'musical group'
        MUSICIAN = 'musician'
        SONG = 'musical work'
        INSTRUMENT = 'musical instrument'

    class EntityGroup: # TODO revise, import from entity_group.py (Cannot for some reason)
        BAND = EntityGroup({'musical group'}, entity_blacklist={'Musical ensemble'}, entity_whitelist={'BTS'})
        MUSICIAN = EntityGroup({'musician', 'musical group'},
                                        entity_blacklist={'Tom Hanks', 'Keanu Reeves', 'Leonardo da Vinci', 'Charlie Chaplin',
                                                          'Kim Kardashian', 'Stephen King', 'Florence Pugh', 'Carrie Fisher',
                                                          'Adam Sandler', 'Tom Hiddleston', 'Diane Keaton', 'Zooey Deschanel',
                                                          'John Lithgow', 'Robert Downey Jr.', 'Clint Eastwood', 'Julia Louis-Dreyfus',
                                                          'Rashida Jones', 'Maya Rudolph', 'Jennifer Lawrence', 'Viggo Mortensen',
                                                          'Ryan Gosling', 'Bruce Willis', 'Gwyneth Paltrow', 'Jamie Dornan',
                                                          'Emma Stone', 'Paul Bettany', 'Michelle Rodriguez', 'Sarah Silverman',
                                                          'Jackie Chan', 'Johnny Depp', 'Scarlett Johansson', 'Naomi Scott',
                                                          'Christopher Lee', 'Martin Luther', 'Matthew Broderick', 'Kirsten Dunst',
                                                          'Musician', 'Musical ensemble'}, entity_whitelist={'BTS'})
        SONG = EntityGroup({'song'}, {'genre'}, entity_blacklist={'Song'})
        INSTRUMENT = EntityGroup({'musical instrument'}, entity_blacklist={'Musical instrument'})

    @classmethod
    def get_most_popular_music_entity(cls, music_entities, blacklist_wiki_entities=[], maximum_comparisons=5):
        top_entity = None
        for ind, music_entity in enumerate(music_entities):
            if ind < maximum_comparisons:
                wiki_entity = cls.link_span(music_entity.pref_label)
                if wiki_entity and wiki_entity not in blacklist_wiki_entities:
                    music_entity.wiki_entity = wiki_entity
                    if not top_entity:
                        top_entity = music_entity
                    elif top_entity.wiki_entity.pageview > wiki_entity.pageview:
                        top_entity = music_entity
            else:
                break
        return top_entity

    @classmethod
    def get_by_name(cls, name):
        try:
            wiki_entity = get_entity_by_wiki_name(name)
        except Exception:
            wiki_entity = None
        return wiki_entity

    @classmethod
    def get_by_title(cls, name):
        wiki_entity = cls.get_by_name(cls.make_title(name))
        return wiki_entity

    @classmethod
    def link_span(cls, span):
        try:
            entity = link_span_to_entity(span, use_asr_robustness=False)
        except Exception:
            entity = None
        return entity

    @classmethod
    def is_in_entity_group(cls, entity, entity_group):
        if entity_group.matches(entity):
            return True
        return False

    @classmethod
    def is_title_in_entities(cls, title, entities):
        answer = any([True for entity in entities if title == entity.name])
        return answer

    @staticmethod
    def make_title(entity_name):
        # Make the words like 'a' and 'an' lowercase.
        entity_title_list = [w if w in LOWER_CASE_TITLE_WORDS else w.capitalize() for w in entity_name.split()]
        # Make the first letter of the first and last words uppercase.
        entity_title_list[0] = entity_title_list[0].capitalize()
        entity_title_list[-1] = entity_title_list[-1].capitalize()
        # Join the title words and return.
        entity_title = ' '.join(entity_title_list)
        return entity_title

    @staticmethod
    def overview(entity_name):
        overview = overview_entity(entity_name, lambda text: text.split('.'))
        return overview

    @classmethod
    def extract_musician_name_from_song_overview(cls, song_name):
        # Try to get it from the wikipedia title
        #search_pattern = '\((.*?) song\)'

        # Try to get the musician name from the overview
        musician_words = ['singer', 'musician', 'songwriter', 'band', 'by', 'artist', 'group', 'rapper']
        musician_words_pattern = '|'.join(musician_words)
        ending_expressions = ['\.', ',', 'from', 'that', 'which', 'who', 'whose', 'whom']
        ending_expressions_pattern = '|'.join(ending_expressions)
        sample_musician_word = musician_words[0]
        search_pattern = '({})(.*?)({})'.format(sample_musician_word, ending_expressions_pattern)
        cleaning_pattern = '({}|{})'.format(sample_musician_word, ending_expressions_pattern)

        overview = cls.overview(song_name)
        if overview:
            overview = re.sub(musician_words_pattern, sample_musician_word, overview)
            regex_match = re.search(search_pattern, overview)
            if regex_match:
                match_string = regex_match.group().split(sample_musician_word)[-1]
                musician_name = re.sub(cleaning_pattern, '', match_string).strip()
                return musician_name
        return None

class Pronoun:

    class Placeholder:
        SUBJECT = 'SUBJECT_PLACEHOLDER'
        OBJECT = 'OBJECT_PLACEHOLDER'
        POSSESSIVE = 'POSSESSIVE_PLACEHOLDER'

    class Sex:
        FEMALE = 'female'
        MALE = 'male'

    @classmethod
    def get_subject_pronoun(cls, sex):
        if sex is cls.Sex.FEMALE: return 'she'
        if sex is cls.Sex.MALE: return 'he'

    @classmethod
    def get_object_pronoun(cls, sex):
        if sex is cls.Sex.FEMALE: return 'her'
        if sex is cls.Sex.MALE: return 'him'

    @classmethod
    def get_possessive_pronoun(cls, sex):
        if sex is cls.Sex.FEMALE: return 'her'
        if sex is cls.Sex.MALE: return 'his'

    @classmethod
    def replace_pronouns(cls, text, sex):
        text = text.replace(cls.Placeholder.SUBJECT, cls.get_subject_pronoun(sex))
        text = text.replace(cls.Placeholder.OBJECT, cls.get_object_pronoun(sex))
        text = text.replace(cls.Placeholder.POSSESSIVE, cls.get_possessive_pronoun(sex))
        return text

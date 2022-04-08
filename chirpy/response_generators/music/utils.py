import logging
import re
import psycopg2
import os
from collections import Counter

from chirpy.core.entity_linker.entity_groups import EntityGroup
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name, link_span_to_entity

from chirpy.response_generators.wiki2.wiki_utils import overview_entity


LOWER_CASE_TITLE_WORDS = ['a', 'an', 'the', 'and', 'or', 'of', 'to', 'with', 'without']


logger = logging.getLogger('chirpylogger')


REPEAT_THRESHOLD = 1


# MusicBrainz
HOST = os.environ.get('POSTGRES_HOST', 'localhost')
DATABASE = 'musicbrainz'
PORT = 5432
USER = os.environ.get('POSTGRES_USER')
PASSWORD = os.environ.get('POSTGRES_PASSWORD')


class MusicEntity:

    def __init__(self, kg_label=None, pref_label=None, wiki_entity=None):
        self.kg_label = kg_label
        self.pref_label = pref_label
        self.wiki_entity = wiki_entity

    def __repr__(self):
        return "MusicEntity: {}, {}, {}".format(self.kg_label, self.pref_label, self.wiki_entity)


class MusicBrainzInterface:

    class Query:
        SONG_BY_MUSICIAN = """
            SELECT release.name AS release_name
            FROM musicbrainz.artist_credit
            INNER JOIN musicbrainz.release ON artist_credit.id = release.artist_credit
            WHERE LOWER(artist_credit.name) = LOWER('{placeholder}');
            """
        TOP_SONGS_BY_MUSICIAN = """
            SELECT
            track.name,
            COUNT(*)
            FROM musicbrainz.track
            LEFT JOIN musicbrainz.artist_credit ON
            track.artist_credit = artist_credit.id
            WHERE LOWER(artist_credit.name) = LOWER('{placeholder}')
            GROUP BY track.name
            ORDER BY count DESC
            LIMIT 5
        """
        MUSICIAN_BY_SONG = """
            SELECT artist_credit.name AS artist_name
            FROM musicbrainz.artist_credit
            INNER JOIN musicbrainz.release ON artist_credit.id = release.artist_credit
            WHERE LOWER(release.name) = LOWER('{placeholder}');
        """
        SONG_META = """
            SELECT
            release.name AS song,
            first_release_date_year,
            artist_credit_name.name AS musician,
            ARRAY_AGG(DISTINCT tag.name) AS tag,
            artist_credit.ref_count AS artist_ref_count
            FROM musicbrainz.release
            LEFT JOIN musicbrainz.release_group_meta
            ON release.release_group = release_group_meta.id
            LEFT JOIN musicbrainz.artist_credit_name
            ON release.artist_credit = artist_credit_name.artist_credit
            LEFT JOIN musicbrainz.artist_credit
            ON artist_credit_name.artist = artist_credit.id
            LEFT JOIN musicbrainz.release_group_tag
            ON release.release_group = release_group_tag.release_group
            LEFT JOIN musicbrainz.tag
            ON release_group_tag.tag = tag.id
            WHERE LOWER(release.name) = LOWER('{placeholder}')
            AND artist_credit.ref_count IS NOT NULL
            AND artist_credit_name.name != 'Various Artists'
            GROUP BY release.name, first_release_date_year, artist_credit_name.name, artist_credit.ref_count
            ORDER BY artist_credit.ref_count DESC,
            first_release_date_year ASC
            LIMIT 1
        """
        SONG_META_NAMED_SINGER = """
            SELECT
            release.name AS song,
            first_release_date_year,
            artist_credit_name.name AS musician,
            ARRAY_AGG(DISTINCT tag.name) AS tag,
            artist_credit.ref_count AS artist_ref_count
            FROM musicbrainz.release
            LEFT JOIN musicbrainz.release_group_meta
            ON release.release_group = release_group_meta.id
            LEFT JOIN musicbrainz.artist_credit_name
            ON release.artist_credit = artist_credit_name.artist_credit
            LEFT JOIN musicbrainz.artist_credit
            ON artist_credit_name.artist = artist_credit.id
            LEFT JOIN musicbrainz.release_group_tag
            ON release.release_group = release_group_tag.release_group
            LEFT JOIN musicbrainz.tag
            ON release_group_tag.tag = tag.id
            WHERE LOWER(release.name) = LOWER('{song}')
            AND LOWER(artist_credit_name.name) = LOWER('{singer}')
            AND artist_credit.ref_count IS NOT NULL
            GROUP BY release.name, first_release_date_year, artist_credit_name.name, artist_credit.ref_count
            ORDER BY artist_credit.ref_count DESC,
            first_release_date_year ASC
            LIMIT 1
        """
        SINGER_META = """
            SELECT
            tag.name
            FROM musicbrainz.artist
            LEFT JOIN musicbrainz.artist_tag
            ON artist_tag.artist = artist.id
            LEFT JOIN musicbrainz.tag
            ON tag.id = artist_tag.tag
            WHERE LOWER(artist.name) = LOWER('{placeholder}')
            AND tag.name IS NOT NULL
            ORDER BY ref_count DESC
            LIMIT 1
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
        # TODO: Maybe select the most common musician
        song_name = WikiEntityInterface.make_title(song_name)
        song_name = song_name.replace("'", "''")
        query = MusicBrainzInterface.Query.MUSICIAN_BY_SONG.format(placeholder=song_name)
        musician_entities = self.get_results(query)
        return musician_entities

    def get_song_entities_by_musician(self, musician_name):
        musician_name = WikiEntityInterface.make_title(musician_name)
        musician_name = musician_name.replace("'", "''")
        query = MusicBrainzInterface.Query.SONG_BY_MUSICIAN.format(placeholder=musician_name)
        song_entities = self.get_results(query)
        return song_entities

    def get_top_songs_by_musician(self, musician_name):
        musician_name = WikiEntityInterface.make_title(musician_name)
        logger.primary_info(f"Getting top songs by {musician_name}")
        musician_name = musician_name.replace("'", "''")
        query = MusicBrainzInterface.Query.TOP_SONGS_BY_MUSICIAN.format(placeholder=musician_name)
        self.cur.execute(query)
        results = self.cur.fetchall()
        song_names = [r[0] for r in results]
        logger.primary_info(f"Retrieved songs {song_names} by {musician_name}")
        return song_names

    def get_song_meta(self, song_name, singer_name=None):
        logger.primary_info(f"Getting metadata for {song_name}")
        song_name = WikiEntityInterface.make_title(song_name)
        song_name = song_name.replace("'", "''")
        results = []
        if singer_name:
            singer_name = WikiEntityInterface.make_title(singer_name)
            singer_name = singer_name.replace("'", "''")
            query = MusicBrainzInterface.Query.SONG_META_NAMED_SINGER.format(song=song_name, singer=singer_name)
            self.cur.execute(query)
            results = self.cur.fetchall()

        if len(results) == 0:
            query = MusicBrainzInterface.Query.SONG_META.format(placeholder=song_name)
            self.cur.execute(query)
            results = self.cur.fetchall()

        logger.primary_info(f"Retrieved metadata {results} for {song_name}")
        if len(results):
            result = results[0]
            return {
                'song': result[0],
                'year': result[1],
                'artist': result[2],
                'tags': result[3],
            }

    def get_singer_genre(self, singer_name):
        logger.primary_info(f"Getting genre of {singer_name}")
        singer_name = WikiEntityInterface.make_title(singer_name)
        singer_name = singer_name.replace("'", "''")
        query = MusicBrainzInterface.Query.SINGER_META.format(placeholder=singer_name)
        self.cur.execute(query)
        results = self.cur.fetchall()
        logger.primary_info(f"Retrieved genre {results} for {singer_name}")
        if len(results):
            return results[0][0]

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

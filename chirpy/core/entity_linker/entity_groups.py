"""
This file defines EntityGroups, which capture certain groups of WikiEntities, depending on their WikiData types.
"""

import logging
from dataclasses import dataclass, asdict, field
from functools import lru_cache
from typing import List, Optional, Tuple, Set

logger = logging.getLogger('chirpylogger')

@dataclass
class EntityGroup:
    """
    Class to represent a desired group of WikiEntities, e.g. books.
    """
    positives: Set[str]  # list of wikidata categories
    negatives: Set[str] = field(default_factory=set)  # list of wikidata categories
    entity_whitelist: Set[str] = field(default_factory=set)  # list of entity names that should be considered part of the class
    entity_blacklist: Set[str] = field(default_factory=set)  # list of entity names that should not be considered part of the class

    @lru_cache(maxsize=2048)
    def matches(self, entity) -> bool:
        """
        Returns True iff the entity is in this EntityGroup.
        Aside from the whitelist and blacklist, a WikiEntity is a member of an EntityGroup iff:
            (a) the WikiEntity contains ANY of the positive categories, and
            (b) it contains NONE of the negative categories.

        Input:
            entity: a WikiEntity
        """
        if not isinstance(self.entity_blacklist, set):
            self.entity_blacklist = set(self.entity_blacklist)
        if not isinstance(self.entity_whitelist, set):
            self.entity_whitelist = set(self.entity_whitelist)
        if not isinstance(self.positives, set):
            self.positives= set(self.positives)
        if not isinstance(self.positives, set):
            self.negatives = set(self.negatives)
        if entity.name in self.entity_whitelist:
            return True
        if entity.name in self.entity_blacklist:
            return False
        wikidata_categories = set(entity.wikidata_categories)
        return len(wikidata_categories &  set(self.positives))>0 and len(wikidata_categories & set(self.negatives)) == 0

    def __hash__(self):
        return hash(tuple((k, tuple(v)) for k, v in asdict(self).items()))


@dataclass
class EntityGroupsForExpectedType:
    """
    Class to hold some EntityGroups used as expected_type (i.e. to detect entities the user mentions
    in response to typed questions). These should be high recall, because people often give answers in related
    categories that aren't exactly what we asked for (e.g. we ask what their favorite game is, they might just name
    a gaming console).

    Ordering doesn't matter.
    """
    game_related: EntityGroup = EntityGroup(
        {'video game', 'video game series', 'video game console', 'video game developer', 'toy', 'game'})
    animal_related: EntityGroup = EntityGroup(
        {'pet', 'animal', 'taxon', 'polyphyletic common name', 'mythical creature', 'mythical animal'})
    person_related: EntityGroup = EntityGroup({'human', 'human who may be fictional', 'kin', 'kinship'}, entity_blacklist={
        'Woman', 'Girl', 'Man', 'Boy', 'Wife', 'Husband'})
    sport_related: EntityGroup = EntityGroup({'sport', 'exertion', 'sports team', 'dance', 'athlete'})
    history_related: EntityGroup = EntityGroup({'historical period', 'human', 'human who may be fictional', 'time'})
    science_related: EntityGroup = EntityGroup({'academic discipline', 'branch of science', 'space object'},
                                               {'physical object', 'physical activity', 'diet'}, entity_whitelist={
            'Science fiction'}, entity_blacklist={'Calendar', 'Streaming media'})
    scientist_related: EntityGroup = EntityGroup({'academic discipline', 'branch of science', 'space object', 'human'},
                                                 {'physical object', 'physical activity', 'diet'}, entity_whitelist={
            'Science fiction'}, entity_blacklist={'Calendar', 'Streaming media'})
    device_related: EntityGroup = EntityGroup(
        {'toy', 'video game', 'video game series', 'mobile app', 'website', 'streaming media', 'streaming service',
         'vehicle model', 'vehicle', 'mode of transport', 'computing platform', 'electric device', 'digital media'}, entity_whitelist={
            'Xbox', 'PlayStation'})
    book_related: EntityGroup = EntityGroup({'literary work', 'literary form', 'genre', 'author', 'written work'},
                                            {'audiovisual', 'film score', 'game', 'website', 'genre', 'human',
                                             'events in a specific year or time period',
                                             "certain aspects of a person's life"}, entity_blacklist={'Woman', 'Girl',
                                                                                                      'Man', 'Boy'})
    food_related: EntityGroup = EntityGroup({'food', 'fruit', 'taxon', 'restaurant chain', 'diet'})
    anime_related: EntityGroup = EntityGroup({'anime', 'manga', 'manga series', 'television program', 'film', 'book'}, set())
    artcraft_related: EntityGroup = EntityGroup(
        {"art", "arts", "art form", 'textile process', 'textile arts', 'ceramic', 'paint', 'craft', 'art material',
         'art genre'}, entity_whitelist={'Drawing', 'Nail art', 'Handmade jewelry'})
    transport_related: EntityGroup = EntityGroup(
        {'vehicle model', 'vehicle', 'mode of transport', 'automobile manufacturer', 'automobile marque',
         'automobile model'}, set())
    academic_related: EntityGroup = EntityGroup(
        {'academic discipline', 'branch of science', 'mathematical object', 'mental process', 'knowledge',
         'learning or memory', 'memory', 'punctuation mark', 'arts', 'performing arts', 'art genre',
         'historical period', 'war'}, entity_whitelist={'Spelling'}, entity_blacklist={'Fun'})
    tv_related: EntityGroup = EntityGroup(
        {"television network", 'channel', 'television program', 'television film', 'film', 'film series', 'film actor',
         'television actor', 'stage actor', 'actor'})
    dance_related: EntityGroup = EntityGroup({'dance', 'dancer'},set())
    location_related: EntityGroup = EntityGroup(
        {'location', 'country', 'constituent state', 'city', 'quarter', 'administrative territorial entity',
         'tourist attraction', 'point of interest', 'group of physical objects', 'business', 'restaurant chain',
         'brick and mortar company'})
    clothing_related: EntityGroup = EntityGroup({'clothing', 'fashion house', 'fashion label', 'clothing store chain'}, set())
    film: EntityGroup = EntityGroup({'film', 'film series', 'television film'}, {'genre'})  # used by Movies RG, when asking the user to name a film. Kathleen you can refine this if you wish


@dataclass
class EntityGroupsForClassification:
    """
    Class to hold an ordered list of EntityGroups. A WikiEntity can match multiple EntityGroups, but this list is
    intended to classify a single entity into the most specific group that it matches (or none, if it matches none).

    The EntityGroups are ordered so that the first-matching EntityGroup for a WikiEntity is more likely to be correct.
    This means that they're ordered from most to least specific, and groups that tend to have more false positives
    are put lower.

    The groups and their ordering aim to be high precision (i.e., the group that an entity is sorted into should be
    correct most of the time).

    The wikidata types are not intuitive and there are lots of strange unexpected memberships.
    Before changing something here, you should  open "notebooks/Entity Popularity.ipynb" to see the potential effects
    of your changes (it doesn't take too long to run).

    Note: it's important to put
        name: EntityGroup = ...
    If you don't include the ": EntityGroup" part, then the EntityGroup will not be included when we iterate over
    these attributes using asdict(ENTITY_GROUPS_CLASSIFICATION).
    """
    group_of_people: EntityGroup = EntityGroup(
        {'identity', 'ethnic group', 'ethnoreligious group', 'minority group', 'race'}, entity_blacklist={'Gender',
                                                                                                          'Race (human categorization)'})

    sport: EntityGroup = EntityGroup({'sport', 'exertion'}, {'board game', 'card game'}, entity_blacklist={'Esports', 'Yoga'})
    # Added yoga because it doesn't feel like a sport with typical tournaments etc and so WIKI breaks down
    toy: EntityGroup = EntityGroup({'toy'}, entity_whitelist={'Xbox', 'PlayStation'})
    game: EntityGroup = EntityGroup({'video game', 'video game series', 'board game'}, {'sport', 'video game genre'}, entity_blacklist={
        'Video game', 'Online game'})
    anime: EntityGroup = EntityGroup({'anime'}, set())
    tv_channel: EntityGroup = EntityGroup({"television network", 'channel'}, set())
    tv_show: EntityGroup = EntityGroup({'television program'}, {'television film', 'television network', 'channel'})
    film: EntityGroup = EntityGroup({'film', 'film series', 'television film'}, {'genre'})
    app_or_website: EntityGroup = EntityGroup({'mobile app', 'website', 'streaming media', 'streaming service'}, entity_blacklist={
        'Online shopping'})
    media_franchise: EntityGroup = EntityGroup({'media franchise'})

    sports_team: EntityGroup = EntityGroup({'sports team'}, set())

    academic_subject: EntityGroup = EntityGroup({'academic discipline', 'branch of science'},
                                                {'physical object', 'physical activity', 'diet'}, entity_blacklist={
            'Calendar', 'Streaming media'})

    mode_of_transport: EntityGroup = EntityGroup({'vehicle model', 'automobile model', 'vehicle', 'mode of transport'}, set())
    dance: EntityGroup = EntityGroup({'dance'}, set())
    clothing: EntityGroup = EntityGroup({'clothing'}, set())
    historical_period: EntityGroup = EntityGroup({'historical period'}, set(), entity_blacklist={'Switzerland'})
    food: EntityGroup = EntityGroup({'food', 'fruit'}, set(), entity_whitelist={'Avocado'}, entity_blacklist={'Food'})
    pet: EntityGroup = EntityGroup({'pet'})  # more specific than animal
    animal: EntityGroup = EntityGroup({'animal', 'polyphyletic common name'}, {'plant'}, entity_blacklist={'Human',
                                                                                                           'Pet'})
    musical_instrument: EntityGroup = EntityGroup({'musical instrument'}, set(), entity_blacklist={'Musical instrument'})
    musical_work: EntityGroup = EntityGroup({'musical work'}, {'genre'}, entity_blacklist={'Song', 'Album'})

    restaurant_chain: EntityGroup = EntityGroup({'restaurant chain'})
    company: EntityGroup = EntityGroup({'enterprise'}, {'type of organisation'}, entity_blacklist={'Bank'})  # more general than restaurant chain. captures various companies

    # Unfortunately, a lot of animals don't have the 'animal' label but many of them do have the 'taxon' label
    # However, there are several plants/foods (e.g. Blueberry, Ginger, Avocado and more) that have identical labels
    # to these animals which have 'taxon' but not 'animal'.
    taxon: EntityGroup = EntityGroup({'taxon'}, {'hazard', 'disease causative agent'}, entity_blacklist={'Animal',
                                                                                                         'Coronavirus'})  # Make sure that both 'food' and 'animal' come before taxon.

    tourist_attraction: EntityGroup = EntityGroup({'tourist attraction', 'point of interest'})

    # I tried using the 'location' label but that has some strange members like 'Netflix'
    location: EntityGroup = EntityGroup(
        {'country', 'constituent state', 'city', 'quarter', 'administrative territorial entity'}, entity_blacklist={'Song dynasty'})

    painting: EntityGroup = EntityGroup({'painting'}, set())

    general_technology: EntityGroup = EntityGroup({'computing platform', 'electric device', 'digital media'}, entity_blacklist={
        'Toilet paper'})  # more general than app_or_website, toy, game

    musical_group: EntityGroup = EntityGroup({'musical group'}, entity_whitelist={'BTS'}, entity_blacklist={'Musical ensemble'})

    mythical_creature: EntityGroup = EntityGroup({'mythical creature', 'mythical animal'}, {'religious character'})
    fictional_character: EntityGroup = EntityGroup({'fictional character'},
                                                   {'group of fictional characters', 'hypothetical entity'}, entity_blacklist={
            'Skynet (Terminator)'})

    comedian: EntityGroup = EntityGroup({'comedian'})
    musician: EntityGroup = EntityGroup({'musician'},
                                        entity_blacklist={'Tom Hanks', 'Keanu Reeves', 'Leonardo da Vinci',
                                                          'Charlie Chaplin',
                                                          'Kim Kardashian', 'Stephen King', 'Florence Pugh',
                                                          'Carrie Fisher',
                                                          'Adam Sandler', 'Tom Hiddleston', 'Diane Keaton',
                                                          'Zooey Deschanel',
                                                          'John Lithgow', 'Robert Downey Jr.', 'Clint Eastwood',
                                                          'Julia Louis-Dreyfus',
                                                          'Rashida Jones', 'Maya Rudolph', 'Jennifer Lawrence',
                                                          'Viggo Mortensen',
                                                          'Ryan Gosling', 'Bruce Willis', 'Gwyneth Paltrow',
                                                          'Jamie Dornan',
                                                          'Emma Stone', 'Paul Bettany', 'Michelle Rodriguez',
                                                          'Sarah Silverman',
                                                          'Jackie Chan', 'Johnny Depp', 'Scarlett Johansson',
                                                          'Naomi Scott',
                                                          'Christopher Lee', 'Martin Luther', 'Matthew Broderick',
                                                          'Kirsten Dunst', 'Musician', 'Patrick Swayze',
                                                          })  # problem: many actors are also musicians
    actor: EntityGroup = EntityGroup({'film actor', 'television actor', 'stage actor'}, {'politician'}, entity_blacklist={
        'LeBron James', 'Ronald Reagan', 'Donald Trump'})  # problem: there are quite a few musicians in here like Taylor Swift
    politician: EntityGroup = EntityGroup({'politician'}, {'public office', 'title', 'fictional character'}, entity_blacklist={
        'Kim Kardashian', 'Innocent (actor)', 'Andy Warhol'})
    athlete: EntityGroup = EntityGroup({'athlete'}, set(), entity_blacklist={'Stanley Kubrick'})  # There are some people (e.g. politicians, musicians) who are also athletes, so athletes should come lower
    dancer: EntityGroup = EntityGroup({'dancer'}, set())  # Many musicians/actors are also dancers, so dancer should come lower
    fashion_designer: EntityGroup = EntityGroup({'fashion designer'}, set())  # Many people who are predominantly e.g. musicians are also fashion designers, so fashion_designer should come lower
    artist: EntityGroup = EntityGroup({'artist'}, set(), entity_blacklist={'Actor', 'Musician'})
    family_member: EntityGroup = EntityGroup({'kin', 'kinship'}, entity_blacklist={'Elvis Presley', 'Julian Dennison'})
    human: EntityGroup = EntityGroup({'human', 'human who may be fictional'}, {'kin'}, entity_blacklist={'Woman',
                                                                                                         'Girl', 'Man',
                                                                                                         'Boy', 'Wife',
                                                                                                         'Husband'})  # the 'person' label has a lot of weird false positives so be careful with that

    # there seems to be something wrong with the 'literary work' category - there are websites, people and a bunch of
    # weird things with the label. so putting it at the bottom here. the 'written work' label is even worse.
    book: EntityGroup = EntityGroup({'literary work'},
                                    {'literary form', 'audiovisual', 'game', 'website', 'genre', 'human',
                                     'events in a specific year or time period', "certain aspects of a person's life"}, entity_blacklist={
            'Woman', 'Girl', 'Man', 'Boy'})

    @property
    def ordered_items(self) -> List[Tuple[str, EntityGroup]]:
        """Returns a list of (name: str, entity_group: EntityGroup) pairs, in the order they're defined above"""
        ordered_keys = asdict(self).keys()
        return [(k, getattr(self, k)) for k in ordered_keys]



def validate_entity_groups(entity_groups):
    """Check that all the entity groups are in asdict(entity_groups)"""
    for k in dir(entity_groups):
        v = getattr(entity_groups, k)
        if isinstance(v, EntityGroup):
            assert k in asdict(entity_groups), f'key "{k}" corresponds to an EntityGroup in {entity_groups} but the key is ' \
                                               f'not in asdict({entity_groups}). Perhaps you forgot to give the type ' \
                                               f'information ": EntityGroup" when declaring the entity group?'


ENTITY_GROUPS_FOR_CLASSIFICATION = EntityGroupsForClassification()
validate_entity_groups(ENTITY_GROUPS_FOR_CLASSIFICATION)
ENTITY_GROUPS_FOR_EXPECTED_TYPE = EntityGroupsForExpectedType()
validate_entity_groups(ENTITY_GROUPS_FOR_EXPECTED_TYPE)
import logging
import jsonpickle
from collections import OrderedDict
from typing import List, Dict, Optional
from tabulate import tabulate
import re
import requests

from chirpy.core.entity_linker.util import wiki_name_to_url
from chirpy.core.latency import measure
from chirpy.response_generators.categories.categories import CATEGORYNAME2CLASS
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.util import filter_and_log, make_text_like_user_text
from chirpy.core.entity_linker.lists import MANUAL_SPAN2ENTINFO, ENTITY_WHITELIST, WIKIDATA_CATEGORY_WHITELIST, STOPWORDS, DONT_LINK_WORDS
from chirpy.core.entity_linker.thresholds import SCORE_THRESHOLD_ELIMINATE_DONT_LINK_WORDS, SCORE_THRESHOLD_ELIMINATE, SCORE_THRESHOLD_ELIMINATE_HIGHFREQUNIGRAM_SPAN, UNIGRAM_FREQ_THRESHOLD, SCORE_THRESHOLD_EXPECTEDTYPE
from chirpy.core.entity_linker.entity_groups import EntityGroup

import inflect
engine = inflect.engine()

logger = logging.getLogger('chirpylogger')

# Get a set of entity names (strings) which should be considered categories
CATEGORY_ENTITY_NAMES = {'Film', 'Sport', 'Video game', 'Animal', 'History', 'Science', 'Book', 'Food', 'Art', 'Car', 'Education', 'Pet', 'Television', 'Cooking', 'Dance', 'Celebrity', 'Travel', 'Fashion'}
# CATEGORY_ENTITY_NAMES = {question.cur_entity_wiki_name for category_class in CATEGORYNAME2CLASS.values() for question in category_class.questions} | {'Film'}  # not all these are categories any more, some are specific entities

# Max number of entities in each LinkedSpan
MAX_ENTITIES_PER_SPAN = 10

# Entities in this group are usually referred to by their whole name, so if we only have a partial match (and other
# conditions like low score), the entity might be removed
whole_name_entgroup = EntityGroup({'human', 'human who may be fictional', 'written work'})


# When users say a plural noun (e.g. "dogs") we also try matching the singular form (e.g. "dog"). This works well for general objects like animals.
# This doesn't work well for entities such as film/book/game titles (e.g. the tv show "Heroes" is never referred to as "Hero").
# For entities in this group, we do not consider artificially singularized versions of user spans to be equivalent to the original plural version.
dont_singularize_entgroup = EntityGroup(
    {'video game', 'video game series', 'board game', 'film', 'film series', 'television film', 'television program',
     'human', 'musical work', 'written work'})

class WikiEntity(object):
    """Class to represent an entity (Wikipedia article)"""

    def __init__(self, name: str, doc_id: int, pageview: int, confidence: float, wikidata_categories: List[str], anchortext_counts: Dict[str, int], redirects: List[str], plural: str):
        """
        @param name: the canonical name of the entity / the title of the article
        @param doc_id: unique identifier for the article
        @param pageview: raw number of pageviews for the article
        @param wikidata_categories: wikidata_categories from the ES articles index
        @param anchortext_counts: dict mapping from span, to number of references from that span to this article.
        @param redirects: Names of articles which redirect to this article
        """
        self.name = name
        self.doc_id = doc_id
        self.pageview = pageview
        self.confidence = confidence
        self.wikidata_categories = sorted(wikidata_categories)
        self.redirects = redirects
        self.anchortext_counts = OrderedDict(sorted(anchortext_counts.items(), key=lambda x: x[1], reverse=True))  # span->count, ordered descending by count
        self.sum_anchortext_counts = sum(self.anchortext_counts.values())
        self.url = wiki_name_to_url(self.name)
        self.is_category = self.name in CATEGORY_ENTITY_NAMES  # bool
        self.talkable_name = self._get_talkable_name(name, plural)

    def _get_talkable_name(self, name, plural):
        """Checks to ensure that the plural name is sensible"""
        if len(plural) - len(name) <= 6:
            return plural
        else: # invalid plural
            if "(" in name: # Halo (franchise)
                return ' '.join([tok for tok in name.split() if "(" not in tok])
            else:
                return name

    def __hash__(self):
        return hash(self.doc_id)

    def score(self, span) -> float:
        """
        Returns the score of span, for this entity.
            score(span, entity) = pageview(entity) * P_anchortext(span|entity)
        where P_anchortext is self.anchortext_counts normalized.
        If span is not among the anchortexts for this entity, returns 0.
        """
        return self.confidence

    def is_type(self, type_str: str):
        """
        Returns true iff type_str is among self.wikidata_categories
        """
        type_str = type_str.strip()
        assert type_str
        return type_str.strip() in self.wikidata_categories

    @property
    def common_name(self) -> str:
        """
        Returns the title, with any bracketed parts removed. While self.name is the full wikipedia article title
        (e.g. "Frozen (2013 film)"), common_name is just "Frozen".

        Note: this function used to return the most common anchortext for this entity, but that had some difficulties
        e.g. with the anchortext being an adjective e.g. "atheist" for "Atheism", plus other problems.
        """
        # return next(iter(self.anchortext_counts))
        return re.sub("\(.*?\)", "", self.name).strip()

    def __repr__(self):
        if hasattr(self, "confidence"):
            return f"<WikiEntity: {self.name}> (confidence={self.confidence:.3f}, sum_anchortext_counts={self.sum_anchortext_counts})>"
        else:
            logger.warning("DEPRECATION: WikiEntity object has no attribute 'confidence', so you are likely using an outdated version of the global State (older than April 2021). Make sure this is intentional.")
            return f"<WikiEntity: {self.name}>"

    def __eq__(self, other) -> bool:
        """
        Determine whether this WikiEntity is equal to other object.
        Returns True iff other is a WikiEntity with the same doc_id.
        """
        if not isinstance(other, WikiEntity):
            return False
        return self.doc_id == other.doc_id

    @property
    def is_plural(self) -> bool:
        #logger.warning(f"Talkable name is {self.talkable_name}")
        #logger.warning(f"Is singular is {engine.singular_noun(self.talkable_name)}")
        return bool(engine.singular_noun(self.talkable_name))


def is_offensive_entity(entity: WikiEntity):
    """Returns True if the entity is offensive (i.e. has offensive phrases in its title or wikidata categories)"""
    if entity.name in ENTITY_WHITELIST:
        logger.primary_info(f'Entity {entity} is on ENTITY_WHITELIST, so not filtering it for offensiveness in the entity linker')
        return False
    if contains_offensive(entity.name):
        return True
    for cat in entity.wikidata_categories:
        if cat in WIKIDATA_CATEGORY_WHITELIST:
            logger.primary_info(f"Entity {entity} has a wikidata category '{cat}' which contains an offensive phrase, but the category is whitelisted")
        else:
            if contains_offensive(cat):
                return True
    return False

class LinkedSpan(object):
    """Class to represent a span and the candidate entities to which it could be linked"""
    MAX_SHOW = 5  # how many to show when doing detail_repr or html

    def __init__(self, span: str, candidate_entities: List[WikiEntity], min_unigram_freq: Optional[int] = None,
                 span_used_for_search: Optional[str] = None, ner_type=None, is_proper_noun=False,
                 ):
        """
        @param span: the span appearing in the original text
        @param candidate_entities: list of WikiEntities
        @param min_unigram_freq: int
        @param span_used_for_search: optionally, an alternative span that was used to obtain the span->entity refcounts,
            but is not what originally appeared in the text. If None, will assume "span" was used for search.
        @param ner_type: the NER type of this span
        @param is_proper_noun: whether this span is a proper noun
        """
        self.span = span
        self.min_unigram_freq = min_unigram_freq
        self.span_used_for_search = span_used_for_search
        self.ner_type = ner_type
        self.is_proper_noun = is_proper_noun
        assert len(candidate_entities) > 0, 'candidate_entities should not be empty'

        self.entname2ent = {ent.name: ent for ent in candidate_entities}
        self.top_ent_score = max(entity.confidence for entity in self.entname2ent.values())

        # If this span has a manually linked entity, identify it
        self.manual_top_ent_name = None
        self.manual_top_ent_force_highprec = False
        if span in MANUAL_SPAN2ENTINFO:
            manual_top_ent_name = MANUAL_SPAN2ENTINFO[span].ent_name
            manual_top_ent_force_highprec = MANUAL_SPAN2ENTINFO[span].force_high_prec
            if manual_top_ent_name in [ent.name for ent in candidate_entities]:
                self.manual_top_ent_name = manual_top_ent_name
                self.manual_top_ent_force_highprec = manual_top_ent_force_highprec
                if MANUAL_SPAN2ENTINFO[span].delete_alternative_entities:
                    logger.primary_info(f'Manual link from span "{span}" to "{manual_top_ent_name}" has '
                                        f'delete_alternative_entities=True, so deleting all other candidate entities in the LinkedSpan')
                    candidate_entities = [ent for ent in candidate_entities if ent.name == manual_top_ent_name]
            else:
                logger.error('Span "{}" is manually linked to entity "{}" but there is no candidate entity with that '
                             'name'.format(span, manual_top_ent_name))

        self.filter_offensive()  # do this last as it's most expensive

    def update_candidate_entities(self, new_candidate_entities: List[WikiEntity]):
        """Update the LinkedSpan to only contain new_candidate_entities"""
        assert all(ent in self.entname2ent.values() for ent in new_candidate_entities)  # check that all new_candidate_entities are already in this LinkedSpan
        self.entname2ent = {ent.name: ent for ent in new_candidate_entities}

    def filter_offensive(self):
        """Update the LinkedSpan to only contain inoffensive entities"""
        new_candidate_entities = filter_and_log(lambda e: not is_offensive_entity(e), self.entname2ent.values(), f'candidate entities for LinkedSpan "{self.span}"',
                                                'it contains an offensive phrase in the title or wikidata categories')
        self.update_candidate_entities(new_candidate_entities)

    @property
    def is_empty(self):
        return len(self.entname2ent) == 0

    @property
    def top_ent(self):
        return max(self.entname2ent.values(), key=lambda ent: (
            ent.name == self.manual_top_ent_name,
            ent.confidence))

    @property
    def manual_top_ent(self) -> Optional[WikiEntity]:
        """Returns the manually chosen top entity if there is one, otherwise returns None"""
        if self.manual_top_ent_name:
            return self.entname2ent[self.manual_top_ent_name]
        return None

    @property
    def protection_level(self):
        return 0

    @property
    def ents_by_priority(self):
        return sorted(self.entname2ent.values(), key=lambda ent: (
            ent.name == self.manual_top_ent_name,
            ent.confidence
        ), reverse=True)

    @property
    def html(self) -> str:
        """Return a HTML representation of the object (for display in dashboard)"""
        output = ''
        output += '<h6>span: "{}"</h6>'.format(self.span)
        output += "min_unigram_freq={}".format(self.min_unigram_freq)
        if self.span_used_for_search != self.span:
            output += f" (used '{self.span_used_for_search}' to search)"
        if self.is_proper_noun:
            output += f", is_proper_noun=True"
        if self.ner_type:
            output += f", ner_type={self.ner_type}"
        if self.manual_top_ent:
            output += f", manual_top_ent={self.manual_top_ent.name}"
        # if self.type_based_top_ent:
        #     output += f", type_based_top_ent={self.type_based_top_ent}"
        # if hasattr(self, 'override_top_ent_score'):
        #     output += f", override_top_ent_score={self.override_top_ent_score}"
        #
        # # Table
        headers = ['pageview', 'score', 'doc_id', 'name', 'wikidata_categories']
        output += '<table id="dashboard-table">'
        output += '<tr>{}</tr>'.format(''.join(['<th>{}</th>'.format(header) for header in headers]))
        for ent in self.ents_by_priority[:self.MAX_SHOW]:
            row = [
                ent.pageview,
                '{:.2f}'.format(ent.confidence),
                self.entname2ent[ent.name].doc_id,
                '<a href="{}">{}</a>'.format(ent.url, ent.name),
                ', '.join(sorted(self.entname2ent[ent.name].wikidata_categories))
            ]
            output += '<tr>{}</tr>'.format(''.join(['<td>{}</td>'.format(item) for item in row]))
        output += '</table>'
        if len(self.entname2ent) > self.MAX_SHOW:
            output += f'\n+ {len(self.entname2ent)-self.MAX_SHOW} more candidate entities'

        # print('LINKED SPAN HTML:')
        # print(output)

        return output

    def __repr__(self):
        output = f"<LinkedSpan: span='{self.span}'"
        if self.span_used_for_search != self.span:
            output += f" (used '{self.span_used_for_search}' to search)"
        output += ', min_unigram_freq={}'.format(self.min_unigram_freq)
        if self.is_empty:
            output += f" (is empty)"
        else:
            if self.is_proper_noun:
                output += f", is_proper_noun=True"
            if self.ner_type:
                output += f", ner_type={self.ner_type}"
            output += f", top_entity='{self.top_ent.name}'"
            if self.manual_top_ent:
                output += " (manually chosen)"
            # if self.type_based_top_ent:
            #     output += f", (high prec type-matching top entity)"
            output += f", score={self.top_ent_score}"
            # if hasattr(self, 'override_top_ent_score'):
            #     output += f" (override)"
        output += ">"
        return output

    @property
    def detail_repr(self):
        return self.__repr__()

class EntityLinkerResult(object):
    """A class to represent the output of the entity linker module"""

    def __init__(self, high_prec: List[LinkedSpan] = [], threshold_removed: List[LinkedSpan] = [],
                 conflict_removed: List[LinkedSpan] = []):
        """
        @param high_prec: LinkedSpans that should be considered high-precision links
        @param threshold_removed: LinkedSpans that are not in the high precision set because they did not meet
            the score or unigram-freq thresholds.
        @param conflict_removed: LinkedSpans that are not in the high precision set because they conflicted (e.g.
            are alternative forms of, or nested with) with a LinkedSpan in the high precision set.
        """
        self.high_prec = high_prec
        self.threshold_removed = threshold_removed
        self.conflict_removed = conflict_removed

    @property
    def low_prec(self) -> List[LinkedSpan]:
        """This exists for legacy reasons"""
        return self.threshold_removed + self.conflict_removed  # put threshold-removed as higher priority than conflict-removed

    @property
    def all_linkedspans(self) -> List[LinkedSpan]:
        """
        A list of all the LinkedSpans in priority order (first the high precision ones, then the threshold-removed ones,
        then the conflict-removed ones).
        """
        return self.high_prec + self.threshold_removed + self.conflict_removed

    @property
    def top_highprec_ent(self) -> Optional[WikiEntity]:
        """
        Returns the highest-priority entity of the highest-priority high-precision LinkedSpan.
        Returns None if there is no such entity.
        """
        if self.high_prec:
            return self.high_prec[0].top_ent
        return None

    @measure
    def top_ent(self, condition_fn=(lambda x, y, z: True)) -> Optional[WikiEntity]:
        """
        Returns the highest-priority entity which satisfies condition_fn.
        If no condition_fn is supplied, gives top entity of highest-priority LinkedSpan.

        Inputs:
          condition_fn: A function which takes in a (EntityLinkerResult, LinkedSpan, WikiEntity)
            and returns a bool.
        """
        logger.info(f'Searching for highest-priority entity in EntityLinkerResults satisfying condition {condition_fn}')
        # First look through all top entities of high_prec and threshold_removed linked spans in order
        for linked_span in self.high_prec + self.threshold_removed:
            if condition_fn(self, linked_span, linked_span.top_ent):
                logger.info(f'Found entity {linked_span.top_ent} satisfying {condition_fn}')
                return linked_span.top_ent

        # Then look through all other entities in score order
        ents_and_scores = [(ls, ent, ent.confidence) for ls in self.all_linkedspans for ent in
                           ls.entname2ent.values() if not (ls in self.high_prec + self.threshold_removed and ent == ls.top_ent)]
        ents_and_scores = sorted(ents_and_scores, key=lambda x: x[2], reverse=True)  # sort by score
        for (linked_span, ent, _) in ents_and_scores:
            if condition_fn(self, linked_span, ent):
                logger.info(f'Found entity {ent} satisfying {condition_fn}')
                return ent

        logger.info(f'Didn\'t find any entities satisfying "{condition_fn}"')
        return None

    @measure
    def best_ent_of_type(self, entity_type: EntityGroup) -> Optional[WikiEntity]:
        """
        Returns highest-priority WikiEntity of desired type (i.e. the entity matches the EntityGroup).
        If none is found, returns None.
        """
        if not isinstance(entity_type, EntityGroup):
            raise TypeError(f'entity_type should be type {EntityGroup}, not {type(entity_type)}')
        logger.info(f'Searching for entities of type {entity_type} in EntityLinkerResults')
        def condition_fn(entity_linker_result, linked_span, entity) -> bool:
            return entity_type.matches(entity)
        return self.top_ent(condition_fn)

    def __repr__(self):
        return f'<EntityLinkerResults: high_prec={self.high_prec}, threshold_removed={self.threshold_removed}, conflict_removed={self.conflict_removed}>'

    @property
    def html(self) -> str:
        """Return a HTML representation of the object (for display in dashboard)"""
        output = ''

        def get_tables(linkedspan_list: List[LinkedSpan], name: str):
            tables_html = ''
            tables_html += f'<h4>{name}</h4>'
            tables_html += '<div>'
            if not linkedspan_list:
                tables_html += f'<p>No {name}</p>'
            for ls in linkedspan_list:
                tables_html += '<div>{}</div>'.format(ls.html)
            tables_html += '</div>'
            return tables_html

        output += get_tables(self.high_prec, 'High-precision LinkedSpans')
        output += get_tables(self.threshold_removed, 'Threshold-removed low-precision LinkedSpans')
        output += get_tables(self.conflict_removed, 'Conflict-removed low-precision LinkedSpans')
        return output

    @measure
    def reduce_size(self, max_size: int):
        """Return a version of this EntityLinkerResult which, when jsonpickled, is under max_size"""

        def num_wikientities() -> int:
            """Returns the number of wikientities stored in this EntityLinkerResult"""
            return sum([len(ls.entname2ent) for ls in self.all_linkedspans])

        logger.info(f'Attempting to reduce the size of EntityLinkerResult to less than {max_size}. Current EntityLinkerResult has '
                    f'{len(self.all_linkedspans)} LinkedSpans containing {num_wikientities()} WikiEntities in total:\n{self}')

        # First limit the number of WikiEntities per LinkedSpan
        MAX_ENTS_PER_LINKEDSPAN = 5
        for ls in self.all_linkedspans:
            ls.filter_top_n(MAX_ENTS_PER_LINKEDSPAN)
        encoded_result = jsonpickle.encode(self)
        logger.info(f'After limiting each LinkedSpan to {MAX_ENTS_PER_LINKEDSPAN} WikiEntities, there are now '
                    f'{len(self.all_linkedspans)} LinkedSpans containing {num_wikientities()} WikiEntities in total. '
                    f'New size={len(encoded_result)}')
        if len(encoded_result) < max_size:
            return

        # Otherwise, keep removing LinkedSpans until the size is small enough
        while len(encoded_result) >= max_size:
            if self.conflict_removed:
                logger.info(f'Removing the LinkedSpan {self.conflict_removed[-1]}')
                self.conflict_removed = self.conflict_removed[:-1]
            elif self.threshold_removed:
                logger.info(f'Removing the LinkedSpan {self.threshold_removed[-1]}')
                self.threshold_removed = self.threshold_removed[:-1]
            elif self.high_prec:
                logger.info(f'Removing the LinkedSpan {self.high_prec[-1]}')
                self.high_prec = self.high_prec[:-1]
            else:
                logger.error("Removed all LinkedSpans from the EntityLinkerResult but it's still too big")
                break
            encoded_result = jsonpickle.encode(self)
            logger.info(f'After removing another LinkedSpan, there are now {len(self.all_linkedspans)} LinkedSpans '
                        f'containing {num_wikientities()} WikiEntities in total. New size={len(encoded_result)}')

from .integration_base import BaseIntegrationTest
from unittest import TestCase
from chirpy.core.flags import USE_ASR_ROBUSTNESS_OVERALL_FLAG
from agents.local_agent import apology_string
from chirpy.core.entity_linker.entity_linker import entity_link
from chirpy.core.entity_linker.entity_linker_simple import link_span_to_entity, get_entity_by_wiki_name
from chirpy.core.entity_linker.entity_groups import EntityGroup
from chirpy.core.entity_linker.util import add_all_alternative_spans

class TestEntityLinkerIntegration(BaseIntegrationTest):
    launch_sequence = ['let\'s chat', 'my name is abi']

    def test_easy_link(self):
        """Check that the top high-precision entity is Ariana Grande in this easy case"""
        _, current_state, response_text = self.process_utterance('do you like ariana grande')
        self.assertEqual(current_state['entity_linker'].top_highprec_ent.doc_id, 25276055)
        self.assertNotIn(apology_string, response_text)  # check it didn't result in fatal error

    def test_long_utterance(self):
        """Check that the entity linker runs correctly on a long utterance"""
        _, current_state, response_text = self.process_utterance("what do you think about ariana grande have you heard her new album it's probably my favorite one so far")
        self.assertEqual(current_state['entity_linker'].top_highprec_ent.doc_id, 25276055)
        self.assertNotIn(apology_string, response_text)  # check it didn't result in fatal error

    def test_asr_short_utterance(self):
        """Check that the entity linker runs correctly on a long utterance"""
        if USE_ASR_ROBUSTNESS_OVERALL_FLAG:
            _, current_state, response_text = self.process_utterance(
                "their eyes of skywalker")
            self.assertEqual(current_state['entity_linker'].top_highprec_ent.doc_id, 43910733)
            self.assertNotIn(apology_string, response_text)  # check it didn't result in fatal error

    def test_asr_long_utterance(self):
        """Check that the entity linker runs correctly on a long utterance"""
        if USE_ASR_ROBUSTNESS_OVERALL_FLAG:
            _, current_state, response_text = self.process_utterance(
                "i recently watched their eyes of skywalker and it was really really good much better than i had anticipated")
            self.assertEqual(current_state['entity_linker'].top_highprec_ent.doc_id, 43910733)
            self.assertNotIn(apology_string, response_text)  # check it didn't result in fatal error


class TestEntityLinkerUnit(TestCase):

    def test_include_common_phrases(self):
        """Check that the entity linker identifies the movie 'Home Alone' (in threshold_removed set) when include_common_phrases=True"""
        entity_linker_results = entity_link('i watched home alone', None, include_common_phrases=True)
        self.assertEqual(entity_linker_results.threshold_removed[0].top_ent.doc_id, 216072)

    def test_get_entity_by_wiki_name(self):
        """Test the get_entity_by_wiki_name function"""
        entity = get_entity_by_wiki_name('Chicago (2002 film)')
        self.assertEqual(entity.doc_id, 201534)  # Chicago the movie

        entity = get_entity_by_wiki_name('Chicago (2002 filmm)')
        self.assertIsNone(entity)  # there is no wikipedia article by this name

    def test_link_span_to_entity(self):
        """Test the link_span_to_entity function"""
        entity = link_span_to_entity('chicago', expected_type=None)
        self.assertEqual(entity.doc_id, 6886)  # Chicago the city

        entity = link_span_to_entity('chicago', expected_type=EntityGroup({'film'}))
        self.assertEqual(entity.doc_id, 201534)  # Chicago the movie

        entity = link_span_to_entity('chicago', expected_type=EntityGroup({'painting'}), must_match_expected_type=True)
        self.assertIsNone(entity)  # there is no Chicago painting

        entity = link_span_to_entity('chicago', expected_type=EntityGroup({'painting'}), must_match_expected_type=False)
        self.assertEqual(entity.doc_id, 6886)  # Chicago the city

class TestEntityLinkerUnit(TestCase):

    def check_alternative_versions(self, span, output_spans):
        """Check that add_all_alternative_spans adds the alternative spans we expect"""
        spans_to_lookup, _ = add_all_alternative_spans({span}, {span}, [])
        self.assertSetEqual(spans_to_lookup, output_spans)

    def test_alt_span_spiderman_two(self):
        output_spans = {'spiderman 2', 'spiderman two', 'spiderman ii', 'spider-man 2', 'spider-man two', 'spider-man ii', 'spider man 2', 'spider man two', 'spider man ii'}
        self.check_alternative_versions('spider-man 2', output_spans)

    def test_alt_span_cats(self):
        output_spans = {'i love cats', 'i love cat'}
        self.check_alternative_versions('i love cats', output_spans)

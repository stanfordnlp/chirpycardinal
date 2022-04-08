from .integration_base import BaseIntegrationTest
from chirpy.core.test_args import TestArgs
from chirpy.core.response_generator_datatypes import ResponsePriority, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE

class TestCategoriesResponseGenerator(BaseIntegrationTest):
    launch_sequence = ['let\'s chat', 'my name is abi']
    categories_test_args = TestArgs(selected_prompt_rg="CATEGORIES", experiment_values={'category_style': 'question'})

    def process_utterance(self, utterance, with_extra_args=False, extra_args=None):
        if with_extra_args:
            return super().process_utterance(utterance, test_args=extra_args)
        return super().process_utterance(utterance, TestArgs(experiment_values={'category_style': 'question'}))

    def get_categories_state(self, current_state: dict):
        return current_state['response_generator_states']['CATEGORIES']

    def get_categories_response(self, current_state: dict):
        return current_state['response_results']['CATEGORIES']

    def get_categories_prompt(self, current_state: dict):
        return current_state['prompt_results']['CATEGORIES']

    def categories_response_chosen(self, current_state) -> bool:
        return current_state.get('selected_response_rg') == 'CATEGORIES'

    def categories_prompt_chosen(self, current_state) -> bool:
        return current_state.get('selected_prompt_rg') == 'CATEGORIES'

    def test_food_affirmative_response(self):

        # When the user says food, check that categories gives a food response or prompt, and its response is chosen.
        _, current_state, response_text = self.process_utterance('can we talk about food')
        self.assertTrue(self.categories_response_chosen(current_state) or self.categories_prompt_chosen(current_state))
        categories_result = self.get_categories_response(current_state) if self.categories_response_chosen(current_state) else self.get_categories_prompt(current_state)
        self.assertEqual(categories_result.cur_entity.name, 'Food')
        self.assertEqual(categories_result.expected_type, ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related)
        state = self.get_categories_state(current_state)
        self.assertEqual(state.cur_treelet, 'HandleAnswerTreelet')
        self.assertEqual(state.cur_category_name, 'FoodCategory')
        self.assertEqual(sum(state.questions_used['FoodCategory'].values()), 1)

        # When the user names a food, check that it becomes the cur_entity and categories gives no response
        _, current_state, response_text = self.process_utterance('salsa')
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, "Salsa (sauce)")
        categories_result = self.get_categories_response(current_state)
        self.assertEqual(categories_result.priority, ResponsePriority.NO)

    def test_food_negnav_response(self):
        _, current_state, response_text = self.process_utterance('can we talk about food')

        # When the user says a negnav intent, check the cur_entity changes to None and categories gives no response
        _, current_state, response_text = self.process_utterance('change the subject')
        self.assertIsNone(current_state['entity_tracker'].history[-1]['user'])
        categories_result = self.get_categories_response(current_state)
        self.assertEqual(categories_result.priority, ResponsePriority.NO)

    def test_food_usernewtopic_response(self):
        _, current_state, response_text = self.process_utterance('can we talk about food')

        # When the user starts talking about some other entity, check it becomes the cur_entity and categories gives no response
        _, current_state, response_text = self.process_utterance("let's talk about elvis presley")
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, "Elvis Presley")
        categories_result = self.get_categories_response(current_state)
        self.assertEqual(categories_result.priority, ResponsePriority.NO)

    def test_food_sametopic_response(self):
        _, current_state, response_text = self.process_utterance('can we talk about food')

        # # When the user responds with "i don't know", check that categories gives a WEAK_CONTINUE response
        # # with another food question
        # _, current_state, response_text = self.process_utterance("i don't know")
        # categories_result = self.get_categories_response(current_state)
        # self.assertEqual(categories_result.cur_entity.name, 'Food')
        # self.assertEqual(categories_result.expected_type, 'food')
        # self.assertEqual(categories_result.priority, ResponsePriority.WEAK_CONTINUE)
        # self.assertEqual(categories_result.conditional_state.cur_treelet, 'HandleAnswerTreelet')
        # self.assertEqual(categories_result.conditional_state.cur_category_name, 'FoodCategory')

        # When the user responds with "i don't know", check that categories gives a STRONG_CONTINUE response
        # and setting cur_entity and expected_type to be None
        _, current_state, response_text = self.process_utterance("i don't know")
        categories_result = self.get_categories_response(current_state)
        self.assertEqual(categories_result.cur_entity, None)
        self.assertEqual(categories_result.expected_type, None)
        self.assertEqual(categories_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(categories_result.conditional_state.cur_treelet, 'HandleAnswerTreelet')
        self.assertEqual(categories_result.conditional_state.cur_category_name, 'FoodCategory')


    def test_multiple_consecutive_categories_response(self):
        # Ask to talk about food
        _, current_state, response_text = self.process_utterance('can we talk about food')

        # Switch to cars and check that categories gives a question (response or prompt) about cars
        _, current_state, response_text = self.process_utterance('i want to talk about cars')
        self.assertTrue(self.categories_response_chosen(current_state) or self.categories_prompt_chosen(current_state))
        categories_result = self.get_categories_response(current_state) if self.categories_response_chosen(current_state) else self.get_categories_prompt(current_state)
        self.assertEqual(categories_result.expected_type, ENTITY_GROUPS_FOR_EXPECTED_TYPE.transport_related)
        self.assertEqual(categories_result.cur_entity.name, 'Car')
        state = self.get_categories_state(current_state)
        self.assertEqual(state.cur_treelet, 'HandleAnswerTreelet')
        self.assertEqual(state.cur_category_name, 'CarsCategory')
        self.assertEqual(sum(state.questions_used['CarsCategory'].values()), 1)

        # Switch to movies
        _, current_state, response_text = self.process_utterance("let's talk about movies")

        # Switch to art and check categories gives a question about art
        _, current_state, response_text = self.process_utterance("let's talk about art")
        state = self.get_categories_state(current_state)
        self.assertEqual(state.cur_treelet, 'HandleAnswerTreelet')
        self.assertEqual(state.cur_category_name, 'ArtCategory')
        self.assertEqual(sum(state.questions_used['ArtCategory'].values()), 1)

    def test_categories_prompt(self):

        # Check that when the user triggers red_question, categories then gives a generic prompt which is chosen
        _, current_state, response_text = self.process_utterance('who are you', with_extra_args=True, extra_args=self.categories_test_args)
        categories_prompt_result = self.get_categories_prompt(current_state)
        category_name = categories_prompt_result.conditional_state.cur_category_name
        state = self.get_categories_state(current_state)
        self.assertIsNotNone(categories_prompt_result.cur_entity)
        self.assertIsNotNone(categories_prompt_result.expected_type)
        self.assertEqual(categories_prompt_result.type, PromptType.GENERIC)
        self.assertEqual(categories_prompt_result.conditional_state.cur_treelet, 'HandleAnswerTreelet')
        self.assertEqual(sum(state.questions_used[category_name].values()), 1)
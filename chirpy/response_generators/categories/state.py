import logging
from chirpy.core.response_generator.state import *
from collections import defaultdict, Counter
from chirpy.core.entity_linker.entity_groups import EntityGroup
from chirpy.response_generators.categories.categories import CATEGORYNAME2CLASS, CategoryQuestion
from random import choice

logger = logging.getLogger('chirpylogger')


CATEGORY_WITH_STATEMENTS = ['VideoGamesCategory', 'AnimalsCategory', 'BooksCategory',
                            'FoodCategory', 'SchoolCategory', 'PetsCategory', 'TVCategory', 'CookingCategory',
                            'CelebritiesCategory', 'TravelCategory']

@dataclass
class CategoryQuestionStatement(object):
    """A class to represent a question and statement the categories RG can use to respond"""
    statement: Optional[str] # the statement we tell the user
    question: Optional[str] # the question we ask the user
    cur_entity_wiki_name: str  # the name of the wikipedia article that should be the cur_entity once we've asked the question
    expected_type: Optional[EntityGroup]  # EntityGroup representing the expected_type of the user's answer on the next turn. or None if no expected type


@dataclass
class ConditionalState(BaseConditionalState):
    cur_category_name: str = None  # the name of the category for the question we asked
    statement: Optional[str] = None# the statement we used
    question: Optional[str] = None # the question we asked
    just_asked: bool = False # whether we have just used a follow up prompt from another RG and should give priority to other RGs


@dataclass
class State(BaseState):
    questions_used: Dict[str, Dict[str, int]] = None #TODO field(default_factory=defaultdict(Counter))  # maps from category name (str) to a dict mapping questions (str) to how many times we've asked them (int)
    statements_used: Dict[str, Dict[str, int]] = None  # maps from category name (str) to a dict mapping statements (str) to how many times we've used them (int)
    statement: Optional[str] = None
    cur_category_name: Optional[str] = None # if we asked a category question on the last turn, the name of the category
    just_asked: bool = False

    def __init__(self):
        self.questions_used = defaultdict(Counter)
        self.statements_used = defaultdict(Counter)

    def discussed(self, category_name: str) -> bool:
        """Returns True iff we have already asked at last one question or used one statement on this category"""
        return (sum(self.questions_used[category_name].values()) + sum(self.statements_used[category_name].values())) > 0

    @property
    def undiscussed_generic_categories(self) -> List[str]:
        """Returns a list of all names of categories that are generic and for which we haven't asked any questions"""
        return [category_name for category_name, category_class in CATEGORYNAME2CLASS.items()
                if category_class.generic_prompt and not self.discussed(category_name)]

    def get_random_generic_undiscussed_category_question(self) -> (Optional[str], Optional[CategoryQuestion]):
        """Randomly chooses an undiscussed generic category, and returns its first question, along with the category name"""
        if self.undiscussed_generic_categories:
            category_name = choice(self.undiscussed_generic_categories)
            question = self.get_first_unasked_question(category_name)
            return category_name, question
        else:
            return None, None

    def get_first_unasked_question(self, category_name: str) -> Optional[CategoryQuestion]:
        """Returns the first unasked question for category_name, or None if we've asked them all"""

        logger.info(f'Getting first unasked question for category_name={category_name}')
        question_counter = self.questions_used[category_name]  # dict mapping str to int
        category_class = CATEGORYNAME2CLASS[category_name]  # Category subclass

        for question in category_class.questions:  # question is CategoryQuestion class
            question_str = question.question
            if question_counter[question_str] == 0:
                logger.info(f'Found unasked question for category_name={category_name}: {question_str}')
                return question
        logger.info(f'Found no unasked questions for category_name={category_name}')
        return None

    def get_first_untold_statement(self, category_name: str, state_manager=None) -> Optional[CategoryQuestion]:
        """Returns the first untold statement for category_name, or None if we've asked them all"""

        logger.info(f'Getting first untold statement for category_name={category_name}')
        statement_counter = self.statements_used[category_name]  # dict mapping str to int
        category_class = CATEGORYNAME2CLASS[category_name]  # Category subclass

        statement_values = None
        if state_manager and category_name in CATEGORY_WITH_STATEMENTS:
            # statement_type = state_manager.current_state.experiments.look_up_experiment_value('statement_type')
            # turned off experiment: personal_experience performs best
            statement_type = 'personal_experience'
            if statement_type == 'personal_opinion':
                statement_values = category_class.personal_opinions
            elif statement_type == 'personal_experience':
                statement_values = category_class.personal_experiences
            elif statement_type == 'general_statement':
                statement_values = category_class.general_statements

        if statement_values is not None:
            for statement in statement_values:
                statement_str = statement.question
                if statement_counter[statement_str] == 0:
                    logger.info(f'Found unused statement for category_name={category_name}: {statement_str}')
                    return statement
        logger.info(f'Found no untold statement for category_name={category_name}')
        return None

    def get_first_category_response(self, category_name: str, state_manager)-> Optional[CategoryQuestionStatement]:
        """Returns the pair of statement, question to respond to the user."""
        statement_part = self.get_first_untold_statement(category_name, state_manager)
        question_part = self.get_first_unasked_question(category_name)
        # category_style = state_manager.current_state.experiments.look_up_experiment_value('category_style')
        category_style = 'question_and_statement' # no longer experimenting

        if category_style == 'question' or statement_part is None:
            if question_part is None:
                return None
            return CategoryQuestionStatement(None, question_part.question,
                                             question_part.cur_entity_wiki_name,
                                             question_part.expected_type)
        elif category_style == 'statement' or question_part is None:
            if statement_part is None:
                return None
            return CategoryQuestionStatement(statement_part.question, None, statement_part.cur_entity_wiki_name, statement_part.expected_type)
        else: # category_style == 'question_and_statement'
            if question_part is None or statement_part is None:
                return None
            return CategoryQuestionStatement(statement_part.question, question_part.question, question_part.cur_entity_wiki_name, question_part.expected_type)

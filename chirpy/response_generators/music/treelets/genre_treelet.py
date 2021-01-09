from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.core.response_generator_datatypes import emptyResult, emptyPrompt

from chirpy.response_generators.music.treelets.abstract_treelet import Treelet, TreeletType


TRIGGER_CATEGORIES = [
    'genre',
    'subgenre'
]

class GenreTreelet(Treelet):

    def __init__(self, rg):
        super().__init__(rg)
        self.name = "genre"
        self.repr = "Genre Treelet"
        self.treelet_type = TreeletType.HEAD
        self.trigger_categories = self.get_trigger_categories()

    def get_trigger_categories(self):
        return TRIGGER_CATEGORIES

    def get_trigger_utterances(self):
        return [
            'music category',
            'music kind',
            'music type',
            'music style',
            'music taste',
            'category of music',
            'kind of music',
            'type of music',
            'style of music',
            'taste of music',
            'song category',
            'song kind',
            'song type',
            'song style',
            'category of song',
            'kind of song',
            'type of song',
            'style of song'
        ]

    def get_response(self, state, utterance):
        text = "MUSIC This is GENRE treelet"
        return ResponseGeneratorResult(text=text, priority=ResponsePriority.CAN_START,
                                       needs_prompt=True, state=state, cur_entity=None,
                                       conditional_state=state)

import logging
from typing import Dict, List, Tuple
from dataclasses import asdict, dataclass

logger = logging.getLogger('chirpylogger')

GRANDMA_WORDS = ['grandma', 'grandmother', 'granny']
GRANDPA_WORDS = ['granddad', 'grandpa', 'grandfather', 'granddaddy']

YOU_MENTIONED = [
    "You mentioned your {name}.",
    "I think you mentioned your {name}.",
]

YOU_MENTIONED_EARLIER = [
    "You mentioned your {name} earlier.",
    "I think you mentioned your {name} earlier.",
]

BRIDGE = [
    ("I'd love to hear more about {them}, if you'd like to share.", []),
    ("I'd be interested to hear about {them}, if you'd like to tell me.", ['interest']),
]

UNIVERSAL_PERSON_STRATEGIES = {
    'NO_ADDITIONAL_QUESTION': [''],
    'WHAT_ARE_THEY_LIKE': ["What {are} {they} like?"],
    'WHAT_DO_TOGETHER': ["What do you like to do together?", "What's something you enjoy doing together?", "What do you like to do when you hang out?"],
    'MEMORY': ["What's something fun you've done together?", "What's something memorable you've done together?"],
}

PERSON_STRATEGIES = {
    'WHAT_ADMIRE': ["What's something that makes {them} unique?", "What's something you admire about {them}?", "What's something you really appreciate about {them}?"],
    'PERSONALITY': ["How would you describe {their} personality?"],
    'WHAT_THEIR_INTERESTS': ["What are some of {their} interests?"],
    'SHARED_INTEREST': ["What's an interest you both have in common?", "What's something you're both interested in?"],
    'HOW_YOU_MEET': ["How did you guys meet?"],
    'HOW_THEY_MEET': ["How did they meet?"],
    'DO_THEY_LIVE_NEARBY': ["Do {they} live nearby?"],
    'HOW_KEEP_IN_CONTACT': ["How do you guys like to keep in contact?"],
    'HOW_MANY': ["How many {name} do you have?"],
}
PERSON_STRATEGIES.update(UNIVERSAL_PERSON_STRATEGIES)

SINGULAR_PARENT_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['WHAT_ADMIRE', 'SHARED_INTEREST', 'PERSONALITY', 'WHAT_THEIR_INTERESTS']
SINGULAR_GRANDPARENT_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['WHAT_ADMIRE', 'SHARED_INTEREST', 'PERSONALITY', 'WHAT_THEIR_INTERESTS', 'DO_THEY_LIVE_NEARBY']
PARENTAL_COUPLE_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['HOW_THEY_MEET']
SINGULAR_FRIEND_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['WHAT_ADMIRE', 'SHARED_INTEREST', 'DO_THEY_LIVE_NEARBY', 'HOW_KEEP_IN_CONTACT', 'HOW_YOU_MEET', 'PERSONALITY', 'WHAT_THEIR_INTERESTS']
PLURAL_FRIEND_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['DO_THEY_LIVE_NEARBY', 'HOW_KEEP_IN_CONTACT', 'HOW_YOU_MEET']
PARTNER_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['WHAT_ADMIRE', 'SHARED_INTEREST', 'HOW_YOU_MEET', 'PERSONALITY', 'WHAT_THEIR_INTERESTS']
SINGULAR_SIBLING_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['WHAT_ADMIRE', 'SHARED_INTEREST', 'PERSONALITY', 'WHAT_THEIR_INTERESTS']
PLURAL_SIBLING_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['HOW_MANY']
SINGULAR_COUSIN_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['WHAT_ADMIRE', 'SHARED_INTEREST', 'DO_THEY_LIVE_NEARBY', 'HOW_KEEP_IN_CONTACT', 'PERSONALITY', 'WHAT_THEIR_INTERESTS']
PLURAL_COUSIN_STRATEGIES = list(UNIVERSAL_PERSON_STRATEGIES.keys()) + ['DO_THEY_LIVE_NEARBY', 'HOW_KEEP_IN_CONTACT', 'HOW_MANY']

UNIVERSAL_PETCHILD_STRATEGIES = {
    'NO_ADDITIONAL_QUESTION': [''],
    'WHAT_ARE_THEY_LIKE': ["What {are} {they} like?"],
    'WHAT_DO_TOGETHER': ["What do you like to do together?", "What's something you enjoy doing together?"],
    'WHAT_THEY_LIKE_DO': ["What {do} {they} like to do?"],
    'HOW_OLD': ["How old {are} {they}?"],
}

PET_CHILD_STRATEGIES = {
    'WHAT_ADMIRE': ["What's something that makes {them} unique?", "What's something you really appreciate about {them}?"],
    'WHAT_TYPE': ["What kind of {name} do you have?"],
    'PERSONALITY': ["How would you describe {their} personality?"],
    'HOW_MANY': ["How many {name} do you have?"],
}
PET_CHILD_STRATEGIES.update(UNIVERSAL_PETCHILD_STRATEGIES)

SINGULAR_PET_STRATEGIES = list(UNIVERSAL_PETCHILD_STRATEGIES.keys()) + ['WHAT_ADMIRE', 'WHAT_TYPE', 'PERSONALITY']
PLURAL_PET_STRATEGIES = list(UNIVERSAL_PETCHILD_STRATEGIES.keys()) + ['WHAT_TYPE', 'HOW_MANY']
SINGULAR_CHILD_STRATEGIES = list(UNIVERSAL_PETCHILD_STRATEGIES.keys()) + ['WHAT_ADMIRE', 'PERSONALITY']
PLURAL_CHILD_STRATEGIES = list(UNIVERSAL_PETCHILD_STRATEGIES.keys()) + ['HOW_MANY']

PRONOUNS = {
    'F': ['she', 'her', "she's", 'is', 'her'],
    'M': ['he', 'him', "he's", 'is', 'his'],
    'N': ['they', 'them', "they're", 'are', 'their'],
    'P': ['they', 'them', "they're", 'are', 'their'],
    'O': ['it', 'it', "it's", 'is', 'its'],
}


@dataclass
class UserFamilyMember:
    trigger_phrases: List[str]  # phrases which, when mentioned preceded by 'my', trigger us to ask starter questions
    strategies: List[str]  # non-empty list of keys (in all_strategy_templates) that are valid for this UserFamilyMember
    pronoun: str  # key in PRONOUNS

    @property
    def all_strategy_templates(self) -> Dict[str, List[str]]:
        """
        Returns the dict that contains all the strategies and templates, in which we can lookup self.strategies.
        Needs to be implemented in child classes.
        """
        raise NotImplementedError("all_strategy_templates needs to be implemented in the child classes")

    @property
    def name(self) -> str:
        return self.trigger_phrases[0]

    @property
    def name_plural(self) -> str:
        if self.pronoun == 'P':
            return self.name
        else:
            return self.name+'s'

    @property
    def they(self) -> str:
        if self.pronoun in ['O']:
            return f'your {self.name}'
        else:
            return PRONOUNS[self.pronoun][0]

    @property
    def them(self) -> str:
        if self.pronoun in ['O']:
            return f'your {self.name}'
        else:
            return PRONOUNS[self.pronoun][1]

    @property
    def theyre(self) -> str:
        if self.pronoun in ['O']:
            return f"your {self.name}'s"
        else:
            return PRONOUNS[self.pronoun][2]

    @property
    def are(self) -> str:
        return PRONOUNS[self.pronoun][3]

    @property
    def their(self) -> str:
        if self.pronoun in ['O']:
            return f"your {self.name}'s"
        else:
            return PRONOUNS[self.pronoun][4]

    @property
    def a(self) -> str:
        if self.pronoun == 'P':
            return 'are'
        else:
            return 'a'

    @property
    def do(self) -> str:
        if self.pronoun in ['P', 'N']:
            return 'do'
        else:
            return 'does'

    @property
    def formatters(self) -> Dict[str, str]:
        return {'name': self.name, 'name_plural': self.name_plural, 'they': self.they, 'them': self.them, 'theyre': self.theyre, 'are': self.are, 'their': self.their, 'a': self.a, 'do': self.do}

    @property
    def you_mentioned_earlier(self) -> List[str]:
        """Returns a non-empty list of 'You mentioned your X earlier.' phrases"""
        return [t.format(**self.formatters) for t in YOU_MENTIONED_EARLIER]

    @property
    def you_mentioned(self) -> List[str]:
        """Returns a non-empty list of 'You mentioned your X.' phrases"""
        return [t.format(**self.formatters) for t in YOU_MENTIONED]

    def bridges(self, starter_question: str) -> List[str]:
        """
        Given starter_question, returns a non-empty list of bridge phrases (like "I'd love to hear more about them") to
        use after "You mentioned your X" and before the starter_question. Avoids picking bridges that have phrases
        in common with the starter question.
        """
        templates = [t for (t, avoid_phrases) in BRIDGE if all(p not in starter_question for p in avoid_phrases)]
        if len(templates) == 0:
            logger.error(f"The UserFamilyMember {self} has no bridges for starter_question={starter_question}.")
        return [t.format(**self.formatters) for t in templates]

    @property
    def strategy2starterq(self) -> Dict[str, List[str]]:
        """
        Returns a dict mapping from valid strategy names for this UserFamilyMember (str), to a list of starter
        questions for that strategy (list of str), formatted for this UserFamilyMember. The dict is guaranteed to
        contain all the strategies in self.strategies and a non-empty list for each.
        """
        output = {strat: [template.format(**self.formatters) for template in self.all_strategy_templates[strat]] for strat in self.strategies}
        for strat in self.strategies:
            assert strat in output, f"In {self}, strategy '{strat}' is not in strategy2starterq"  # contains all strategies in self.strategies
            assert len(output[strat]) > 0, f"In {self}, strategy '{strat}' maps to an empty list"  # all lists are nonempty
        return output

    def get_mentioned_trigger_phrase(self, current_state) -> Tuple[List[str], bool]:
        """
        Given current_state, determine if the user is mentioning any of the trigger phrases for this UserFamilyMember.

        Returns:
            trigger_phrase: Optional[str]. The first of self.trigger_phrases that is mentioned by the user on this turn.
                If none are mentioned, is None.
            posnav: bool. True iff the trigger_phrase is in the posnav slot
        """
        user_utterance = current_state.text
        nav_intent = current_state.navigational_intent
        for trigger_phrase in self.trigger_phrases:
            if 'my {}'.format(trigger_phrase) in user_utterance:
                posnav = nav_intent.pos_intent and nav_intent.pos_topic_is_supplied and trigger_phrase in nav_intent.pos_topic[0]
                return trigger_phrase, posnav
        return None, False


class Person(UserFamilyMember):

    @property
    def all_strategy_templates(self) -> Dict[str, List[str]]:
        return PERSON_STRATEGIES


class PetOrChild(UserFamilyMember):

    @property
    def all_strategy_templates(self) -> Dict[str, List[str]]:
        return PET_CHILD_STRATEGIES



OLDER_FAMILY_MEMBERS = [
    Person(['parents'], PARENTAL_COUPLE_STRATEGIES, 'P'),
    Person(['great-grandparents', 'great grandparents'], PARENTAL_COUPLE_STRATEGIES, 'P'),
    Person(['grandparents'], PARENTAL_COUPLE_STRATEGIES, 'P'),
    Person(['mom', 'mommy', 'mother', 'mum'], SINGULAR_PARENT_STRATEGIES, 'F'),
    Person(['dad', 'daddy', 'father', 'old man'], SINGULAR_PARENT_STRATEGIES, 'M'),
    Person(['aunt', 'auntie', 'aunty'], SINGULAR_PARENT_STRATEGIES, 'F'),
    Person(['uncle'], SINGULAR_PARENT_STRATEGIES, 'M'),
    Person(GRANDMA_WORDS + ['great-' + w for w in GRANDMA_WORDS] + ['great ' + w for w in GRANDMA_WORDS], SINGULAR_GRANDPARENT_STRATEGIES, 'F'),
    Person(GRANDPA_WORDS + ['great-' + w for w in GRANDPA_WORDS] + ['great ' + w for w in GRANDPA_WORDS], SINGULAR_GRANDPARENT_STRATEGIES, 'M'),
]

FRIENDS = [
    Person(['friends'], PLURAL_FRIEND_STRATEGIES, 'P'),
    Person(['friend', 'best friend'], SINGULAR_FRIEND_STRATEGIES, 'N'),
]

PARTNERS = [
    Person(['boyfriend'], PARTNER_STRATEGIES, 'M'),
    Person(['girlfriend'], PARTNER_STRATEGIES, 'F'),
    Person(['husband', 'hubby'], PARTNER_STRATEGIES, 'M'),
    Person(['wife'], PARTNER_STRATEGIES, 'F'),
    Person(['partner', 'spouse'], PARTNER_STRATEGIES, 'N'),
]

SIBLINGS_AND_COUSINS = [
    Person(['sisters'], PLURAL_SIBLING_STRATEGIES, 'P'),
    Person(['brothers'], PLURAL_SIBLING_STRATEGIES, 'P'),
    Person(['siblings'], PLURAL_SIBLING_STRATEGIES, 'P'),
    Person(['cousins'], PLURAL_COUSIN_STRATEGIES, 'P'),
    Person(['sister'], SINGULAR_SIBLING_STRATEGIES, 'F'),
    Person(['brother'], SINGULAR_SIBLING_STRATEGIES, 'M'),
    Person(['sibling'], SINGULAR_SIBLING_STRATEGIES, 'N'),
    Person(['cousin'], SINGULAR_COUSIN_STRATEGIES, 'N'),
]

KIDS = [
    PetOrChild(['sons', 'little boys'], PLURAL_CHILD_STRATEGIES, 'P'),
    PetOrChild(['daughters', 'little girls'], PLURAL_CHILD_STRATEGIES, 'P'),
    PetOrChild(['kids', 'children', 'little ones'], PLURAL_CHILD_STRATEGIES, 'P'),
    PetOrChild(['son', 'little boy'], SINGULAR_CHILD_STRATEGIES, 'M'),
    PetOrChild(['daughter', 'little girl'], SINGULAR_CHILD_STRATEGIES, 'F'),
    PetOrChild(['kid', 'child', 'baby'], SINGULAR_CHILD_STRATEGIES, 'N'),
]

PETS = [
    PetOrChild(['pets'], ['WHAT_TYPE', 'WHAT_ARE_THEY_LIKE'], 'P'),
    PetOrChild(['cats'], PLURAL_PET_STRATEGIES, 'P'),
    PetOrChild(['dogs'], PLURAL_PET_STRATEGIES, 'P'),
    PetOrChild(['pet'], ['WHAT_TYPE', 'WHAT_ARE_THEY_LIKE'], 'O'),
    PetOrChild(['cat'], SINGULAR_PET_STRATEGIES, 'O'),
    PetOrChild(['dog'], SINGULAR_PET_STRATEGIES, 'O'),
]



if __name__=="__main__":
    for name in asdict(PETS).keys():
        print()
        print(name)
        data = getattr(PETS, name)
        for s in data.you_mentioned:
            print(s)
        print()
        for s in data.bridges(''):
            print(s)
        print()
        for strat, qs in data.strategy2starterq.items():
            print(strat, qs)

import re
from time import perf_counter_ns
import unittest
import logging

from chirpy.core.regex.util import oneof

logger = logging.getLogger('chirpylogger')


MAX_TIME_FOR_EXECUTE = 0.001  # max time in seconds that we want execute() to take

def print_exception(title, msg):
    print("=" * 80)
    print(f"FAIL: {title}")
    print("=" * 80)
    print()
    print(msg)
    print()

class RegexTemplate(unittest.TestCase):
    """
    A class to specify a regex template that can be used to match text and extract slots.
    This class inherits from TestCase and implements a test (test_examples) so that any subclass of RegexTemplate
    will automatically be a TestCase with the test_examples test.
    """

    # The following class constants should be overwritten by the subclass inheriting from RegexTemplate:

    # slots should be a dict mapping from string (slot name) to either a string (a regex) or a list of strings.
    # A list of strings will be interpreted as an "OR" regex among the members, e.g. ["yes", "yeah"] -> "yes|yeah"
    slots = None

    # templates should be a list of strings, representing possible templates, possibly containing {slots}.
    # Note that when the RegexClassifier executes on an input string, it returns the FIRST matching template, as ordered
    # in this list. So if text could match multiple of your templates, put the one you want first.
    templates = None

    # positive_examples should be a list of (string, dict) pairs.
    # The string should be an input text that should match the template, and the dict is the expected slot mapping.
    positive_examples = None

    # negative_examples should be a list of strings, representing input texts that shouldn't match the template.
    negative_examples = None

    def __init__(self, *args, **kwargs):
        """
        Note that we can't change the signature of __init__ because we're inheriting from TestCase.
        TestCase needs to be able to init this class with its expected args/kwargs.
        """
        logger.debug(f'RegexTemplate ({type(self).__name__}) is starting __init__...')
        t0 = perf_counter_ns()
        super().__init__(*args, **kwargs)  # init TestCase parent class
        time_for_parent_init = perf_counter_ns()-t0

        # Only need to do the rest of initializing if we're initializing a subclass of RegexTemplate
        if type(self) == RegexTemplate:
            return

        # Check that slots, templates, positive_examples and negative_examples have been defined by the subclass
        assert self.slots is not None, 'self.slots should not be None. It should be defined as a class constant in the class inheriting from RegexTemplate.'
        assert self.templates is not None, 'self.templates should not be None. It should be defined as a class constant in the class inheriting from RegexTemplate.'
        assert self.positive_examples is not None, 'self.positive_examples should not be None. It should be defined as a class constant in the class inheriting from RegexTemplate.'
        assert self.negative_examples is not None, 'self.negative_examples should not be None. It should be defined as a class constant in the class inheriting from RegexTemplate.'

        # In self.slots, convert lists of strings to "OR" regex strings
        for name, value in self.slots.items():
            if isinstance(value, list):
                self.slots[name] = oneof(value)
            else:
                assert isinstance(value, str), f"The values in the slots dictionary should be either strings or lists of strings, not {type(value)}"

        # Dictionary from slot name -> regex for that slot in a named group
        # e.g. 'my_name_is' -> '(?P<my_name_is>my name is|call me|i'm called)'
        slot_name_to_regex_group = {
            slot_name: "(?P<{}>{})".format(slot_name, slot_regex) for slot_name, slot_regex in
            self.slots.items()
        }

        # For each template, replace each {slot_name} with its regex. Also add start and end characters (^ and $).
        # e.g. '{my_name_is} {name}' -> '^(?P<my_name_is>my name is|call me|i'm called) (?P<name>.+?)$'
        regexes = ['^' + template.format(**slot_name_to_regex_group) + '$' for template in
                   self.templates]

        # Compile the regexes
        t0_compile = perf_counter_ns()
        self.compiled_regexes = []
        for r in regexes:
            # t0_indiv = perf_counter_ns()
            self.compiled_regexes.append(re.compile(r))
            # logger.debug(f'RegexTemplate ({type(self).__name__}) took {(perf_counter_ns()-t0_indiv)/10**9} seconds to compile {r}')
        time_to_compile = perf_counter_ns() - t0_compile

        logger.debug(f'RegexTemplate ({type(self).__name__}) finished __init__, compiling {len(self.compiled_regexes)} regexes. '
                     f'Took {(perf_counter_ns()-t0)/10**9} seconds total, of which {time_for_parent_init/10**9} seconds were for TestCase.__init__ '
                     f'and {time_to_compile/10**9} seconds were for re.compile.')

    def execute(self, input_string: str):
        """
        Try to match input_string against self.compiled_regexes, in order.
        Returns the slot values for the FIRST matched regex, or returns None if no match is found.
        """
        t0 = perf_counter_ns()
        logger.setLevel(logging.DEBUG)
        logger.debug(f'RegexTemplate ({type(self).__name__}) is executing on "{input_string}", checking against {len(self.compiled_regexes)} compiled regexes...')
        for idx, r in enumerate(self.compiled_regexes):
            # t0_indiv = perf_counter_ns()
            matched = r.match(input_string)
            # logger.debug(f'RegexTemplate ({type(self).__name__}) took {(perf_counter_ns()-t0_indiv)/10**9} seconds for regex {r}')
            if matched:
                logger.debug(f'RegexTemplate ({type(self).__name__}) finished executing on "{input_string}". '
                             f'Matched with compiled regex {idx} of {len(self.compiled_regexes)}, '
                             f'Took {(perf_counter_ns()-t0)/10**9} seconds total')
                return {k: v for k,v in matched.groupdict().items() if v is not None}
        logger.debug(f'RegexTemplate ({type(self).__name__}) finished executing on "{input_string}". '
                     f'Matched with none of {len(self.compiled_regexes)} compiled regexes. '
                     f'Took {(perf_counter_ns() - t0)/10**9} seconds total')
        return None

    def test_examples(self):
        # This function checks that self.positive_examples match the template and self.negative_examples don't

        # Don't run tests for the base class (RegexTemplate), only subclasses
        if type(self) == RegexTemplate:
            raise unittest.SkipTest('skipping testing base class')

        # Test positive
        for (text, expected_slots) in self.positive_examples:
            slots = self.execute(text)
            try:
                self.assertIsNotNone(slots, f'positive example "{text}" did not match {type(self).__name__}')
                self.assertDictEqual(slots, expected_slots, f'positive example "{text}" matched {type(self).__name__}, but the resulting slots {slots} do not match the expected slots {expected_slots}')
            except AssertionError as e:
                print_exception(f"{self.__class__.__name__}.pos_test_{text.replace(' ', '_')}", e)

        # Test negative
        for text in self.negative_examples:
            slots = self.execute(text)
            try:
                self.assertIsNone(slots, f'negative example "{text}" matched {type(self).__name__}')
            except AssertionError as e:
                print_exception(f"{self.__class__.__name__}.neg_test_{text.replace(' ', '_')}", e)

    def test_speed(self):
        if type(self) == RegexTemplate:
            raise unittest.SkipTest('skipping testing base class')

        word = 'asdfasdf'  # a word that will match nothing except regex components designed to catch anything
        length2time = {}
        for length in [5, 10, 20, 50, 100]:
            text = ' '.join([word for _ in range(length)])
            t0 = perf_counter_ns()
            self.execute(text)
            time_taken = (perf_counter_ns() - t0)/10**9
            length2time[length] = time_taken
            try:
                self.assertLess(time_taken, MAX_TIME_FOR_EXECUTE, f'{type(self).__name__} took {time_taken} seconds (more than MAX_TIME_FOR_EXECUTE={MAX_TIME_FOR_EXECUTE}) executing on an input length {length}')
            except AssertionError as e:
                print_exception(f"{self.__class__.__name__}.timed_test_length_{length}", e)

        print(f'{type(self).__name__} speeds: ' + ', '.join([f'{length} words: {time} seconds' for length, time in length2time.items()]))
"""This file contains some thresholds that are used in the entity linker"""

SCORE_THRESHOLD_HIGHPREC = 0  # Generally, a LinkedSpan needs its top entity to have a score greater than this to be high precision
SCORE_THRESHOLD_EXPECTEDTYPE = 0  # If we have an expected type, we look for entities of expected type with this score or higher to become cur_entity
SCORE_THRESHOLD_NAV_ABOUT = 0  # when the user says "I want to talk about X", we look for any entities with this score or higher in X
SCORE_THRESHOLD_NAV_NOT_ABOUT = 0  # when the user says "I want to talk X", we look for any entities with this score or higher in X
SCORE_THRESHOLD_ELIMINATE_OUTER_SPAN = 0  # if an outer span has a score below this, and an inner span has score above SCORE_THRESHOLD_HIGHPREC, the inner span wins
SCORE_THRESHOLD_CHOOSE_INNER_SPAN_OF_TYPE = 0  # if an inner span has a score above this and is of expected type, and the outer span has a lower score and is not of expected type, the inner span wins
SCORE_THRESHOLD_ELIMINATE_DONT_LINK_WORDS = 0  # in a LinkedSpan, if a candidate entity has a score below this, and the span consists entirely of DONT_LINK_WORDS, discard the candidate entity
SCORE_THRESHOLD_ELIMINATE_HIGHFREQUNIGRAM_SPAN = 0  # in a LinkedSpan, if a candidate entity has a score below this, and the span consists entirely of high-freq unigrams, discard the candidate entity (see usage for more detailed rules)
SCORE_THRESHOLD_ELIMINATE = 0  # in a LinkedSpan, if a candidate entity has a score below this, remove it
UNIGRAM_FREQ_THRESHOLD = 9  # unigram spans need a frequency lower than this to be high precision
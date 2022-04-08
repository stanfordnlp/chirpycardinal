## CC: This is unused.

from typing import List, Optional

from chirpy.annotators.corenlp import Sentiment
from chirpy.response_generators.personal_issues.response_templates.response_components import QUESTIONS_REFLECTIVE, \
    STATEMENTS_VALIDATE, QUESTIONS_SOLUTION, QUESTIONS_ENCOURAGE_SHARING, STATEMENTS_OFFER_LISTEN, \
    SUB_TAG_QUESTION, SUB_NEUTRAL_PRE_INTERJECTION, SUB_TENTAFIERS, SUB_SUBJUNCTIVE_PRE, WORD_BOT_PERSONAL_EMOTION_NEGATIVE, \
    WORD_USER_PERSONAL_EMOTION_NEGATIVE, WORD_PERSONAL_EMOTION_POSITIVE, WORD_SUPERLATIVE, \
    SUB_EMOTION_INFINITIVE, WORD_OBJECTIVE_EMOTION_NEGATIVE, WORD_OBJECTIVE_EMOTION_POSITIVE
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST
from chirpy.core.response_generator.response_template import ResponseTemplateFormatter

import logging
import random
import string
import operator
import re
from itertools import chain

logger = logging.getLogger('chirpylogger')

from chirpy.annotators.corenlp import Sentiment

PENN_TREEBANK_ADVERB_PREFIX = 'RB'
POV_TRANSLATION_DICT = {
    "am": "are",
    "was": "were",
    "i": "you",
    "my": "your",
    "are": "am",
    "you've": "i've",
    "you'll": "i'll",
    "your": "my",
    "yours": "mine",
    "you": "me",
    "me": "you",
    "i'm": "you're",
    "i'll": "you'll",
    "i've": "you've",
    "i'd": "you'd",
    "you'd": "i'd",
    "'m": "'re"
}


class TemplateBasedParaphraser(object):
    def __init__(self):
        """This class is to be used by the SubsequentResponseTreelet (see ...personal_issues/treelets/subsequent_response_treelet.py)
        to paraphrase user responses. This initializes the Paraphraser with the global state of the Cobot instance, so this class
        has access to the annotations from the NLP pipeline.
        """

    def clean_contractions(self, tokens: List[str]) -> List[str]:
        """This method is admittedly hacky; it takes a list of tokens, and cleans up contractions by combining parts of
        contractions with the rest of the word. As example input-output behavior:

        <input> => <output>
        =====================
        tokens=["have", "n't"] => ["haven't"]
        tokens=["did", "n't"] => ["didn't"]
        tokens=["You", "'re"] => ["You're"]

        Args:
            tokens (List[str]): List of string tokens

        Returns:
            List[str]: The same list, with contractions cleaned as described above.
        """
        while "n't" in tokens: # HACK: ....do i need to explain why this is a hack? :'(
            contraction_end_idx = tokens.index("n't")
            tokens[contraction_end_idx-1:contraction_end_idx+1] = [''.join(tokens[contraction_end_idx-1:contraction_end_idx+1])]
        contraction_detector = list(map(lambda x: x.startswith("'"), tokens))
        while any(contraction_detector):
            contraction_end_idx = contraction_detector.index(True)
            tokens[contraction_end_idx-1:contraction_end_idx+1] = [''.join(tokens[contraction_end_idx-1:contraction_end_idx+1])]
            contraction_detector = list(map(lambda x: x.startswith("'"), tokens))
        return tokens


    def add_sentiment_phrases(self, sentiment: Sentiment, paraphrase: str,
                              pre_text_probability: Optional[float] = 1/2,
                              post_text_probability: Optional[float] = 1/2):
        """This method decorates a paraphrase by pre-pending or appending clauses to the start
        or end of generated paraphrases (i.e. "So, ..." or "..., is that right?") to facilitate
        a more natural-sounding response. Note that this method will not add a clause to both
        the start and end of the sentence; in practice, doing so can lead to an awkward-sounding responses
        (i.e. "Let's see now, it sounds like you've been having a difficult time lately, is that right?")

        Args:
            sentiment (Sentiment): The annotator sentiment returned by the CoreNLP annotator
                (see ...chirpy/annotators/corenlp.py); used for selecting adjectives with appropriate
                valence.
            paraphrase (str): Raw paraphrase string.
            pre_text_probability (Optional[float], optional): Probability that tokens are added to the
                start of the paraphrase. Defaults to 1/3.
            post_text_probability (Optional[float], optional): Probability that tokens are added to the
                end of the paraphrase. Defaults to 1/3.

            Exactly ONE of pre_text_probability and post_text_probability must be specified. The
            helper _threshold_helper takes both keywords, and outputs the following:

                - pre_threshold (float, between 0 and 1): if random.random() < pre_threshold, then a clause
                    is added to the beginning of the paraphrase.
                - post_threshold (float, between 0 and 1): if random.random() > post_threshold, then a clause
                    is added to the end of the paraphrase.

            Implicitly, if random.random() falls between pre_threshold and post_threshold, then nothing is added.

        """
        def _threshold_helper(pre_text_probability: float, post_text_probability: float):
            if pre_text_probability and post_text_probability:
                if pre_text_probability + post_text_probability > 1:
                    raise ValueError("Pre-text and post-text sampling probabilities must sum"
                                     + f" to less than one ({pre_text_probability} + {post_text_probability})"
                                     + f"= {pre_text_probability + post_text_probability} > 1)")
                return pre_text_probability, 1 - post_text_probability
            raise ValueError("Both 'pre_text_probability' or 'post_text_probability'"
                             + f" must be provided to _add_sentiment_phrases, but got pre_text_probability={pre_text_probability}"
                             + f" and post_text_probability={post_text_probability}.")

        pre_threhsold, post_threshold = _threshold_helper(pre_text_probability, post_text_probability)
        if random.random() < pre_threhsold:
            response = " ".join([self.sample_pre_text(sentiment), paraphrase]).strip()
        elif random.random() > post_threshold:
            response = " ".join([paraphrase, self.sample_post_text(sentiment)]).strip()
        else:
            response = paraphrase
        if response[-1] not in string.punctuation:
            response += "."
        return response

    def prepend_first_person_pronoun(self, verbphrase: str) -> str:
        """Since the CoreNLP annotator outputs verb phrases, the phrase does not include personal
        pronouns. This is a preprocessing method that adds the first-person pronoun 'i' to the
        start of the verb phrase, in order to facilitate fluent paraphrasing.

        Args:
            verbphrase (str): A verb phrase returned by CoreNLP.

        Returns:
            [str]: The same verb phrase with a first-person pronoun added.
        """
        if verbphrase.startswith("'"):
            verbphrase = f'i{verbphrase}' # HACK: deal w/ splitting at the apostrophe
        else:
            verbphrase = f'i {verbphrase}' # HACK: this just adds first-person pronoun to the top of the verb phrase
        return verbphrase

    def pov_translate(self, utterance: str) -> str:
        """This quotes back the user utterance by replacing first-person pronoun occurrences
        with the corresponding second-person pronoun. Used to simulate ELIZA-like paraphrasing.

        Args:
            utterance (str): A portion of the user utterance.

        Returns:
            str: The same utterance with first-person pronouns replaced with second-person pronouns.
        """
        tokens = utterance.lower().split()
        translated_utterance = [POV_TRANSLATION_DICT[word] if word in POV_TRANSLATION_DICT else word for word in tokens]
        final_paraphrase = self.clean_contractions(translated_utterance)
        return " ".join(final_paraphrase)


    def get_response_probability_distribution(self, responses: List[str], null_response_probability: float) -> List[float]:
        """This utility function is designed for sampling from response components (see
        ...persoanlity/response_templates/response_components.py) with null (non-word) components. This can be
        useful if our response string contains just a sentence-ending mark, and we want granular control of
        how often we sample such a response. We use a greedy regex search to find the first "null" response element and set the
        corresponding probability of sampling that null element to null_response_probability.

        Args:
            responses (List[str]): List of possible responses to be sampled
            null_response_probability (float): Probability of sampling the null element.

        Returns:
            List[float]: A probability mass function for sampling, corresponding to the indices of parameter
                'responses.' Can be used directly in random.choices().
        """
        null_index = [re.search('\w', response) for response in responses].index(None)
        non_null_response_probability = 1 - null_response_probability
        n_non_null_responses = len(responses) - 1
        pmf = [non_null_response_probability / n_non_null_responses] * len(responses)
        pmf[null_index] = null_response_probability
        return pmf


    def sample_pre_text(self, sentiment: Sentiment) -> str:
        """This samples a clause that will go before the paraphrase. In practice, this usually entails
        the bot expressing its "own" emotion consistent with the valence of the user utterance (i.e.
        "I'm sad that this happened to you"), or commenting on the user's emotion (i.e. "You must feel
        dejected about this.").

        Args:
            sentiment (Sentiment): Sentiment enum from CoreNLP annotator (see ...cobot/chirpy/annotators/corenlp.py),
                used for determining what list of emotion-words to sample from.

        Returns:
            [type]: Sampled templated-based response.
        """
        # TODO: think abt design choices -- not sure if I should create a copy of each response template with a possible place for superlatives,
        # or (what the below is doing) simply sample a superlative word OR the empty string, and pre-pend whatever the result is to the
        # underlying emotion-sharing statement?
        superlative = (random.choice(WORD_SUPERLATIVE) + " ").lstrip()
        if sentiment < Sentiment.NEUTRAL:
            response = random.choice(SUB_SUBJUNCTIVE_PRE).format(bot_personal_emotion=superlative + random.choice(WORD_BOT_PERSONAL_EMOTION_NEGATIVE),
                                                                 user_personal_emotion=superlative + random.choice(WORD_USER_PERSONAL_EMOTION_NEGATIVE),
                                                                 objective_emotion=superlative + random.choice(WORD_OBJECTIVE_EMOTION_NEGATIVE),
                                                                 tentafier=random.choice(SUB_TENTAFIERS),
                                                                 emotion_infinitive=random.choice(SUB_EMOTION_INFINITIVE))
        elif sentiment > Sentiment.NEUTRAL:
            response = random.choice(SUB_SUBJUNCTIVE_PRE).format(bot_personal_emotion=superlative + random.choice(WORD_PERSONAL_EMOTION_POSITIVE),
                                                                 user_personal_emotion=superlative + random.choice(WORD_PERSONAL_EMOTION_POSITIVE),
                                                                 objective_emotion=superlative + random.choice(WORD_OBJECTIVE_EMOTION_POSITIVE),
                                                                 tentafier=random.choice(SUB_TENTAFIERS),
                                                                 emotion_infinitive=random.choice(SUB_EMOTION_INFINITIVE))
        else:
            #pmf = self.get_response_probability_distribution(SUB_NEUTRAL_PRE_INTERJECTION, null_response_probability)
            response = random.choices(SUB_NEUTRAL_PRE_INTERJECTION)[0]
        return response.strip()


    def sample_post_text(self, sentiment: Sentiment, null_response_probability: Optional[float] = 0.5) -> str:
        """This samples a clause that will go before the paraphrase. In practice, this usually entails
        a tag-question (i.e. "...right?", "...is that so?", "...is it?")

        Args:
            sentiment (str): currently unused, but can be utilized to create more emotionally specific
                responses in the future.
            null_response_probability (Optional[float], optional): Probability of sampling a null tag
                question (just "?"). Defaults to 0.5.

        Returns:
            str: [description]
        """
        pmf = self.get_response_probability_distribution(SUB_TAG_QUESTION, null_response_probability)
        return "\b" + random.choices(SUB_TAG_QUESTION, weights=pmf)[0] # HACK: makes the spacing correct; is there a more robust way to do this?


    def remove_adverbs_from_span(self, state, start: int, end: int) -> str:
        """Removes adverbs from a given span (start, end) in the current user utterance. This
        method will first extract a list of string tokens, then remove adverbs in the span
        tokens[start:end].

        Args:
            state: global COBOT state
            start (int): start index of the span
            end (int): ending index of the span

        Returns:
            str: an adverb-free version of the span given by tokens[start:end]
        """
        tokens = [token["originalText"] for token in state.corenlp['tokens']]
        token_pos_tags = [token["pos"] for token in state.corenlp['tokens']]
        return " ".join([tokens[i] for i in range(start, end) if not token_pos_tags[i].startswith(PENN_TREEBANK_ADVERB_PREFIX)])


    def extract_best_span_with_sentiment(self, state, sentiment: Optional[Sentiment] = None) -> str:
        """Given a list of spans; this method returns the span that contributes the most to the
        specified sentiment, returning the shortest span in the case of a tie. This also returns
        the token index of the span.

        Args:
            state: Cobot global state
            sentiment (Optional[Sentiment], optional): A sentiment. Defaults to None.

        Returns:
            str: string representation of span.
            int: start index of span in token list.
            int: ending index of span in token list.
        """

        def _get_sentiment_contribution_score(token_info):
            """

            Args:
                token_info (TokenSentimentInfo): data storing class with token-level sentiment info.

            Returns:
                float: weighted sentiment score.

            """
            return (1 - int(abs(token_info.sentiment - sentiment)) * 0.5) * token_info.sentiment_prob

        spans = state.corenlp['verbphrases']
        corenlp_sentiment_info = state.corenlp['sentiment_full']
        if not sentiment:
            sentiment = Sentiment(corenlp_sentiment_info["sentiment"])
        token_sentiment_info = [sentence_annotations["token_sentiment_info"] for sentence_annotations \
                                in corenlp_sentiment_info]

        token_sentiment_contribution_scores = list(chain(*[list(map(_get_sentiment_contribution_score, sentence_info)) \
                                                           for sentence_info in token_sentiment_info]))
        tokens = [token["originalText"] for token in state.corenlp['tokens']]

        span_scores = {}
        # calculate span scores
        for span in spans:
            span_tokens = span.split()
            # find span in full utterance
            indices = [i for i, token in enumerate(tokens) if token == span_tokens[0]] # there are certainly more elegant ways to do a sub-list search (i.e. Rabin-Karp)
            for idx in indices:
                if tokens[idx:idx+len(span_tokens)] == span_tokens:
                    # get "sentiment-ness" of each span
                    span_score = sum(token_sentiment_contribution_scores[idx:idx+len(span_tokens)])
                    span_scores[span] = (span_score, idx, idx+len(span_tokens))
                    break
        best_score, _, _ = max(span_scores.values(), key=operator.itemgetter(0))
        best_spans = [span for span, (score, _, _) in span_scores.items() if score == best_score]
        shortest_best_span = min(best_spans, default="", key=len)
        logger.primary_info(f"{self.__class__.__name__} span extraction under {sentiment}: tokens={tokens}, scores={token_sentiment_contribution_scores}."
                            + f" Returning span '{shortest_best_span}' with score {best_score}. Full spans with scores: {span_scores}")
        _, best_span_start, best_span_end = span_scores[shortest_best_span]
        return shortest_best_span, best_span_start, best_span_end



    def paraphrase(self, state) -> str:
        """This function paraphrases the user utterance using template-based methods. In general, the
        chain of operations is the following:

        1. Extract the top verbphrase from the CoreNLP annotator (see ...cobot/chirpy/annotators/corenlp.py). This
            is the main target of the paraphrasing class.
        2. Preprocess the verbphrase by adding the first person pronoun 'i' to the start of the phrases
            (via self.prepend_first_person_pronoun)
        3. Replace first-person pronouns with second-person pronouns (I'm sad about X -> You're sad about X) using
            self.pov_translate (i.e. "translate" the point of view).
        4. Sample possible beginning and ending clauses to add to the resultant paraphrase, intended to 1) increase
            response fluency and 2) generate empathetic dialogue.


        Args:
            utterance (str): The user utterance.

        Returns:
            str: Paraphrased user utterance.
        """

        response = ""
        # nounphrases = self.global_state.stanfordnlp['nounphrases']
        sentiment = state.corenlp['sentiment']
        best_span, start, end = self.extract_best_span_with_sentiment(state, sentiment)
        #adverb_free_span = self.remove_adverbs_from_span(state, start, end)
        best_span = self.prepend_first_person_pronoun(best_span)
        paraphrase = self.pov_translate(best_span)
        response = self.add_sentiment_phrases(sentiment, paraphrase)
        return response
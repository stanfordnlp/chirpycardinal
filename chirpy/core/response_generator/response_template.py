import logging
import random

logger = logging.getLogger('chirpylogger')

"""class ResponseTemplateFormatter

    The following class can be thought of as a "reverse-regex" matcher; instead of determining whether a 
    particular utterance matches a template given certain slots, this samples an utterance given a template
    and slots. Most treelets (see personal_issues/treelets directory) have a corresponding response template used to sample a 
    different response to give back to the user.

    Initialization is a no-op. The only fields that must be set when subclassing the ResponseTemplateFormatter
    are templates, a List[str] that contains format-string templates, and slots, which is a dictionary dict(str: List[str])
    that stores the possible utterances that can fill each slot. 

    METHODS

    - __init__()
        Args: None

        This is a no-op.

    - sample()
        Args: 
        - template_weights: a List[float] or List[int] with the same length as self.templates, that imposes a weighting for sampling 
            from the template list. Default "None" (uniform random sampling).
        - slot_weights: a dict(str: List[float/int]) with the same structure as self.slots, that imposes a weighting for sampling
            EACH slot. Default "None" (uniform random sampling).

        Given templates and a slot, this method samples a possible utterance and returns the resultant string. Ideally, this is then
        passed on to response-handling logic in the relevant treelet(s).

    
"""

class ResponseTemplateFormatter:
    templates = None  # list of strings
    slots = None  # a dict

    def __init__(self):
        super(ResponseTemplateFormatter, self).__init__()
        if not type(self) == ResponseTemplateFormatter:
            self._check_state()

    def sample(self, template_weights=None, slot_weights=None) -> str:
        template = random.choices(self.templates, template_weights, k=1)[0]
        if slot_weights:
            sampled_phrases = {k: random.choices(v, slot_weights[k], k=1)[0] for k, v in self.slots.items()}
        else:
            sampled_phrases = {k: random.choices(v, k=1)[0] for k, v in self.slots.items()}
        #logger.primary_info("From response template formatter: " + str(sampled_phrases))

        response_text = template.format(**sampled_phrases)
        return response_text

    def _check_state(self):
        assert self.templates is not None, "Templates must be overridden."
        assert self.slots is not None, "Slots must be overridden."
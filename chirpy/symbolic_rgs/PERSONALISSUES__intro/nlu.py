from chirpy.core.response_generator.nlu import nlu_processing
from chirpy.response_generators.personal_issues import personal_issues_helpers

@nlu_processing
def get_flags(rg, state, utterance):
    pass

@nlu_processing
def get_background_flags(rg, utterance):
    is_personal_issue = personal_issues_helpers.is_personal_issue(rg, utterance)
    ADD_NLU_FLAG('PERSONALISSUEINTRO_personal_sharing_negative', is_personal_issue)
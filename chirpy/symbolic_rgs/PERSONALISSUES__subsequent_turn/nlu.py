from chirpy.core.response_generator.nlu import nlu_processing
from chirpy.response_generators.personal_issues import personal_issues_helpers

@nlu_processing
def get_flags(rg, state, utterance):
    if personal_issues_helpers.is_gratitude_response(rg, utterance):
        ADD_NLU_FLAG('PERSONALISSUE_gratitude')
    if personal_issues_helpers.is_personal_issue(rg, utterance):
        ADD_NLU_FLAG('PERSONALISSUE_personal_sharing_negative')
    if personal_issues_helpers.is_continued_sharing(rg, utterance):
        ADD_NLU_FLAG('PERSONALISSUE_is_continued_sharing')
    if personal_issues_helpers.is_noncommittal_response(rg, utterance):
        ADD_NLU_FLAG('PERSONALISSUE_noncommittal')
    if personal_issues_helpers.is_short_response(rg, utterance):
        ADD_NLU_FLAG('PERSONALISSUE_short_response')

@nlu_processing
def get_background_flags(rg, utterance):
    return
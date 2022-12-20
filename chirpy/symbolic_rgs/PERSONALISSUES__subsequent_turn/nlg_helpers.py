from chirpy.response_generators.personal_issues import personal_issues_helpers 
from chirpy.response_generators.personal_issues import response_templates 
from chirpy.core.response_generator import nlg_helper
import logging
import random

logger = logging.getLogger('chirpylogger')


@nlg_helper 
def sample_subsequent_turn_statement(rg):
    template = response_templates.SubsequentTurnResponseTemplate()
    return template.sample()

@nlg_helper
def sample_partial_subsequent_turn_statement(rg):
    template = response_templates.PartialSubsequentTurnResponseTemplate()
    return template.sample()

@nlg_helper 
def sample_validation_statement(rg):
    template = response_templates.ValidationResponseTemplate()
    return template.sample()

@nlg_helper 
def sample_possible_continue_statement(rg):
    template = response_templates.PossibleContinueResponseTemplate()
    return template.sample()

@nlg_helper 
def sample_possible_continue_accepted_statement(rg):
    template = response_templates.PossibleContinueAcceptedResponseTemplate()
    return template.sample()

@nlg_helper 
def sample_ending_statement(rg):
    template = response_templates.EndingResponseTemplate()
    return template.sample()

@nlg_helper 
def response_contains_question(rg, response):
    return '?' in response
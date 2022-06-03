from chirpy.core.response_generator import nlg_helper
import random

BRIDGES = ["So, I was just thinking,", "I'd love to hear,", "Anyway, I was wondering,"]
ACKNOWLEDGEMENTS = ["Ok. Can do!", "Cool!", "Awesome!", "Great!", "Works for me!"]

@nlg_helper
def choose_random_bridge():
	return random.choice(BRIDGES)

@nlg_helper
def get_question_str(question):
	if question.statement is None:
		return question.question
	elif question.question is None:
		return question.statement
	else:
		return ' '.join((question.statement, question.question))

@nlg_helper
def best_acknow(rg):
	return rg.state_manager.current_state.choose_least_repetitive(ACKNOWLEDGEMENTS)


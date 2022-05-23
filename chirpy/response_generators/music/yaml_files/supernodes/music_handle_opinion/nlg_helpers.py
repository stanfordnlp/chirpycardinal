from chirpy.response_generators.music.response_templates import handle_opinion_template
from chirpy.core.response_generator import nlg_helper

@nlg_helper
def get_likes_music_response():
	return handle_opinion_template.HandleLikeMusicResponseTemplate().sample()
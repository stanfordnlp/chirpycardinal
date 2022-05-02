from chirpy.response_generators.music.response_templates import handle_opinion_template

def get_likes_music_response():
	return handle_opinion_template.HandleLikeMusicResponseTemplate().sample()
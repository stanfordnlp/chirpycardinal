from chirpy.core.response_generator.response_template import ResponseTemplateFormatter

chirpy_likes_music_comment = [
    "Music makes me feel alive. When I am listening to a piece of music that I love, I'm so overwhelmed by emotions.",
    'I think music demonstrates the best of humanity, it fills me with so much awe. I don\'t know what I would do without music.',
    "You know, I'm the kind of person who feels that life is incomplete without music.",
]

class HandleLikeMusicResponseTemplate(ResponseTemplateFormatter):
    slots = {
        "user_likes_music_comment": [
            "It's always nice to find another person who enjoys listening to music!",
            'You seem to love music a lot!',
        ],
        "chirpy_likes_music_comment": chirpy_likes_music_comment
    }

    templates = [
        "{user_likes_music_comment} {chirpy_likes_music_comment}"
    ]

class HandleLikeMusicPromptTemplate(ResponseTemplateFormatter):
    slots = {
        "user_likes_music_comment": [
            'By the way, it sounds like you really love music!',
            'By the way, you seem like a huge music fan!',
        ],
        "chirpy_likes_music_comment": chirpy_likes_music_comment
    }

    templates = [
        "{user_likes_music_comment} {chirpy_likes_music_comment}"
    ]
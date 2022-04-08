import random

def compliment_user_musician_choice():
    return [
        'You have really great taste in music!',
        'You sound like a real music buff!',
        'Your taste in music is awesome!',
    ]

def compliment_user_song_choice():
    return [
        'That\'s a great song I love it!',
        'I am so in love with that song too!',
        'Yes that seems like a really nice song!',
        'I\'m sure that sounds amazing!',
    ]

def til(til):
    return random.choice([
        f'I found out that {til}. Isn\'t that interesting?',
        f'I learned that {til}. What do you think about that?',
        f'Did you know that {til}?',
        f'I just found out the other day that {til}. Isn\'t that fascinating? What do you think?',
    ])

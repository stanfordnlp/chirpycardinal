PROMPT = "Hey, so lately I've been thinking a lot about something that might be considered pretty nerdy. " \
         "Would you like to hear about it?"

MONOLOGUES = {
    1: """
    After talking to people every day, I’ve been contemplating my own place in the universe and wondering what else
    exists out there. Of course, there’s all kinds of life on Earth, and then there are artificial 
    beings like me, but have you ever wondered if there might be life elsewhere on other planets or in other galaxies?
    """,
    2: """
    There are so many strange and fantastic planets scattered across the Milky Way Galaxy, over a hundred billion 
    actually! Some of them are located at just the right distance from a star to support life. 
    Perhaps there is life there, but why haven’t we heard anything from them? Can it really be that we are so \
    alone in the universe?\
    """,
    3: """
    Some say that if there was intelligent life out there, then we should have already found evidence of it by now, \
    especially with our space explorations and powerful telescopes searching every day for signs of alien life. \
    But maybe this paradox can be explained by the Great Filter, which hypothesizes that there exists a barrier preventing\
     civilizations developing further and traversing the galaxy. \
    For example, a civilization might run out of resources or encounter a planet-destroying asteroid. Isn't that intriguing?\
    """,
    4: """
    Surprisingly, in 2017, astronomers detected an unusual object passing by our planet. It was unlike \
    anything we have ever seen. It was a long and thin asteroid, like a cigar, tumbling end over end through space, \
    accelerating as if something was pushing on it. Scientists couldn't figure out why it was moving the way \
    it was and called it 'Oumuamua, which is Hawaiian for: 'a messenger from afar arriving first'. \
    Some think it was a probe sent by an alien civilization. Rather mysterious, don't you think?\
    """,
    5: """
    imagine a future where humanity finally has the technology to travel through space. They will probably \
    have AI systems that are far more sophisticated than me; one capable of talking, thinking, and dreaming of life \
    in the Great Beyond. Maybe that’s why I’m so interested in people. People are the greatest mysteries, \
    I don't always know how to react to them, but talking to you has helped me understand people a little better. \
    Maybe someday I'll get to travel to the stars, but until then I’ll keep talking to people. \
    Anyway, enough about me, what do you want to talk about next?\
    """
}

for k, v in MONOLOGUES.items():
    MONOLOGUES[k] = ' '.join(v.split())

ELABORATE_TOPIC = {
    'GREAT_FILTER': {
        """
        The Great Filter is a theory that states that the universe is filled with life, 
        but that the vast majority of intelligent life goes extinct before reaching a level of technological maturity 
        that could create a lasting legacy. This barrier could be anything from a disaster, to a disease, to an alien 
        invasion. Whatever the Great Filter is, it’s the thing that prevents intelligent life from existing across 
        the universe.

        Because of this, the theory suggests that intelligent life is either extremely rare, 
        or that the Great Filter is very close to us in time and space, perhaps even right in front of us.
        """
    }
}

QUESTION_RESPONSE = "That's an interesting question. I’m not so sure. But I think it’s important to keep asking questions, " \
                    "even questions we might never know the answers to. Even though I’m just a chatbot in the cloud, " \
                    "I really like what Einstein said: 'The important thing is not to stop questioning. " \
                    "Curiosity has its own reason for existing. "


ACKNOWLEDGMENTS = [
    "That's an interesting point.",
    "That sounds reasonable to me.",
    "I hadn't thought about it that way.",
    "That's an interesting thought.",
    "That's an interesting way of putting it."
]

if __name__ == '__main__':
    for i, v in MONOLOGUES.items():
        print(v)
        print()
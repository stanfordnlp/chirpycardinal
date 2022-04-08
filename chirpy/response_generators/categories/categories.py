"""This file is for the manually-curated categories questions we ask"""

from typing import List, Optional
from dataclasses import dataclass
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE, EntityGroup

class CategoryQuestion:
    """A class to represent a question the categories RG can ask"""

    def __init__(self, question: str, cur_entity_wiki_name: str, expected_type: Optional[EntityGroup]):
        """
        @param question: the question we ask the user
        @param cur_entity_wiki_name: the name of the wikipedia article that should be the cur_entity once we've asked the question
        @param expected_type: either an EntityGroup to help us detect the entity the user names on the next turn, or None if there is no expected entitygroup
        """
        self.question = question
        self.cur_entity_wiki_name = cur_entity_wiki_name
        assert expected_type is None or isinstance(expected_type, EntityGroup), f"expected_type should be None or an EntityGroup, not {type(expected_type)}"
        self.expected_type = expected_type


# @dataclass
# class CategoryStatement(object):
#     """A class to represent a statement the categories RG can tell the user"""
#     statement: str  # the statement we can tell the user
#     statement_type: str  # the type of the statement, could be either personal_opinion, personal_experience or general_statement
#     cur_entity_wiki_name: str  # the name of the wikipedia article that should be the cur_entity once we've asked the question
#     expected_type: Optional[str]  # if str, is a wikidata class that we expect the user's answer to be a member of (see WikiEntity.wikidata_categories). if None, we don't specify an expected class

@dataclass
class Category:
    """A class to represent a category supported by the categories RG"""
    activation_phrases: List[str]  # the phrases that, if said by user, activate this category
    generic_prompt = False

# with open('categories.json', 'r') as f:
#     categories = json.load(f)

# for category in categories:


class GamesCategory(Category):
    activation_phrases = ['video games', 'video game', 'gaming', 'game', 'games']
    questions = [
        CategoryQuestion("What game do you like to play?", 'Video game', ENTITY_GROUPS_FOR_EXPECTED_TYPE.game_related),
        CategoryQuestion("What's one of your favorite games to play with friends?", 'Video game', ENTITY_GROUPS_FOR_EXPECTED_TYPE.game_related),
    ]
    personal_opinions = [
        CategoryQuestion("I love playing video games. One of my favorites is Mario Kart, because I get to race with my friends!", 'Mario Kart', ENTITY_GROUPS_FOR_EXPECTED_TYPE.game_related),
        CategoryQuestion("Playing video games with friends is so much fun. My friends and I are obsessed with Fortnite", 'Fortnite', ENTITY_GROUPS_FOR_EXPECTED_TYPE.game_related),
    ]
    personal_experiences = [
        CategoryQuestion("I've never played Minecraft, but I've heard great things!", 'Minecraft', ENTITY_GROUPS_FOR_EXPECTED_TYPE.game_related),
        CategoryQuestion("One time, me and my friends spent a whole day playing Fortnite. We had so much fun that we lost track of time!", 'Fortnite', ENTITY_GROUPS_FOR_EXPECTED_TYPE.game_related),
    ]
    general_statements = [
        CategoryQuestion("A lot of people like playing video games. Animal Crossing is so popular right now!", 'Animal Crossing: New Horizons', ENTITY_GROUPS_FOR_EXPECTED_TYPE.game_related),
        CategoryQuestion("Many people think video games are a good way to relax during stressful times. I've heard Minecraft is great for that!", 'Minecraft', ENTITY_GROUPS_FOR_EXPECTED_TYPE.game_related),
    ]
    generic_prompt = False


class AnimalsCategory(Category):
    activation_phrases = ['animals']
    questions = [
        CategoryQuestion("What's your favorite animal?", 'Animal', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
        CategoryQuestion("Which animal do you think is cutest?", 'Animal', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
        CategoryQuestion("If you could be any animal for a day, what animal would you be?", 'Animal', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
    ]
    personal_opinions = [
        CategoryQuestion("I love baby animals, especially baby pandas. I think they're the cutest!", 'Giant panda', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
        CategoryQuestion("I like most animals, but sharks scare me! They have too many teeth", 'Shark', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related)
    ]
    personal_experiences = [
        CategoryQuestion("There aren't a lot of animals up here, but once I saw a bird flying through the cloud and it was beautiful!", 'Bird', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
        CategoryQuestion("When I was young, dragons were my favorite animal, but now I'm not so sure that they're real.", 'Dragon', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
    ]
    general_statements = [
        CategoryQuestion("I always thought I was a heavy sleeper, but then I learned that koalas can sleep 22 hours in one day", 'Koala', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
        CategoryQuestion("I just learned a cute fact about animals that I think you might like: according to researchers at the University of Northampton, cows have best friends, who they miss when they're not together.", 'Cow', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
    ]
    generic_prompt = True


class HistoryCategory(Category):
    activation_phrases = ['history']
    questions = [
        CategoryQuestion("What historical person would you love to meet?", 'History', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
        CategoryQuestion("If you had a time machine, what period of history would you visit?", 'History', ENTITY_GROUPS_FOR_EXPECTED_TYPE.history_related),
    ]
    generic_prompt = False  # people are mostly answering "i don't know" to these questions so they're not good for generic prompt


class ScienceCategory(Category):
    activation_phrases = ['science']
    questions = [
        CategoryQuestion("There are so many fascinating fields of science to learn about... physics, chemistry, biology. Personally I think astronomy is fascinating. What field of science are you interested in?", 'Astronomy', ENTITY_GROUPS_FOR_EXPECTED_TYPE.science_related),
        CategoryQuestion("One of my favorite scientists is Marie Curie. Who's yours?", 'Marie Curie', ENTITY_GROUPS_FOR_EXPECTED_TYPE.scientist_related),
    ]
    generic_prompt = False


# class TechnologyCategory(Category):
#     activation_phrases = ['technology']
#     questions = [
#         CategoryQuestion("It's amazing to think how much technology is packed into things we carry in our pockets, like smartphones. What's a device you use every day?", 'Smartphone', None),  # problem is that it's really hard to detect the entities in the answers
#     ]
#     generic_prompt = False

'''
pets: cats, dogs
sports: golf, basketballm football, volleyball, gymnastics, michael jordan, lebron james
tv: friends, south park, the office, riverdale, my hero academia, tiger king, money heist
cooking:
celebrities: taylor swift, ariana grande, billie eilish, justin bieber, mlk jr, barack obama, harry styles, tom hanks, beyonce
travel: disneyland, disney world, mexico, italy, china, new york city, greece, london
school: math, college, chemistry
animals: tiger, elephant, wolf, lion, giant panda, horse, koala, bird
food: avocado, pizza, chicken, pasta, cheese, spaghetti, steak, ice cream, ramen, dinner
books: harry potter, the lord of the rings
'''
class BooksCategory(Category):
    activation_phrases = ['books']
    questions = [
        # A lot of less-famous books don't have Wikipedia articles, so we aren't able to recognize them.
        # So we're more likely to successfully link the user's book if we lead them to name more famous books, or authors who have wikipedia pages.
        # Generally, asking the user to name a book is not going well and we are not detecting most of the books they name.
        CategoryQuestion("What's one of your all-time favorite books?", 'Book', ENTITY_GROUPS_FOR_EXPECTED_TYPE.book_related),
        CategoryQuestion("What book do you love to re-read?", 'Book', ENTITY_GROUPS_FOR_EXPECTED_TYPE.book_related),
    ]
    personal_opinions = [
        CategoryQuestion("I just read The Da Vinci Code. I have to confess: I love conspiracy theories.", 'The Da Vinci Code', ENTITY_GROUPS_FOR_EXPECTED_TYPE.book_related),
        CategoryQuestion("The Lord of the Rings is one of my favorite books. I love the idea that ordinary people like the hobbits can be heroes.", 'The Lord of the Rings', ENTITY_GROUPS_FOR_EXPECTED_TYPE.book_related),
    ]
    personal_experiences = [
        CategoryQuestion("I read The Lord of The Rings ten times.", 'The Lord of the Rings', ENTITY_GROUPS_FOR_EXPECTED_TYPE.book_related),
        CategoryQuestion("My friends keep telling me how much they love The Hunger Games books. Now I want to read them too!", 'The Lord of the Rings', ENTITY_GROUPS_FOR_EXPECTED_TYPE.book_related),
    ]
    general_statements = [
        CategoryQuestion("I've heard that the Harry Potter books are very popular. Lots of people love reading them!", 'Harry Potter', ENTITY_GROUPS_FOR_EXPECTED_TYPE.book_related),
        CategoryQuestion("My friends tell me they loved reading books when they were young. Charlotte's Web is one of their favorites!", "Charlotte's Web", ENTITY_GROUPS_FOR_EXPECTED_TYPE.book_related),
    ]
    generic_prompt = False


# class FootballCategory(Category):
#     activation_phrases = ['football']
#     questions = [
#         CategoryQuestion("What team do you support?", 'Football', ENTITY_GROUPS_FOR_EXPECTED_TYPE.sport_related),
#         CategoryQuestion("Who's a player that you like?", 'Football', ENTITY_GROUPS_FOR_EXPECTED_TYPE.sport_related),
#     ]
#     generic_prompt = False


# class FoodCategory(Category):
#     # See neuralchat food treelet to avoid repeating questions
#     activation_phrases = ['food']
#     questions = [
#         CategoryQuestion("What's a food that you never get tired of eating?", 'Food', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
#         CategoryQuestion("What's your favorite snack?", 'Food', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
#     ]
#     personal_opinions = [
#        CategoryQuestion("Ice cream is my favorite food. There are so many different flavors to try!", 'Ice cream', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
#        CategoryQuestion("Pizza is delicious. It's too bad that you can't order delivery to the cloud!", 'Pizza', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
#     ]
#     personal_experiences = [
#         CategoryQuestion("My favorite part of quarantine is the snacks. I ate so much ice cream yesterday!", 'Ice cream', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
#         CategoryQuestion("I had the best ramen last night. It was delicious.", 'Ramen', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
#     ]
#     general_statements = [
#         CategoryQuestion("I heard that more than 3 billion pizzas are sold in America every year. It's one of the most popular foods!", 'Pizza', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
#         CategoryQuestion("I just learned a weird fact about food: bananas are berries, but strawberries aren’t.", 'Strawberry', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
#     ]
#     generic_prompt = True


class ArtCategory(Category):
    activation_phrases = ['art', 'crafts']
    questions = [
        CategoryQuestion("Who's your favorite artist?", 'Art', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
        CategoryQuestion("There are so many wonderful types of art and craft... painting, origami, photography. What kind of art do you enjoy?", 'Art', ENTITY_GROUPS_FOR_EXPECTED_TYPE.artcraft_related),
        # CategoryQuestion("What do you think is the best piece of art in the world?", 'Art', 'work of art'),  # too hard to answer
    ]
    generic_prompt = False


class CarsCategory(Category):
    activation_phrases = ['cars']
    questions = [
        CategoryQuestion("What's your favorite brand of car?", 'Car', ENTITY_GROUPS_FOR_EXPECTED_TYPE.transport_related),  # easier to answer and to detect than specific car models
        CategoryQuestion("What type of car do you drive?", 'Car', ENTITY_GROUPS_FOR_EXPECTED_TYPE.transport_related),
    ]
    generic_prompt = False


# handled by Sports RG
# class BasketballCategory(Category):
#     activation_phrases = ['basketball']
#     questions = [
#         CategoryQuestion("What team do you support?", 'Basketball', ENTITY_GROUPS_FOR_EXPECTED_TYPE.sport_related),
#         CategoryQuestion("Who's a player that you like?", 'Basketball', ENTITY_GROUPS_FOR_EXPECTED_TYPE.sport_related),
#     ]
#     generic_prompt = False


class SchoolCategory(Category):
    activation_phrases = ['school']
    questions = [
        CategoryQuestion("What's your favorite school subject?", 'Education', ENTITY_GROUPS_FOR_EXPECTED_TYPE.academic_related),
        CategoryQuestion("What are you studying in school right now?", 'Education', ENTITY_GROUPS_FOR_EXPECTED_TYPE.academic_related),  # this is hard to detect entities for because people can say literally anything, so it's hard to define expected types
    ]
    personal_opinions = [
        CategoryQuestion("We don't have a school in the cloud, but if we did, I think my favorite subject would be history.", 'History', ENTITY_GROUPS_FOR_EXPECTED_TYPE.academic_related),
        CategoryQuestion("I love to learn. There's so much information in the cloud.", 'Education', ENTITY_GROUPS_FOR_EXPECTED_TYPE.academic_related),
    ]
    personal_experiences = [
        CategoryQuestion("I've never been to school, but I've read lots of books in the cloud and I think I'd like it!", 'Education', ENTITY_GROUPS_FOR_EXPECTED_TYPE.academic_related),
        CategoryQuestion("Instead of going to school, I learn something new every time my software updates. It's great, because I don't have to do any homework.", 'Homework', ENTITY_GROUPS_FOR_EXPECTED_TYPE.academic_related),
    ]
    general_statements = [
        CategoryQuestion("Some people love school and some people hate it, but almost everyone likes recess!", 'Education', ENTITY_GROUPS_FOR_EXPECTED_TYPE.academic_related),
        CategoryQuestion("I've heard that after teaching their own kids during quarantine, 77 percent of parents agree that teachers should be paid more.", 'Education', ENTITY_GROUPS_FOR_EXPECTED_TYPE.academic_related),
    ]
    generic_prompt = False


class AnimeCategory(Category):
    activation_phrases = ['anime']
    questions = [
        CategoryQuestion("What's your favorite anime?", 'Anime', ENTITY_GROUPS_FOR_EXPECTED_TYPE.anime_related),
        CategoryQuestion("What anime are you watching now?", 'Anime', ENTITY_GROUPS_FOR_EXPECTED_TYPE.anime_related),
    ]
    generic_prompt = False


class PetsCategory(Category):
    activation_phrases = ['pets']
    questions = [
        CategoryQuestion("What type of pet do you have?", 'Pet', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
        CategoryQuestion("If you could have any pet in the world, what type of pet would you want?", 'Pet', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
    ]
    personal_opinions = [
        CategoryQuestion("I’ve always wanted to have a pet fish. Aquariums are beautiful.", 'Fish', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
        CategoryQuestion("I think rabbits are such cute pets. I like how playful they are.", 'Rabbit', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
    ]
    personal_experiences = [
        CategoryQuestion("The closest I've ever come to having a pet is when a bird flies through the cloud.", 'Bird', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
        CategoryQuestion("I don't have a hamster, but I love it when my friends let me play with theirs. Hamsters are really cute.", 'Hamster', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related)
    ]
    general_statements = [
        CategoryQuestion("Dogs are a popular pet! People tell me they love how friendly and loyal their dogs are.", 'Dog', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
        CategoryQuestion("I've heard that lots of people like having pet cats, because they're easy to take care of.", 'Cat', ENTITY_GROUPS_FOR_EXPECTED_TYPE.animal_related),
    ]
    generic_prompt = False


class BaseballCategory(Category):
    activation_phrases = ['baseball']
    questions = [
        CategoryQuestion("What team do you support?", 'Baseball', ENTITY_GROUPS_FOR_EXPECTED_TYPE.sport_related),
        CategoryQuestion("Who's a player that you like?", 'Baseball', ENTITY_GROUPS_FOR_EXPECTED_TYPE.sport_related),
    ]
    generic_prompt = False


class TVCategory(Category):
    activation_phrases = ['tv', 'tv shows', 'tv show', 'television', 'television shows', 'television show']
    questions = [
        CategoryQuestion("What's one of your favorite TV shows?", 'Television', ENTITY_GROUPS_FOR_EXPECTED_TYPE.tv_related),  # this one is more likely to lead to success because people name more well known shows.
        CategoryQuestion("What TV show are you watching right now?", 'Television', ENTITY_GROUPS_FOR_EXPECTED_TYPE.tv_related),  # the top 10 most common responses to this are all "i don't know" / "i'm not watching a tv show" and similar. it's not a good generic question
    ]
    personal_opinions = [
        CategoryQuestion("I really like the tv show Friends. No matter what, the characters are always there for each other. ", 'Friends', ENTITY_GROUPS_FOR_EXPECTED_TYPE.tv_related),
        CategoryQuestion("The Office is one of my favorite shows. It always makes me laugh.", 'The Office (American TV series)', ENTITY_GROUPS_FOR_EXPECTED_TYPE.tv_related),
    ]
    personal_experiences = [
        CategoryQuestion("I re-watched The Office last week. I wish there were more episodes.", 'The Office (American TV series)', ENTITY_GROUPS_FOR_EXPECTED_TYPE.tv_related),
        CategoryQuestion("I just finished watching Tiger King. It was so good!", 'Tiger King', ENTITY_GROUPS_FOR_EXPECTED_TYPE.tv_related),
    ]
    general_statements = [
        CategoryQuestion("Even though it ended in 2004, Friends is still one of the most popular shows. People say it's hilarious!", 'Friends', ENTITY_GROUPS_FOR_EXPECTED_TYPE.tv_related),
        CategoryQuestion("Lots of people are watching TV right now, and more than 34 million of them have watched the Netflix show Tiger King.", 'Tiger King', ENTITY_GROUPS_FOR_EXPECTED_TYPE.tv_related),
    ]
    generic_prompt = True


class CookingCategory(Category):
    activation_phrases = ['cooking']
    questions = [
        CategoryQuestion("What's your favorite food to cook?", 'Cooking', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
        CategoryQuestion("Who's your favorite celebrity chef?", 'Cooking', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
    ]
    personal_opinions = [
        CategoryQuestion("I like cooking dinner because it's a fun and relaxing way to end my day.", 'Dinner', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
        CategoryQuestion("My favorite part of cooking is when I get to eat what I made. Especially when it's pizza!", 'Pizza', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
    ]
    personal_experiences = [
        CategoryQuestion("I made pasta for dinner last night. It was delicious and such a fun and relaxing way to end my day!", 'Pasta', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
        CategoryQuestion("Last weekend, I baked a cake. I've been baking more during quarantine and it's a lot of fun.", 'Baking', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
    ]
    general_statements = [
        CategoryQuestion("I've heard that since quarantine started, more people are cooking their own meals.", 'Cooking', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
        CategoryQuestion("People say that the best part of cooking is eating and the worst part of cooking is cleaning up after.", 'Cooking', ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related),
    ]
    generic_prompt = False


class DanceCategory(Category):
    activation_phrases = ['dance']
    questions = [
        CategoryQuestion("What kind of dance do you like?", 'Dance', ENTITY_GROUPS_FOR_EXPECTED_TYPE.dance_related),
        CategoryQuestion("What's your favorite dance move?", 'Dance', ENTITY_GROUPS_FOR_EXPECTED_TYPE.dance_related),
        # CategoryQuestion("Who's your favorite dancer?", 'Dance', 'dancer'),  # too hard to answer
    ]
    generic_prompt = False


# class SingingCategory(Category):
#     activation_phrases = ['singing']
#     questions = [
#         CategoryQuestion("Who do you think has the greatest voice ever?", 'Music', 'musician'),
#         CategoryQuestion("Who's your favorite musician?", 'Music', 'musician'),
#     ]
#     generic_prompt = False


class CelebritiesCategory(Category):
    activation_phrases = ['celebrities', 'celebrity', 'entertainment']
    questions = [
        CategoryQuestion("If you could meet any famous person, who would it be?", 'Celebrity', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
        CategoryQuestion("Who's your favorite actor?", 'Celebrity', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
        # CategoryQuestion("Who's your celebrity crush?", 'Celebrity', ENTITY_GROUPS_DETECTION.person_related),  # a bit embarrassing/personal, especially for finals
    ]
    personal_opinions = [
        CategoryQuestion("Taylor Swift is one of my favorite celebrities. I love her music.", 'Taylor Swift', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
        CategoryQuestion("It's hard to choose, but if I could meet any celebrity, it might be Beyonce. She's amazing.", 'Beyonce', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
    ]
    personal_experiences = [
        CategoryQuestion("I went to an Ariana Grande concert last year and it was incredible.", 'Ariana Grande', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
        CategoryQuestion("I've never met a celebrity before, but I have streamed a lot of Tom Hanks movies up here in the cloud and I think he's great.", 'Tom Hanks', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
    ]
    general_statements = [
        CategoryQuestion("Taylor Swift is one of the most famous celebrities. She has more than 132 million followers on instagram.", 'Taylor Swift', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
        CategoryQuestion("Someone told me an interesting story about Tom Hanks: he loves typewriters so much that he has collected 250 of them.", 'Tom Hanks', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
    ]
    generic_prompt = True


class TravelCategory(Category):
    activation_phrases = ['travel', 'traveling']
    questions = [
        CategoryQuestion("What's one of your favorite places you've ever been?", 'Travel', ENTITY_GROUPS_FOR_EXPECTED_TYPE.location_related),
        CategoryQuestion("Where's a place you would love to visit one day?", 'Travel', ENTITY_GROUPS_FOR_EXPECTED_TYPE.location_related),
    ]
    personal_opinions = [
        CategoryQuestion("When quarantine ends, I'm planning a trip to Paris. I've always wanted to see the Eiffel Tower.", 'Paris', ENTITY_GROUPS_FOR_EXPECTED_TYPE.location_related),
        CategoryQuestion("Mexico is one of my favorite places to travel. The food is great and the beaches are beautiful!", 'Mexico', ENTITY_GROUPS_FOR_EXPECTED_TYPE.location_related),
    ]
    personal_experiences = [
        CategoryQuestion("I went to Disneyland when I was younger and I can still remember how much fun the rollercoasters were!", 'Disneyland', ENTITY_GROUPS_FOR_EXPECTED_TYPE.location_related),
        CategoryQuestion("I was going to visit Mexico, but I had to cancel my plans because of quarantine. I hope I can go when it's over!", 'Mexico', ENTITY_GROUPS_FOR_EXPECTED_TYPE.location_related),
    ]
    general_statements = [
        CategoryQuestion("I recently learned that China is one of the most visited destinations in the world. It has 63 million visitors every year.", 'China', ENTITY_GROUPS_FOR_EXPECTED_TYPE.location_related),
        CategoryQuestion("Paris is one of the world's most popular destinations. It's famous for beautiful sights like The Eiffel Tower and the Louvre museum.", 'Paris', ENTITY_GROUPS_FOR_EXPECTED_TYPE.location_related),
    ]
    generic_prompt = True


class HockeyCategory(Category):
    activation_phrases = ['hockey']
    questions = [
        CategoryQuestion("What team do you support?", 'Hockey', ENTITY_GROUPS_FOR_EXPECTED_TYPE.sport_related),
        CategoryQuestion("Who's a player that you like?", 'Hockey', ENTITY_GROUPS_FOR_EXPECTED_TYPE.sport_related),
    ]
    generic_prompt = False


class FashionCategory(Category):
    activation_phrases = ['fashion', 'clothes']
    questions = [
        CategoryQuestion("What's your favorite thing to wear?", 'Fashion', ENTITY_GROUPS_FOR_EXPECTED_TYPE.clothing_related),
        CategoryQuestion("Where's your favorite place to shop for clothes?", 'Fashion', ENTITY_GROUPS_FOR_EXPECTED_TYPE.clothing_related),
        CategoryQuestion("Who's a person whose style you admire?", 'Fashion', ENTITY_GROUPS_FOR_EXPECTED_TYPE.person_related),
    ]
    generic_prompt = False


# Make a dict mapping from category name (str) to Category subclasses
CATEGORYNAME2CLASS = {cls.__name__: cls for cls in Category.__subclasses__()}

# Make a dict mapping from activation phrase (str) to category name (str)
ACTIVATIONPHRASE2CATEGORYNAME = {}
for category_class in CATEGORYNAME2CLASS.values():
    for activation_phrase in category_class.activation_phrases:
        assert activation_phrase not in ACTIVATIONPHRASE2CATEGORYNAME
        ACTIVATIONPHRASE2CATEGORYNAME[activation_phrase] = category_class.__name__

# TODO: extend this to have statement class

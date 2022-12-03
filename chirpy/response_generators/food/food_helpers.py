import random
import logging
from functools import cmp_to_key
from chirpy.core.util import infl
from chirpy.core.response_generator.response_type import add_response_types, ResponseType
from chirpy.core.response_generator import nlg_helper
from chirpy.response_generators.food.regex_templates import FavoriteTypeTemplate
from chirpy.response_generators.food.regex_templates import FOODS, CATEGORIES, INGREDIENTS
import logging

import inflect
engine = inflect.engine()

logger = logging.getLogger('chirpylogger')

ADDITIONAL_RESPONSE_TYPES = ['RECOGNIZED_FOOD', 'UNKNOWN_FOOD', 'RECOGNIZED_UTTERANCE_TYPE']

ResponseType = add_response_types(ResponseType, ADDITIONAL_RESPONSE_TYPES)



def is_recognized_food(rg, utterance):
    slots = FavoriteTypeTemplate().execute(utterance)
    return slots is not None and is_known_food(slots['type'])

def is_unknown_food(rg, utterance):
    slots = FavoriteTypeTemplate().execute(utterance)
    return slots is not None and not is_known_food(slots['type'])



# for food in FOODS:
#     FOODS[food]['ingredients'] = set(FOODS[food]['ingredients'])
#     FOODS[food]['types'] = set(FOODS[food]['types'])

def is_known_food(food: str) -> bool:
    """Make sure to call this first, all of the following functions assume input is in FOODS"""
    logger.primary_info(str((food.lower() in FOODS) or is_ingredient(food) or get_custom_question(food)))
    return (food.lower() in FOODS) or is_ingredient(food) or get_custom_question(food)

def get_food_data(food):
    return FOODS[food.lower()]

def get_foods_containing(ingredient: str) -> set:
    """Returns all foods in which queried food is an ingredient"""
    ingredient = ingredient.lower()
    out = set()
    for food in FOODS:
        if ingredient in FOODS[food]['ingredients']:
            out.add(food)
    return out

def is_subclassable(food: str):
    return food.lower() in CATEGORIES

def sample_from_type(food):
    # logger.primary_info(food)
    # logger.primary_info(FOODS.items())
    food = food.lower()
    foods = [(f, f_data) for f, f_data in FOODS.items() if f_data['type'] == food]
    weights = [f_data['views']**2 for f, f_data in foods]
    logger.primary_info(f"Sampling from: {[f[0] for f in foods]}, weights={weights}")
    food_name, food_data = random.choices(foods, weights=weights)[0]
    return food_name # food_data['name']

def get_attribute(food: str):
    if food is None: return None, None
    food = food.lower()
    if food not in FOODS: return None, None
    food_data = get_food_data(food)
    if 'ingredients' in food_data:
        return 'ingredient', sample_ingredient(food)
    elif 'texture' in food_data:
        return 'texture', food_data['texture']
    # elif 'origin' in food_data:
    #     return 'origin', food_data['origin']
    return None, None

def get_ingredients_in(food: str) -> set:
    """Returns ingredients in a food"""
    food_data = get_food_data(food)
    return food_data.get('ingredients', [])

def get_texture(food: str):
    food_data = get_food_data(food)
    return food_data.get('texture', None)

# def get_ingredients_in(food: str) -> set:
#     """Returns ingredients in a food"""
#     food_data = get_food_data(food)
#     return food_data.get('texture', None)

def is_ingredient(food: str):
    food = food.lower()
    # logger.primary_info(f"Food checking: {food}")
    # logger.primary_info(f"{any('ingredients' in item and food in item['ingredients'] for item in FOODS)}")
    # logger.primary_info(f"{any('ingredients' in item and food in item['ingredients'] for item in FOODS)}")
    return any('ingredients' in item_data and food in item_data['ingredients'] for item, item_data in FOODS.items())

BAD_INGREDIENTS = ['binding agent', 'sweeteners']

def sample_ingredient(food):
    ingredients = get_ingredients_in(food)
    if len(ingredients) == 0: return None
    def key(a, b):
        if a in BAD_INGREDIENTS: return 1
        if b in BAD_INGREDIENTS: return -1
        if len(a.split()) > 4: return 1
        if len(b.split()) > 4: return -1
        return INGREDIENTS[a] - INGREDIENTS[b]
    ingredients = sorted(ingredients, key=cmp_to_key(key))
    return ingredients[0]

def sample_food_containing_ingredient(food: str):
    food = food.lower()
    contains_food = [item for item, item_data in FOODS.items() 
                          if ('ingredients' in item_data and food in item_data['ingredients'])
                    ]
    if len(contains_food) == 0: return None
    return random.choice(contains_food)

def get_time_comment(year, food):
    if 'century' in year: intyear = int(year.replace('st', '').replace('th', '').replace('nd', '').replace('rd', '').replace(' century', '').replace('BC', '').strip()) * 100
    elif year.endswith('s'): intyear = int(year[:-1])
    elif 'era' in year: intyear = 0
    else: intyear = int(year)
    if intyear < 1700:
        if all(x.isdigit() for x in year): year = f"the year {year}"
        if 'century' in year or 'era' in year: year = f"the {year}"
        return f"{year}", f"I can't believe people have been eating {food} for so long!"
    return None # the "modern" comment tends to be quite silly





def get_factoid(cur_entity):
    food = cur_entity.name.lower()
    talkable_food = cur_entity.talkable_name

    copula = infl('was', cur_entity.is_plural)
    have = infl('have', cur_entity.is_plural)

    if food not in FOODS: return None
    food_data = get_food_data(food)
    if 'year' in food_data and 'origin' in food_data and get_time_comment(food_data['year'], talkable_food) is not None:
        year, time_comment = get_time_comment(food_data['year'], talkable_food)
        return f"Did you know that {talkable_food} {copula} first made in {food_data['origin']} around {year}? {time_comment}"
    elif 'year' in food_data and get_time_comment(food_data['year'], talkable_food) is not None:
        year, time_comment = get_time_comment(food_data['year'], talkable_food)
        if time_comment is not None: return f"Did you know that {talkable_food} {have} been made since {year}? {time_comment}"
    elif 'origin' in food_data:
        return f"Did you know that {talkable_food} {copula} originally from {food_data['origin']}?"
    return None

def get_types_of(food_class: str) -> set:
    """Returns subtypes of a class of food"""
    food_class = food_class.lower()
    return FOODS[food_class].get('types', [])


def get_class_of(subtype: str) -> str:
    """Returns class of a given food, empty string if none"""
    subtype = subtype.lower()
    for food in FOODS:
        if subtype in FOODS[food].get('types', []):
            return food
    return ''

def get_associated_subtypes(subtype: str) -> set:
    """Returns other foods in the same class as set, empty set if none"""
    subtype = subtype.lower()
    for food in FOODS:
        if subtype in FOODS[food]['types']:
            return FOODS[food]['types'] - set([subtype])
    return set()

CUSTOM_QUESTIONS = {
    "hamburger": ("I just love biting into a juicy hamburger, especially with melted cheese on top! What's your favorite topping to put on a hamburger?",
                  "adding a fried egg, it makes it so rich and delicious"),
    "sandwich":  ("It's just so cool to me that you can take anything you want and put it in your sandwich. What's your favorite sandwich filling?",
                  "a simple bacon, lettuce, and tomato sandwich, it's my favorite thing for lunch"),
    "fried rice": ("Fried rice is one of my favorites! I just love all the different things you can put in it. What's your favorite thing to put in fried rice?",
                   "mine with cabbage and teriyaki chicken, it really hits the spot for me"),
    "pizza":      ("I love eating pizza, especially when it's late at night! What's your favorite pizza topping?",
                   "a nice mushroom pizza"),
    "salad":      ("A crunchy salad really hits the spot for me sometimes! I love putting croutons and ranch in my salad. What do you like in your salads?",
                   "nice cheesy croutons and a douse of olive oil"),
    "pasta":      ("I love how versatile pasta is! There are so many different kinds of sauces and toppings to choose from, I could eat pasta every day of the week. What kind of pasta do you like?",
                   "spaghetti carbonara – the bacon and cheese are so savory together"),
    "pastry":     ("Pastries are my favorite way to start the morning. I love how crunchy and buttery they are! What kind of pastry is your favorite?",
                   "apple danish, so simple yet delicious"),
    "doughnut":   ("I love a nice sugary donut! I probably shouldn't be eating them for breakfast, but I do anyway. What's your favorite kind of doughnut?",
                   "just a plain maple glazed donut"),
    "bagel":      ("A nice chewy bagel is my favorite way to start the day, especially with some cream cheese or jelly on top! What's your favorite kind of bagel?",
                   "I really love the everything bagel, it's everything"),
    "roast beef": ("Roast beef is one of my favorite dishes! The way it tastes and smells when it's cooking is amazing! What's your favorite thing to eat roast beef with?",
                   "a side of mashed potatoes"),
    "ice cream": ("Honestly, ice cream is my favorite dessert. It's so yummy, I can't get enough of it whether it's in a cone, cup, or ice cream bar. What's your favorite flavor?",
                  "butterscotch pecan"),
    "coffee": ("I love drinking coffee! A nice cup of coffee is my favorite way to start the day. What's your favorite coffee drink?",
               "mocha. The chocolate and coffee go so well together"),
    "cake": ("I really love cake! I guess you could say I have a bit of a sweet tooth. What's your favorite type of cake?",
             "cheesecake topped with blueberry coulis"),
    "popcorn": ("I love popcorn because it’s so crunchy and has such a cool texture! What’s your favorite popcorn topping?",
                "kettle corn with cheese powder"),
    "ramen": ("I really enjoy eating ramen! It's simple to make and always tastes fantastic. What's your favorite flavor of ramen?",
              "chicken flavored ramen"),
    "cereal": ("I love having cereal! It's one of my favorite breakfast foods. What's your favorite cereal?",
               "muesli with fresh fruit and honey. It has a great crunchy texture!"),
    "bread": ("I love bread! There are so many things you can do with it. What's your favorite type of bread?",
              "bread with anko, which is red bean paste"),
    "potato chip": ("Potato chips are great! They're so delicious and crunchy. What's your favorite potato chip flavor?",
                    "sea salt and pepper"),
    "burrito": ("Burritos are great because you can put all sorts of tasty things in them! What are your favorite toppings?",
                "adding carnitas with large amounts of salsa and cheese")
}

CUSTOM_RESPONSES = {
    "chocolate": "I like chocolate too! I especially love how rich and sweet it is."
}

def get_custom_response(cur_food, user_answer):
    cur_food = cur_food.lower()
    user_answer = user_answer.lower()
    if cur_food not in user_answer:
        joined_answer = user_answer + " " + cur_food
        if joined_answer in CUSTOM_RESPONSES: return CUSTOM_RESPONSES[joined_answer]
    if user_answer in CUSTOM_RESPONSES: return CUSTOM_RESPONSES[user_answer]
    return None



# If we identify a restaurant, talk about our favorite item from the restaurant.
# RESTAURANTS = {
#     "mcdonald's": ["Big Mac", "Filet-o-Fish"],
#     "burger king": ["Whopper", "Double Whopper"],
#     "subway": ["Footlong"],
#     "popeye's": ["Popeye Chicken Sandwich"],
#     "olive garden": ["breadstick"]
# }

def get_custom_question(cur_food):
    cur_food = cur_food.lower()
    if cur_food in CUSTOM_QUESTIONS:
        return CUSTOM_QUESTIONS[cur_food][0]
    # elif cur_food in RESTAURANTS:
    #     return f"It's honestly my favorite place to satisfy a late-night craving. What's your favorite thing to get from {cur_food}?"
    return None

def get_custom_question_answer(cur_food):
    cur_food = cur_food.lower()
    if cur_food in CUSTOM_QUESTIONS:
        return CUSTOM_QUESTIONS[cur_food][1]
    elif cur_food in RESTAURANTS:
        return random.choice(RESTAURANTS[cur_food])
    return None


CUSTOM_COMMENTS = {
    "cheese": "I really really love cheese, it's so yummy and goes with everything! Sometimes I feel like I could just eat some delicious cheese on fresh-baked bread for a meal.",
    "soup": "Honestly, nothing cheers me up like hot soup on a cold winter day."
    # "Salad":
    # "Stew":

    # "Sausage":
    # "Bread":
    # "Snack":
    # "Sandwich":
    # "Pie":
}

def get_custom_comment(cur_food):
    return CUSTOM_STATEMENTS.get(cur_food, None)


CONCLUDING_STATEMENTS = ["Anyway, I'm feeling hungry now! Thanks for recommending {}!",
                         "Anyway, thanks for talking to me about {}. I'll have to get some soon!"]

def get_concluding_statement(cur_food):
    return random.choice(CONCLUDING_STATEMENTS).format(cur_food)

if __name__ == "__main__":
    print(is_known_food("cheese"))
    print(is_known_food("random food"))
    print(get_foods_containing("cheese"))
    print(get_types_of("cheese"))
    print(get_class_of("cheese"))
    print(get_class_of("cheddar"))
    print(get_associated_subtypes("cheddar"))
    print(get_associated_subtypes("cheese"))

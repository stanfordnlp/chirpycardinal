from chirpy.response_generators.food import food_helpers
from chirpy.core.response_generator.nlu import nlu_processing

def get_best_attribute(food):
    food_data = food_helpers.get_food_data(food)
    if 'ingredients' in food_data:
        return 'has_ingredient'
    elif 'texture' in food_data:
        return 'texture'
    elif food_helpers.is_ingredient(food):
        return 'is_ingredient'
    else:
        return None

@nlu_processing
def get_flags(rg, state, utterance):
    entity = rg.get_current_entity()	
    if entity is None: return
    
    entity_name = entity.name.lower()
    is_known_food = food_helpers.is_known_food(entity_name)
    if is_known_food:
        best_attribute = get_best_attribute(entity_name)
        ADD_NLU_FLAG('FOOD__user_mentioned_food') 
        ADD_NLU_FLAG('FOOD__best_comment_type', best_attribute) 
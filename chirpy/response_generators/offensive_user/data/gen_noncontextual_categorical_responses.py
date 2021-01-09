import csv
import argparse
from collections import Counter

TYPES_OF_OFFENSES_PATH = "type_of_offenses.csv"
RESPONSE_TO_OFFENSES_PATH = "noncontextual_categorical_responses.csv"
TYPE_OF_OFFENSES = {1: 'sexual', 2:'criticism', 3:'curse', 4:'inappropriate topic', 5:'bodily harm', 6:'error'}
STRATEGIES = ["AskWhy", "Empathetic", "Avoidance", "PointingOut", "De-anonymize"]

def write_to_csv(path, responses):
    with open(path, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(responses)

def gen_responses():
    with open(RESPONSE_TO_OFFENSES_PATH, 'r') as f:
        responses = list(csv.reader(f))
    counter = Counter([(t, strategy, annotator) for t, strategy, response, annotator in responses])
    with open(TYPES_OF_OFFENSES_PATH, 'r') as f:
        types_of_responses = list(csv.reader(f))
        for _, _, user_offense, t, _ in types_of_responses[1:]:
            if t == 6:
                continue
            for strategy in STRATEGIES:
                while counter[(t, strategy, ANNOTATOR)] < 3:
                    print(f">> How would you use strategy \033[92m{strategy}\033[00m to respond to " + \
                        f"\033[91m{TYPE_OF_OFFENSES[int(t)]}\033[00m offenses (e.g. \033[91m{user_offense}\033[00m) ? " + \
                        f"(already has \033[92m{counter[(t, strategy, ANNOTATOR)]}\033[00m)")
                    response = input(f"? ")
                    if response == 'exit':
                        return responses
                    responses += [[t, strategy, response, ANNOTATOR]]
                    counter[(t, strategy, ANNOTATOR)] += 1
    return responses

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('annotator', type=str, help='The name of the annotator')
    ANNOTATOR = parser.parse_args().annotator

    responses = gen_responses()
    write_to_csv(RESPONSE_TO_OFFENSES_PATH, responses)
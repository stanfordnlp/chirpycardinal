import logging
import random

logger = logging.getLogger('chirpylogger')

"""
This file contains the Experiments class and the probability for different experiments
"""

EXPERIMENT_NOT_FOUND = "not_defined"

EXPERIMENT_PROBABILITIES = {
    "fallback": {
        "open_question": 0.5,
        "no_question": 0.5
    },
    "statement_type": {
        "personal_opinion": 0.4,
        "personal_experience": 0.3,
        "general_statement": 0.3
    },
    "category_style": {
        "question": 0.25,
        "statement": 0.25,
        "question_and_statement": 0.5
    },
    "convpara_til": {
        True: 1,
        False: 0,
    },
    "convpara_top_p": {
        0.7: 0.5,
        0.75: 0.5
    },
    "convpara": {
        True: 1,
        # False: 0.5
    },
    "opinion_policy" : {
        "random" : 1.0
    },
    "gpt2ed_ranking_policy": {
        # "score_only": 0.34, # conditioned on being in the experimental path
        # "nli_score": 0.33,
        # "rule_based": 0.33
        "score_only": 0.4, # conditioned on being in the experimental path
        "senti_score": 0.2,
        "rule_based": 0.4
    },
    "wikirg_policy": {
        "original": 0,
        "infiller": 1
    },
    "convpara_selection_strategy": {
        "max-pmi": 0.5,
        "fused-pcmi": 0.5
    }
}

class Experiments:

    def __init__(self):
        self.experiments = {}
        self.experiments_aux_data = {}

    def look_up_experiment_value(self, experiment_name):
        """
        Look up the value that experiment_name variable takes in the state.
        If it is not set in the state, sample a value and store the value in the state.
        :param experiment_name: name of experiment
        :return: the value of the experiment variable
        """
        if experiment_name not in self.experiments:
            self.sample_experiment_value(experiment_name)
        return self.experiments[experiment_name]

    def sample_experiment_value(self, experiment_name: str) -> str:
        """
        Sample the value of the experiment_name variable according to the probabilities in EXPERIMENT_PROBABILITIES
        and store it in the current state.
        Return EXPERIMENT_NOT_FOUND if experiment_name is not defined in EXPERIMENT_PROBABILITIES
        :return: the value of the experiment variable
        """
        value = EXPERIMENT_NOT_FOUND
        if experiment_name not in EXPERIMENT_PROBABILITIES.keys():
            logger.error(f"{experiment_name} is not defined in EXPERIMENT_PROBABILITIES, returning {value}")
        else:
            value = random.choices(list(EXPERIMENT_PROBABILITIES[experiment_name].keys()),
                                   list(EXPERIMENT_PROBABILITIES[experiment_name].values()))[0]
            logger.primary_info(f"Set {experiment_name} to be {value}")
        self.experiments[experiment_name] = value
        return value

    def override_experiment_value(self, experiment_name:str, override_value):
        """
        override the value of the experiment_name variable with the given value
        and store it in the current state.
        Return EXPERIMENT_NOT_FOUND if experiment_name is not defined in EXPERIMENT_PROBABILITIES
        :return: the value of the experiment variable
        """
        value = EXPERIMENT_NOT_FOUND
        if experiment_name not in EXPERIMENT_PROBABILITIES.keys():
            logger.error(f"{experiment_name} is not defined in EXPERIMENT_PROBABILITIES, returning {value}")
        else:
            value = override_value
            logger.primary_info(f"Overriding {experiment_name} to be {value}")
        self.experiments[experiment_name] = value
        return value

    def __repr__(self):
        return "Experiments<" + ", ".join(f"{key}={value}" for key, value in self.experiments.items()) + ">"

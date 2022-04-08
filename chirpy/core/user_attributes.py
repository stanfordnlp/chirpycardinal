from dataclasses import dataclass
import logging

import jsonpickle
import json

from chirpy.core.flags import SIZE_THRESHOLD
from chirpy.core.util import print_dict_linebyline

logger = logging.getLogger('chirpylogger')


@dataclass
class UserAttributes:
    user_id: str
    #creation_date_time: str

    @classmethod
    def deserialize(cls, mapping: dict):
        decoded_items = {}
        for k, v in mapping.items():
            try:
                decoded_items[k] = jsonpickle.decode(v)
            except:
                logger.error(f"Unable to decode {k}:{v} from past state")

        constructor_args = ['user_id']
        base_self = cls(**{k: decoded_items[k] for k in constructor_args})
        for k in decoded_items:
            if k not in constructor_args:
                setattr(base_self, k, decoded_items[k])
        return base_self

    def prune_jsons(self):
        """
        Prune jsons from getting too big
        """
        for key in self.__dict__.keys():
        	res = getattr(self, key)
        	ever_successful = False
        	if res is None:
        		continue
        	while True:
        		try:
        			res = json.loads(res)
        		except:
        			break
        		ever_successful = True
        	if ever_successful:
        		setattr(self, key, json.dumps(res))

    def serialize(self):
        logger.debug(f'Running jsonpickle version {jsonpickle.__version__}')
        logger.debug(f'jsonpickle backend names: {jsonpickle.backend.json._backend_names}')
        logger.debug(f'jsonpickle encoder options: {jsonpickle.backend.json._encoder_options}')
        logger.debug(f'jsonpickle fallthrough: {jsonpickle.backend.json._fallthrough}')

        encoded_dict = {k: jsonpickle.encode(v) for k, v in self.__dict__.items()}
        total_size = sum(len(k) + len(v) for k, v in encoded_dict.items())

        if total_size > SIZE_THRESHOLD:
            logger.primary_info(
                f"Total encoded size of state is {total_size}, which is greater than allowed {SIZE_THRESHOLD}. \n"
                f"Size of each value in the dictionary is:\n{print_dict_linebyline({k: len(v) for k, v in encoded_dict.items()})}. \n")

            # Tries to reduce size of the current state
            self.prune_jsons()
            encoded_dict = {k: jsonpickle.encode(v) for k, v in self.__dict__.items()}
            total_size = sum(len(k) + len(v) for k, v in encoded_dict.items())
        logger.primary_info(
            f"Total encoded size of state is {total_size}\n"
            f"Size of each value in the dictionary is:\n{print_dict_linebyline({k: len(v) for k, v in encoded_dict.items()})}. \n")
        return encoded_dict

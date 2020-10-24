import random
from typing import Optional, List
ACKNOWLEDGE_NO = ['Ok sure.', 'Ok, no problem.', 'For sure.', 'Alright.', 'Of course', 'Sure']

def acknowledge_no(conversation_history: Optional[List[str]] = None):
    return random.choice(ACKNOWLEDGE_NO)

class ConditionalState(object):
    def __init__(self, acknowledged_entity_name: str):
        self.acknowledged_entity_name = acknowledged_entity_name  # the name of the entity we acknowledged on this turn

    def __repr__(self):
        return f"<ConditionalState: acknowledged_entity_name={self.acknowledged_entity_name}>"


class State(object):
    def __init__(self):
        self.acknowledged = set()  # set of strings; names of entities that have been acknowledged

    def update_state_if_chosen(self, conditional_state: ConditionalState):
        self.acknowledged.add(conditional_state.acknowledged_entity_name)

    def __repr__(self):
        return f"<State: acknowledged={self.acknowledged}>"

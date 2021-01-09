from chirpy.response_generators.opinion2.state_actions import Action

ACTION_SPACE = [Action(solicit_opinion=True), \
    Action(exit=True), Action(solicit_reason=True), Action(suggest_alternative=True)]
for sentiment in [0, 4]:
    for give_agree in [True, False]:
        for give_reason in [True, False]:
            if not give_agree and not give_reason:
                continue
            for solicit_agree, solicit_reason, suggest_alternative in [(True, False, False), (False, True, False), (False, False, True)]:
                ACTION_SPACE += [Action(sentiment, give_agree, give_reason, False, False, solicit_agree, solicit_reason, suggest_alternative)]
ACTION_SPACE = [action for action in ACTION_SPACE if not (not action.give_reason and action.solicit_agree)]
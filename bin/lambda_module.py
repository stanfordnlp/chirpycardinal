
def lambda_handler(local_agent, user_utterance):
    response, deserialized_current_state = local_agent.process_utterance(user_utterance)
    should_end_conversation = deserialized_current_state['should_end_session']
    return response, should_end_conversation
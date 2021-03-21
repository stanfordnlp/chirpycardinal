import re

import jsonpickle
from flask import Flask, request
import uuid

#from agent.agents.remote_non_persistent import RemoteNonPersistentAgent as Agent
from agents.remote_psql_persistent import RemotePersistentAgent as Agent
app = Flask(__name__)
from flask_cors import CORS
CORS(app, origins='*')

@app.route('/conversation', methods=['POST'])
def conversational_turn():
    json_args = request.get_json(force=True)
    #TODO: Error handling?
    user_utterance = str(json_args.get('user_utterance', None) or '')
    alexa_asr_user_utterance = convert_to_alexa_asr(user_utterance)
    session_uuid = str(json_args.get('session_uuid', None) or str(uuid.uuid4()))
    user_uuid = str(json_args.get('user_uuid', None) or str(uuid.uuid4()))
    payload = json_args.get('payload', None) or {}
    client = str(json_args.get('client', ''))
    client_user_id = str(json_args.get('client_user_id', ''))
    client_information = json_args.get('client_information', {})
    if 'creation_date_time' in payload:
        new_session = False
        last_state_creation_time = payload['creation_date_time']
    else:
        new_session = True
        last_state_creation_time = None

    agent = Agent(session_id = session_uuid,
                                           user_id = user_uuid,
                                           new_session=new_session,
                                           last_state_creation_time = last_state_creation_time)
    response, deserialized_current_state = agent.process_utterance(alexa_asr_user_utterance)

    #TODO: Consider returning the deserialized current state
    json_response = {
        'session_uuid': session_uuid,
        'user_uuid': user_uuid,
        'bot_utterance': response,
        'payload': {'creation_date_time': jsonpickle.encode(deserialized_current_state['creation_date_time'])}
    }
    return json_response

def convert_to_alexa_asr(sentence: str):
    alexa_asr_sentence = re.sub(r"[^\w\d'.\s]+", '', sentence) #remove punctuations except . and '
    alexa_asr_sentence = re.sub(r"(?P<pre>[\w\s\d]{2,})[.]+(?P<post>[\s]|$)", r'\g<pre> \g<post>', alexa_asr_sentence) #remove . except when they are used in an abbreviation (i.e. without space separation)
    alexa_asr_sentence = re.sub(r"(?P<pre>[\s])[.]+", r'\g<pre>', alexa_asr_sentence) #remove . except when they are used in an abbreviation (i.e. without space separation)
    alexa_asr_sentence = re.sub(r"[\s]+", " ", alexa_asr_sentence)
    alexa_asr_sentence = alexa_asr_sentence.lower().strip()
    return alexa_asr_sentence

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5001)
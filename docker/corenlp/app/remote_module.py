from stanfordnlp.server import CoreNLPClient
import os
import time

required_context = ['text', 'annotators']

os.environ['CORENLP_HOME'] = os.environ.get('CORENLP_HOME', '/deploy/stanford-corenlp-full-2018-10-05')

print('initializing corenlpclient...')
t0 = time.time()
# According to advice from Peng, we should initialize the CoreNLPClient with all the annotators we want to send requests for
# Complete list of annotators here: https://stanfordnlp.github.io/CoreNLP/annotators.html
# timeout is 300*1000 milliseconds = 300 seconds = 5 mins
client = CoreNLPClient(annotators=['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse', 'coref', 'sentiment'],
                       timeout=300*1000, be_quiet=False,
                       properties={
                            "parser.model": "edu/stanford/nlp/models/lexparser/englishPCFG.caseless.ser.gz",
                            "pos.model":"edu/stanford/nlp/models/pos-tagger/english-caseless-left3words-distsim.tagger",
                            "ner.model":"edu/stanford/nlp/models/ner/english.all.3class.caseless.distsim.crf.ser.gz,edu/stanford/nlp/models/ner/english.muc.7class.caseless.distsim.crf.ser.gz,edu/stanford/nlp/models/ner/english.conll.4class.caseless.distsim.crf.ser.gz"})
client.ensure_alive()  # this takes some time especially if you specify many annotators above
print('initializing corenlpclient took {} seconds'.format(time.time()-t0))

def get_required_context():
    return required_context

def handle_message(msg):
    """
    Annotates msg['text'] with CoreNLPClient, using the annotators specified in msg['annotators'].
    Returns the full annotation in json format.
    """
    print('\nannotating message {} with annotators {}...'.format(msg['text'], msg['annotators']))
    t0 = time.time()
    ann = client.annotate(msg['text'], annotators=msg['annotators'], output_format='json')
    print('annotating took {} seconds'.format(time.time()-t0))
    print('annotation: {}'.format(ann))
    return ann


if __name__ == "__main__":
    for user_utterance in ['I hate you', 'I love you', 'I think you are ok', 'What is for dinner', 'no i love animals']:
        msg = {"text": user_utterance, 'annotators': ['sentiment']}
        ann = handle_message(msg)
        print(f'ann: {ann}')
import json
import stanfordnlp

nlp = stanfordnlp.Pipeline(processors='tokenize,mwt,pos,lemma,depparse')
required_context = ['text']

def get_required_context():
    return required_context

def handle_message(msg):
    """
    Annotates msg['text'] with stanfordnlp, using the processors specified above.
    Returns the full annotation as a json-encoded string.
    """
    text = msg['text']
    print(f'Annotating this text with stanfordnlp: {text}')
    annotation = nlp(text)  # stanfordnlp.Document
    print(f'Got this annotation: {annotation}')

    # We need to json serialize the annotation (a stanfordnlp.Document) so we can send it to the lamdba fn.
    # We can't jsonpickle here and unpickle on lambda, because we can't install stanfordnlp on the lambda fn
    # (it requires pytorch and is too big).
    # Instead we'll json-serialize in a way that loses the stanfordnlp class but keeps as much information as possible.

    # First, remove circular references that prevent us from json serializing
    # This is a hack, but we're not sure what else we can do
    for sentence in annotation.sentences:
        for word in sentence.words:
            word.parent_token = '<removed to avoid circular references>'

    # json serialize to a string
    # All non-serializable classes are converted to their underlying __dict__
    annotation_str = json.dumps(annotation, default=lambda o: o.__dict__)  # str

    print(f'JSON encoded annotation: {annotation_str}')
    return annotation_str


if __name__ == "__main__":
    msg = {"text": 'i think ariana grande is an amazing singer'}
    annotation = handle_message(msg)
    annotation = json.loads(annotation)
    print(f'Annotation: {annotation}')
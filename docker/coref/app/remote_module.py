import spacy
import re

nlp = spacy.load('en_core_web_sm')

import neuralcoref
neuralcoref.add_to_pipe(nlp)

# context is what we will be resolving from, utterance is what we are resolving.
required_context = ['context', 'utterance']

ignore_list = ["'s", 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", 
               "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves']

remove_symbol = r"\:|\-|\~|\(|\)|\%|\$|\#|\@|\&|\*|\+|\=|\^|\<|\>"


def get_required_context():
    return required_context


def handle_message(msg):
    context = msg['context']
    utterance = msg['utterance']
    context = re.sub(r"\<.*?\>", "", context)
    context = re.sub(remove_symbol, "", context).strip()
    context = re.sub(r"([^\.!\?])$", r"\1.", context)
    input_text = ' '.join([context, utterance])

    doc = nlp(input_text)
    coref_clusters = doc._.coref_clusters
    valid_clusters = list(filter(lambda cluster: all(str(item) not in ignore_list for item in cluster), coref_clusters))
    clusters_dict = {cluster.main.text: [span.text for span in cluster.mentions] for cluster in valid_clusters}

    resolved_total = get_resolved(doc, valid_clusters)
    start_token = len(nlp(context))
    resolved_utterance = ''.join(resolved_total[start_token:])
    return {'clusters': clusters_dict, 'resolved': resolved_utterance}


def get_resolved(doc, clusters):
    ''' Return a list of utterrances text where the coref are resolved to the most representative mention'''
    resolved = list(tok.text_with_ws for tok in doc)
    for cluster in clusters:
        for coref in cluster:
            if coref != cluster.main:
                resolved[coref.start] = cluster.main.text + doc[coref.end-1].whitespace_
                for i in range(coref.start+1, coref.end):
                    resolved[i] = ""
    return resolved

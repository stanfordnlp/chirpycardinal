from transformers import BartTokenizer, BartForConditionalGeneration

import spacy
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import numpy as np
import requests
import time

completion_tokenizer = BartTokenizer.from_pretrained("facebook/bart-large")
completion_model = BartForConditionalGeneration.from_pretrained("models/bart", force_bos_token_to_be_generated=True).cuda()

stop_words = set(stopwords.words('english'))
nlp = spacy.load('en_core_web_lg')

# required_context = ['contexts', 'prompts']

def chunk_text(sentences, sentence_length=3):
    # chunk text into groups of sentences / paragraphs which we will use to match to the templates
    # print(text)
    # assert False
    chunks = [' '.join(sentences[i:i+sentence_length]).replace('\n', '') for i in range(0, len(sentences)-sentence_length+1, sentence_length)]
    return chunks

def get_embedding_for_tokens(tokens):
    vectors = []
    for token in tokens:
        word = nlp.vocab[token]
        if word.has_vector: vectors.append(word.vector)
    return np.array(vectors)

def sim_template_para(template_vects, keyword_vects, k=3):
    denom = np.outer(np.linalg.norm(template_vects, axis=1), np.linalg.norm(keyword_vects, axis=1))
    cos_sim = np.dot(template_vects, keyword_vects.T) / denom

    score = 0
    i = 0
    for template_row in cos_sim:
        i += 1
        ind = np.argpartition(template_row, -k)[-k:]
        top_k = template_row[ind]
        score += np.sum(top_k)

    score /= len(template_vects) # normalize by num template keywords

    return score

def context_for_templates(template_tuples, sentences, sentence_length):
    groups = chunk_text(sentences, sentence_length)
    counts = {i: 0 for i in range(len(groups))}
    templates_to_context = {}
    template_embeddings = [get_embedding_for_tokens(template_keywords) for (_, template_keywords) in template_tuples]
    paragraph_embeddings = [get_embedding_for_tokens(word_tokenize(group)) for group in groups]
    similarities = np.zeros([len(template_embeddings), len(paragraph_embeddings)])
    print(similarities.shape)
    for t, template_embedding in enumerate(template_embeddings):
        for p, paragraph_embedding in enumerate(paragraph_embeddings):
            similarities[t][p] = sim_template_para(template_embedding, paragraph_embedding)

    top_k = 5 # min(len(template_embeddings), len(paragraph_embeddings))
    N = len(paragraph_embeddings)

    # print(similarities)
    for i in range(top_k):
        top_element = np.argmax(similarities)
        print("Top element is", top_element)
        template_idx, paragraph_idx = top_element // N, top_element % N
        print("Top idxs are", paragraph_idx, template_idx)
        print(template_tuples[template_idx][0])
        # print(template_idx, paragraph_idx, len(template_tuples), len(groups))
        templates_to_context[template_tuples[template_idx][0]] = (groups[paragraph_idx], similarities[template_idx][paragraph_idx])
        similarities[template_idx, :] = -1
        similarities[:, paragraph_idx] = -1
        # print(similarities)

    elements = sorted(templates_to_context.items(), key=lambda x: x[1][1])
    for template, (paragraph, score) in elements:
        print(template)
        print(paragraph)
        print(score)

    return templates_to_context

def complete(contexts, prompts, **kwargs):
    print("Context", len(contexts), "Prompts", len(prompts))
    # print(kwargs)
    priming = [(context + '::' + prompt) for context, prompt in zip(contexts, prompts)]
    a = time.time()
    batch = completion_tokenizer(priming, return_tensors='pt', padding=True)
    b = time.time()
    print(f"Finished tokenizing in {b-a:.3f} sec")
    a = time.time()
    generated_ids = completion_model.generate(batch['input_ids'].cuda(), **kwargs)
    b = time.time()
    print(f"Finished generating in {b-a:.3f} sec")
    a = time.time()
    out = completion_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
    b = time.time()
    print(f"Finished decoding in {b-a:.3f} sec")
    return out




def handle_message(msg):
    try:
        # print(msg)
        if 'tuples' in msg:
            sentence_length = msg.get('sentence_length', min(3, len(msg['sentences'])))
            a = time.time()
            templates_to_context = context_for_templates(msg['tuples'], msg['sentences'], sentence_length)
            b = time.time()
            print(f"Finished context_for_templates in {b-a:.3f} sec")
            msg['prompts'] = msg.get('prompts', []) + list(templates_to_context.keys())
            msg['contexts'] = msg.get('contexts', []) + list([x[0] for x in templates_to_context.values()])
            print(msg)
        default_values = {
            'contexts': ["this is a [thing]"],
            'prompts': ["test"],
            'top_p': 0.1,
            'temperature': 1.0,
            'top_k': 0,
            'num_beams': 10,
            'num_return_sequences': 1,
            'min_length': 10,
            'max_length': 100,
            'num_beam_groups': 1,
            'diversity_penalty': 0.0,
            'do_sample': False,
            'repetition_penalty': 1.0
        }
        out = {key: msg.get(key, default_values[key]) for key in default_values.keys()}
        a = time.time()
        completions = complete(**out)
        b = time.time()
        print(f"Finished infilling in {b-a:.3f} sec")

        completions = ['\n         '.join(completions[i:i+out['num_return_sequences']]) for i in range(0, len(completions), out['num_return_sequences'])]
        output = {
            'completions': completions,
            'prompts': msg['prompts'],
            'contexts': msg['contexts']
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('Encountered error, which we will send back in output: ', str(e))
        output = {
            'error': True,
            'message': str(e),
        }
    return output


if __name__ == "__main__":
    msg = {
        'prompts': ['I love [song] because of its [quality].', 'I still remember [year], when it seemed like [song] was on every [genre] station.'],
        'contexts': ['Adele released her second studio album, 21, in 2011.The album was critically well-received and surpassed the success of her debut, earning numerous awards in 2012, among them a record-tying six Grammy Awards, including Album of the Year; the Brit Award for British Album of the Year; and the American Music Award for Favorite Pop/Rock Album. The album has been certified 17× platinum in the UK, and is overall the fourth best-selling album in the nation. In the US, it has held the top position longer than any album since 1985, and is certified Diamond.The world\'s best-selling album of 2011 and 2012, 21 has sold over 31 million copies, making it the best-selling album of the 21st century. The success of 21 earned Adele numerous mentions in the Guinness Book of Records. She was the first female in the history of the Billboard Hot 100 to have three simultaneous top-ten singles as a lead artist, with "Rolling in the Deep", "Someone Like You", and "Set Fire to the Rain", all of which also topped the chart.In 2012, Adele released "Skyfall", which she co-wrote and recorded for the James Bond film of the same name. The song won an Academy Award, a Golden Globe, and the Brit Award for British Single of the Year. After taking a three-year break, Adele released her third studio album, 25, in 2015.It became the year\'s best-selling album and broke first-week sales records in the UK and US. 25 was her second album to be certified Diamond in the US and earned her five Grammy Awards, including Album of the Year, and four Brit Awards, including British Album of the Year. The lead single, "Hello", became the first song in the US to sell over one million digital copies within a week of its release.', 'Adele released her second studio album, 21, in 2011.The album was critically well-received and surpassed the success of her debut, earning numerous awards in 2012, among them a record-tying six Grammy Awards, including Album of the Year; the Brit Award for British Album of the Year; and the American Music Award for Favorite Pop/Rock Album. The album has been certified 17× platinum in the UK, and is overall the fourth best-selling album in the nation. In the US, it has held the top position longer than any album since 1985, and is certified Diamond.The world\'s best-selling album of 2011 and 2012, 21 has sold over 31 million copies, making it the best-selling album of the 21st century. The success of 21 earned Adele numerous mentions in the Guinness Book of Records. She was the first female in the history of the Billboard Hot 100 to have three simultaneous top-ten singles as a lead artist, with "Rolling in the Deep", "Someone Like You", and "Set Fire to the Rain", all of which also topped the chart.In 2012, Adele released "Skyfall", which she co-wrote and recorded for the James Bond film of the same name. The song won an Academy Award, a Golden Globe, and the Brit Award for British Single of the Year. After taking a three-year break, Adele released her third studio album, 25, in 2015.It became the year\'s best-selling album and broke first-week sales records in the UK and US. 25 was her second album to be certified Diamond in the US and earned her five Grammy Awards, including Album of the Year, and four Brit Awards, including British Album of the Year. The lead single, "Hello", became the first song in the US to sell over one million digital copies within a week of its release.']
    }
    result = handle_message(msg)
    print(result)

from bert_qa import predict
import transformers

required_context = ['question', 'context', 'n_best_size', 'max_answer_length']
tokenizer = transformers.BertTokenizer.from_pretrained('bert-base-uncased')
model = transformers.BertForQuestionAnswering.from_pretrained('bert-large-uncased-whole-word-masking-finetuned-squad').to('cuda:0')

def get_required_context():
    return required_context

# msg: Dict of info you're passing in.
def handle_message(msg):
    #your remote module should operate on the text or other context information here
    question = msg['question']
    context = msg['context']
    n_best_size = msg['n_best_size']
    max_answer_length = msg['max_answer_length']
    answers = predict(question, context, tokenizer, model, n_best_size, max_answer_length)
    return {'response': answers}

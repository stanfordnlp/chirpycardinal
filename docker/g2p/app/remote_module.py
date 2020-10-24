from g2p_en import G2p

required_context = ['text']
g2p = G2p()

def get_required_context():
    return required_context

def handle_message(msg):
    #your remote module should operate on the text or other context information here
    print("Got input for g2p: ", msg['text'])
    input_text = msg['text']
    return g2p(input_text)

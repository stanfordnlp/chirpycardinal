FROM nvidia/cuda:11.0-base

ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -qq && apt-get install -qq nginx supervisor gcc g++ git wget

# Get a specific python version
RUN apt-get install -qq software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -qq
RUN apt-get install -qq python3.7 python3-pip

RUN mkdir -p /deploy/app
RUN python3.7 -m pip install awscli

RUN python3.7 -m pip install cmake
RUN wget https://files.pythonhosted.org/packages/f2/e2/813dff3d72df2f49554204e7e5f73a3dc0f0eb1e3958a4cad3ef3fb278b7/sentencepiece-0.1.91-cp37-cp37m-manylinux1_x86_64.whl
RUN python3.7 -m pip install sentencepiece-0.1.91-cp37-cp37m-manylinux1_x86_64.whl

COPY model/gpt2ed /deploy/app/models/gpt2ed
COPY app deploy/app/
RUN python3.7 -m pip install -r /deploy/app/requirements.txt


# Setup git credentials and get git repository
RUN git config --global credential.helper '!aws codecommit credential-helper $@'
RUN git config --global credential.UseHttpPath true
RUN git config -l --global
RUN git clone https://github.com/abisee/transfer-learning-conv-ai.git /deploy/app/transfer-learning-conv-ai && cd /deploy/app/transfer-learning-conv-ai && git checkout 5c3bf313467b86f1e1418cce9ce01e5a3e8a3309 && cd ../../

# Frontloading pip installation, so that these steps can be cached in subsequent calls
# Pip installation takes time, especially pytorch.
# If your repo contains more requirements add them here, so that packages don't need to be installed for every new pull

COPY app/requirements.txt /requirements.txt
RUN python3.7 -m pip install -r /requirements.txt

RUN python3.7 -c 'from transformers import AutoTokenizer; UPDOWN_TOKENIZER = AutoTokenizer.from_pretrained("microsoft/DialogRPT-updown")'
RUN python3.7 -c 'from transformers import AutoModelForSequenceClassification; UPDOWN_MODEL = AutoModelForSequenceClassification.from_pretrained("microsoft/DialogRPT-updown")'

COPY app /deploy/app

# Setup nginx
RUN rm /etc/nginx/sites-enabled/default
# Setup flask application
COPY config/flask.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/flask.conf /etc/nginx/sites-enabled/flask.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

RUN ln -s /usr/local/bin/gunicorn /usr/bin/gunicorn

# Setup supervisord
RUN mkdir -p /var/log/supervisor
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 80

# Start processes
CMD ["/usr/bin/supervisord"]

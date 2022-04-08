FROM nvidia/cuda:11.0-base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y

RUN apt-get update -y && apt-get install -y nginx supervisor gcc g++ git wget curl

RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -y
RUN apt install -y python3.8-dev
RUN apt remove python3-pip
RUN apt install -y python3.8-distutils
RUN apt install -y python3-setuptools
RUN python3.8 -m easy_install pip

RUN python3.8 -m pip install awscli
RUN python3.8 -m pip install wheel
#RUN python3.8 -m pip install cmake
#RUN wget https://files.pythonhosted.org/packages/f2/e2/813dff3.82df2f49554204e7e5f73a3dc0f0eb1e3958a4cad3ef3fb278b7/sentencepiece-0.1.91-cp37-cp37m-manylinux1_x86_64.whl
#RUN python3.8 -m pip install sentencepiece-0.1.91-cp37-cp37m-manylinux1_x86_64.whl

COPY app/requirements.txt /deploy/requirements.txt
RUN python3.8 -m pip install -r /deploy/requirements.txt

# Download the model from S3
RUN aws  --no-sign-request s3 sync s3://chirpycardinal/infiller /deploy/app/models/bart

COPY app /deploy/app
COPY libfiles/modeling_utils.py /usr/local/lib/python3.8/dist-packages/transformers/modeling_utils.py
RUN python3.8 -m spacy download en_core_web_lg
RUN python3.8 -c "import nltk; nltk.download('punkt')"
RUN python3.8 -m nltk.downloader stopwords
RUN python3.8 -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.0.0/en_core_web_lg-3.0.0-py3-none-any.whl
RUN python3.8 -c "import nltk; nltk.download('punkt')"
RUN python3.8 -m nltk.downloader stopwords

RUN rm /etc/nginx/sites-enabled/default
COPY config/flask.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/flask.conf /etc/nginx/sites-enabled/flask.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

RUN ln -s /usr/local/bin/gunicorn /usr/bin/gunicorn

RUN mkdir -p /var/log/supervisor
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN python3.8 -m pip freeze | grep trans

EXPOSE 80

# Start processes
CMD ["/usr/bin/supervisord"]

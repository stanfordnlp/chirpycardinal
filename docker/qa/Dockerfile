FROM nvidia/cuda:9.0-base

RUN apt-get update -y
RUN apt-get install -y nginx supervisor gcc g++ git python3-pip
# update pip
RUN pip3 install pip --upgrade

# Setup flask application
RUN mkdir -p /deploy/app
COPY app/requirements.txt /deploy/app/requirements.txt
RUN pip3 install -r /deploy/app/requirements.txt
RUN python3 -m nltk.downloader punkt
RUN python3 -c "import transformers; transformers.BertTokenizer.from_pretrained('bert-base-uncased'); transformers.BertForQuestionAnswering.from_pretrained('bert-large-uncased-whole-word-masking-finetuned-squad')"

# Setup nginx
RUN rm /etc/nginx/sites-enabled/default
COPY config/flask.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/flask.conf /etc/nginx/sites-enabled/flask.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN ln -s /usr/local/bin/gunicorn /usr/bin/gunicorn
# Setup supervisord
RUN mkdir -p /var/log/supervisor
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
#COPY config/gunicorn.conf /etc/supervisor/conf.d/gunicorn.conf
EXPOSE 80
COPY app /deploy/app

# Start processes
CMD ["/usr/bin/supervisord"]
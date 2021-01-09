FROM nvidia/cuda:9.0-base

RUN apt-get update -y

# Get some basic packages
RUN apt-get update -y && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update && apt-get install -y nginx supervisor gcc g++ git

# Get a specific python version
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -y
RUN apt-get install -y python3.7-dev python3-pip
RUN python3.7 -m pip install -U pip
#RUN apt-get install build-essential libssl-dev libffi-dev

#COPY usr/lib/sentencepiece-0.1.83-cp37-cp37m-manylinux1_x86_64.whl deploy/usr/lib/app/sentencepiece-0.1.83-cp37-cp37m-manylinux1_x86_64.whl
#RUN python3.7 -m pip install sentencepiece-0.1.83-cp37-cp37m-manylinux1_x86_64.whl
#RUN apt-get install pip

# Any pip installation should be run with the python version you've installed
# eg. RUN python3.7 -m pip install ...

# Set up AWS credentials
RUN mkdir -p /deploy/app
# Install awscli and move the .aws dir to ~/
# For some reason, "COPY .aws ~/.aws" doesn't work (the command runs but afterwards ~/.aws is not there)
# RUN python3.7 -m pip install --upgrade pip && python3.7 -m pip install awscli
# COPY .aws /deploy/app/.aws
# RUN mv /deploy/app/.aws ~/

# Frontloading pip installation, so that these steps can be cached in subsequent calls
# Pip installation takes time, especially pytorch.
# If your repo contains more requirements add them here, so that packages don't need to be installed for every new pull
COPY app/requirements.txt deploy/app/requirements.txt
RUN python3.7 -m pip install -r /deploy/app/requirements.txt

# Download the model from S3
COPY model/question-classifier deploy/app/models/baseline

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

COPY app deploy/app/

EXPOSE 80

# Start processes
CMD ["/usr/bin/supervisord"] 


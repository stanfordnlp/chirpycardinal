FROM nvidia/cuda:9.0-base

# Get some basic packages
RUN apt-get update -y && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update -y && apt-get install -y nginx supervisor gcc g++ git 

# Get a specific python version
RUN apt-get update -y && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -y && apt install -y python3.7-dev python3-pip
RUN python3.7 -m pip install --upgrade pip

# Any pip installation should be run with the python version you've installed
# eg. RUN python3.7 -m pip install ...

# Set up AWS credentials
RUN mkdir -p /deploy/app
# Install awscli and move the .aws dir to ~/
# For some reason, "COPY .aws ~/.aws" doesn't work (the command runs but afterwards ~/.aws is not there)
RUN python3.7 -m pip install awscli
#COPY .aws /deploy/app/.aws
#RUN mv /deploy/app/.aws ~/

# Frontloading pip installation, so that these steps can be cached in subsequent calls
# Pip installation takes time, especially pytorch.
# If your repo contains more requirements add them here, so that packages don't need to be installed for every new pull
COPY app/requirements.txt deploy/app/requirements.txt
RUN python3.7 -m pip install -r /deploy/app/requirements.txt

# Download the model from S3
COPY model/dialog-act/midas-2 deploy/app/models/midas-2

# Download vocab file from huggingface
RUN apt-get install wget
RUN wget -O deploy/app/models/midas-2/vocab.txt "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased-vocab.txt"
# RUN aws s3 cp s3://models.huggingface.co/bert/bert-base-uncased-vocab.txt deploy/app/models/midas-2/vocab.txt

# Setup git credentials and get git repository
RUN git config --global credential.UseHttpPath true
RUN git config -l --global
# Note that we checkout a specific version. When you want a new version change the version number here.
# This ensures that the dockerfile cache is invalidated from this point onwards
# RUN git clone https://git-codecommit.us-east-1.amazonaws.com/v1/repos/dialog-act /deploy/app/dialogact && cd /deploy/app/dialogact && git checkout 62ee6ab6 && cd ../../

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


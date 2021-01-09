FROM nvidia/cuda:9.0-base

RUN apt-get update -y

# Get some basic packages
RUN apt-get update -y && apt-get install -y nginx supervisor gcc g++ git

# Get a specific python version
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -y
RUN apt install -y python3.7-dev python3-pip
RUN python3.7 -m pip install -U pip

# Any pip installation should be run with the python version you've installed
# eg. RUN python3.7 -m pip install ...

# Set up AWS credentials
RUN mkdir -p /deploy/app
# Install awscli and move the .aws dir to ~/
# For some reason, "COPY .aws ~/.aws" doesn't work (the command runs but afterwards ~/.aws is not there)

# Frontloading pip installation, so that these steps can be cached in subsequent calls
# Pip installation takes time, especially pytorch.
# If your repo contains more requirements add them here, so that packages don't need to be installed for every new pull
COPY app deploy/app/
RUN python3.7 -m pip install -r /deploy/app/requirements.txt

# Download the model from S3
COPY model/gpt2ed /deploy/app/models/Jan04_22-40-10_ip-172-31-71-210_gpt2-medium

# Setup git credentials and get git repository
#RUN git config --global credential.helper '!aws codecommit credential-helper $@'
RUN git config --global credential.UseHttpPath true
RUN git config -l --global
# Note that we checkout a specific version. When you want a new version change the version number here.
# This ensures that the dockerfile cache is invalidated from this point onwards
RUN git clone https://github.com/abisee/transfer-learning-conv-ai.git /deploy/app/transfer-learning-conv-ai && cd /deploy/app/transfer-learning-conv-ai && git checkout 5c3bf313467b86f1e1418cce9ce01e5a3e8a3309 && cd ../../

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


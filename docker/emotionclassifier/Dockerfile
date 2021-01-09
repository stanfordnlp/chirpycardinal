FROM nvidia/cuda:9.0-base

RUN apt-get update -y

# Get some basic packages
RUN apt-get update -y && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update && apt-get install -y nginx supervisor gcc g++ git

# Get a specific python version
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -y
RUN apt install -y python3.7-dev python3-pip

# Any pip installation should be run with the python version you've installed
# eg. RUN python3.7 -m pip install ...

# Frontloading pip installation, so that these steps can be cached in subsequent calls
# Pip installation takes time, especially pytorch.
# If your repo contains more requirements add them here, so that packages don't need to be installed for every new pull
COPY app/requirements.txt deploy/app/requirements.txt
RUN python3.7 -m pip install -r /deploy/app/requirements.txt

# Copy the model
COPY model/emotion-classifier/roberta deploy/app/models/roberta/

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


FROM nvidia/cuda:10.2-base

RUN apt-get update -y

# Get some basic packages
RUN apt-get install -y nginx supervisor gcc g++ git

# Get a specific python version
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -y
RUN apt install -y python3.7 python3-pip

RUN python3.7 -m pip install awscli
RUN mkdir -p /deploy/app/model
RUN aws --no-sign-request --region us-west-2 s3 sync s3://chirpycardinal/convpara/60/ deploy/app/model/


# Any pip installation should be run with the python version you've installed
# eg. RUN python3.7 -m pip install ...
RUN python3.7 -m pip install torch==1.7.0
# Frontloading pip installation, so that these steps can be cached in subsequent calls
# Pip installation takes time, especially pytorch.
# If your repo contains more requirements add them here, so that packages don't need to be installed for every new pull
COPY app/requirements.txt deploy/app/requirements.txt
RUN python3.7 -m pip install -r /deploy/app/requirements.txt

# Setup git credentials and get git repository
#RUN git config --global credential.UseHttpPath true
#RUN git config -l --global
# Note that we checkout a specific version. When you want a new version change the version number here.
# This ensures that the dockerfile cache is invalidated from this point onwards

COPY app deploy/app/
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


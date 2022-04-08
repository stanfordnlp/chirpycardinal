FROM nvidia/cuda:11.0-base

ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y && apt-get install -y nginx supervisor gcc g++ git
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -y
RUN apt install -y python3.7-dev python3-pip python3-setuptools

RUN mkdir -p /deploy/app
RUN python3.7 -m pip install awscli

COPY app deploy/app/
RUN python3.7 -m pip install -r /deploy/app/requirements.txt

# Load the ParlAI copy we have with the custom agent; switch to correct branch
# RUN git clone https://git-codecommit.us-east-1.amazonaws.com/v1/repos/parlai-blenderbot-fork /deploy/app/parlai && cd /deploy/app/parlai && git checkout 43d0b2bee762d950bf2034ee1f5aa78b32bba023 && python3.7 setup.py develop && python3.7 -c "import parlai; print('Check to see that your ParlAI installation is where you expect:', parlai.__file__)" && cd ../../
RUN git clone https://github.com/stanfordnlp/chirpy-parlai-blenderbot-fork /deploy/app/parlai && cd /deploy/app/parlai && git checkout 3e1d1c646733ea6fd6a1d00984ec7b8ba58a0b73 && python3.7 setup.py develop && python3.7 -c "import parlai; print('Check to see that your ParlAI installation is where you expect:', parlai.__file__)" && cd ../../

# Download the model from S3
RUN aws --no-sign-request s3 sync s3://chirpycardinal/blender_distilled/ /deploy/app/blender_distilled/

COPY app deploy/app/
RUN rm /etc/nginx/sites-enabled/default
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

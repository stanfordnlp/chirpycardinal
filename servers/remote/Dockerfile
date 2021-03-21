FROM python:3.7-slim-buster

COPY ./servers/remote/requirements.txt /deploy/servers/remote/requirements.txt
WORKDIR /deploy

#RUN apt-get update -y
#RUN apt-get install -y curl

# update pip
RUN pip install pip --upgrade
RUN pip install -r /deploy/servers/remote/requirements.txt

# Setup flask application
EXPOSE 5001 5432 4080 4081 4082 4083 4084 4085

COPY ./ /deploy/
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "servers.remote.chat_api:app"]
#CMD ["python", "-m" ,"remote.chat_api"]
#RUN mkdir -p /deploy/app

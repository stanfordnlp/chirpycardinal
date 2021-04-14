It expects the following environment variables to be set

**Elasticsearch** 

* `ES_SCHEME` - `https`
* `ES_HOST` - `localhost` or url  (eg ....us-west-2.es.amazonaws.com)
* `ES_PORT` - `443`
* `ES_USER`
* `ES_PASSWORD`

**Postgres**
* `POSTGRES_HOST` - `localhost` or `host.docker.internal` (when running on docker for Mac/Windows and the db is on localhost) or the url
* `POSTGRES_USER_`
* `POSTGRES_PASSWORD`

**Callable urls**
* `corenlp_URL` - `localhost:port` or remote url
* `dialogact_URL`
* `g2p_URL`
* `gpt2ed_URL`
* `question_URL`
* `stanfordnlp_URL`

The recommended method is to store them in a file such as `local_env.list`
in the format 
```
ES_SCHEME=https
ES_HOST=localhost
...
```

## Runing locally
To run the server locally, run from project directory
```
source servers/remote/local_env.list
python -m servers.remote.chat_api
```

## Running via Docker
To build (from the project directory)
```
docker build --file servers/remote/Dockerfile .
```
This adds the entire project as context and builds the docker container terminating with an output like `Successfully built d2b0029ce2da`

To run the container, you will need to create another list of environment variables, say `docker_env.list`
Here `localhost` should be replaced by `host.docker.internal` when running using Docker for Mac/Windows
```
docker run -p 5001:5001 --env-file docker_env.list d2b0029ce2da 
```

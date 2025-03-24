# yaflaskapp
Yet another flash app

## Build docker image

docker build -t flask-hello-app .

## Starting docker

docker run -e PORT=8080 -p 8080:8080 flask-hello-app

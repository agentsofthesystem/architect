FROM python:3.11-alpine

# Install requirements for pycurl package
RUN apk update && apk add gcc libc-dev curl-dev openssl-dev

COPY requirements.txt /tmp/requirements.txt
COPY ./application /var/application

RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt

WORKDIR /var

CMD ["gunicorn", "-w", "1", "--access-logfile", "-", "-b", ":3000", "-t", "30", "--reload", "application.wsgi:start_app(deploy_as='docker_compose')"]
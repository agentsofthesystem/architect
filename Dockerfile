FROM python:3.11-alpine as base
FROM base as builder

# Setup temp install dir.
RUN mkdir /install
WORKDIR /install

# Install requirements for pycurl package
RUN apk update && apk add gcc libc-dev curl-dev openssl-dev

# Copy install requirements file.
COPY requirements.txt /tmp/requirements.txt
RUN pip install -U pip
RUN pip install --prefix=/install -r /tmp/requirements.txt

FROM base
RUN apk add curl-dev
COPY --from=builder /install /usr/local
COPY ./application /var/application
WORKDIR /var

CMD ["gunicorn", "-w", "2", "--access-logfile", "-", "-b", ":3000", "-t", "60", "--keep-alive", "30", "--reload", "application.wsgi:start_app(deploy_as='docker_compose')"]
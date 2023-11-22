FROM python:3.11

# Copy requirements file.
COPY requirements.txt /tmp/requirements.txt
COPY ./application /var/application

# Install requirements for pycurl package
RUN apt update && apt install libcurl4-nss-dev libssl-dev -y

# Run installer commands
RUN pip install -U pip
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /tmp/requirements.txt

WORKDIR /var

CMD ["gunicorn", "-w", "1", "--access-logfile", "-", "-b", ":80", "-t", "30", "--reload", "application.wsgi:start_app(deploy_as='docker_compose')"]
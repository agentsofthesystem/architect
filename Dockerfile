FROM python:3.11

# Copy requirements file.
COPY requirements.txt /tmp/requirements.txt
COPY ./application /var/application

# Run installer commands
RUN pip install -U pip
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /tmp/requirements.txt

# Manually install flask mail because master is ahead of version on pypi.
# RUN git clone https://github.com/jreed1701/flask-mail.git /var/packages/flask-mail
# RUN cd /var/packages/flask-mail && pip install -e .

WORKDIR /var

CMD ["gunicorn", "-w", "1", "--access-logfile", "-", "-b", ":3000", "-t", "30", "--reload", "application.wsgi:start_app(deploy_as='docker_compose')"]
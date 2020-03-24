FROM python:3.6.6

RUN groupadd -r plunger && useradd --no-log-init -r -g plunger plunger

WORKDIR /opt/tools
COPY bin /opt/tools/plunger/bin
COPY plunger /opt/tools/plunger/plunger
COPY install.sh /opt/tools/plunger/install.sh
COPY requirements.txt /opt/tools/plunger/requirements.txt

WORKDIR /opt/tools/plunger
RUN pip3 install virtualenv
RUN ./install.sh

WORKDIR /opt/tools/plunger

ENTRYPOINT ["bin/plunger"]

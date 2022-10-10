#ARG PYTHON_VERSION=3.9.1
#
#FROM python:${PYTHON_VERSION}
#
#RUN apt-get update && apt-get install -y \
#    python3-pip \
#    python3-venv \
#    python3-dev \
#    python3-setuptools \
#    python3-wheel
#
#RUN mkdir -p /app
#WORKDIR /app
#
#COPY requirements.txt .
#RUN pip install -r requirements.txt
#
#COPY . .
#
##RUN python main.py collectstatic --noinput
#
#
#EXPOSE 8080
#
## replace APP_NAME with module name
##CMD ["gunicorn", "--bind", ":8080", "--workers", "2", "demo.wsgi"]
#CMD python main.py

FROM ubuntu:20.04
RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3-pip && \
    apt-get install -y ffmpeg && apt-get install libopus0

WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
COPY . /bot
CMD python3 main.py

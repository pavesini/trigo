FROM python:alpine3.17

RUN apk update && apk add git

WORKDIR /bot
COPY ./bot.py ./requirements.txt /bot
RUN pip install -r requirements.txt 
RUN pip install git+https://github.com/oasisprotocol/sapphire-paratime.git@main#subdirectory=clients/py

ENTRYPOINT ["python", "bot.py"]

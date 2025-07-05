FROM python:alpine3.17

RUN apk update && apk add git

WORKDIR /bot
COPY ./requirements.txt /bot
RUN pip install -r requirements.txt 
RUN pip install git+https://github.com/oasisprotocol/sapphire-paratime.git@main#subdirectory=clients/py
COPY ./bot.py ./BlackjackABI.json /bot
COPY ./gif/over.gif ./gif/win.gif /bot/gif

ENTRYPOINT ["python", "bot.py"]

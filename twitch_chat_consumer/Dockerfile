FROM python:3.7.6
ENV PYTHONUNBUFFERED=1
# Install requirements before moving code for layer cache performance
COPY ./requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
RUN python -m textblob.download_corpora

COPY . /code
WORKDIR /code

#TODO: Should run as unprivlaged user
CMD ["python", "-m", "twitch_chat_consumer"]

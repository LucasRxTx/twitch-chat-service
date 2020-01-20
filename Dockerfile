FROM python:3.7.6
ENV PYTHONUNBUFFERED=1
# Install requirements before moving code for layer cache performance
COPY ./requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

COPY . /code
WORKDIR /code

#TODO: Should run as unprivlaged user
CMD ["uvicorn", "--reload", "--host", "0.0.0.0", "twitch_chat_service.__main__:app"]

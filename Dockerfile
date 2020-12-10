FROM python:3.8-slim

RUN groupadd -g 8733 jadetree \
  && adduser --disabled-password --uid 8733 --gid 8733 jadetree

WORKDIR /home/jadetree

RUN apt-get update \
  && apt-get -y upgrade \
  && apt-get -y install --no-install-recommends build-essential \
    libpq-dev libmariadbclient-dev

COPY requirements.txt ./
RUN python -m venv venv \
  && venv/bin/pip install -r requirements.txt \
  && venv/bin/pip install gunicorn

COPY jadetree jadetree
COPY migrations migrations
COPY docker/* ./
COPY pyproject.toml ./
RUN mkdir -p /var/lib/jadetree \
  && chown -R jadetree:jadetree /var/lib/jadetree ./ \
  && chmod +x docker-entry.sh

USER jadetree
EXPOSE 5000
ENTRYPOINT [ "/home/jadetree/docker-entry.sh" ]
CMD [ "jadetree" ]

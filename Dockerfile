FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y \
 git \
 tini \
 make \
 && rm -rf /var/lib/apt/lists/*

ENV PYROOT /pyroot
ENV PYTHONUSERBASE $PYROOT
ENV PATH=/pyroot/bin:$PATH

ENV VIRTUAL_ENV=/usr/src/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /usr/src

COPY .  /usr/src

RUN  python3 -m pip install poetry && \
     poetry config virtualenvs.in-project true && \
     poetry install

ENTRYPOINT [ "python", "main.py" ]

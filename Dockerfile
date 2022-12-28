FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y \
 git \
 tini \
 make \
 curl \
 unzip \
 && rm -rf /var/lib/apt/lists/*

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
unzip awscliv2.zip && \
./aws/install

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

FROM ubuntu:18.04
COPY requirements.apt /src/
WORKDIR /src
RUN set -x && \
    apt-get update && xargs apt-get install -y < requirements.apt
COPY requirements.txt /src
RUN pip install -r requirements.txt 
COPY ./oops /src/oops
COPY ./odincal /src/odincal
RUN pip install ./oops ./odincal
RUN useradd jenkins --uid 386 --shell /bin/bash --create-home
CMD level0file_server

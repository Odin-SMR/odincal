FROM python:2.7
WORKDIR /src
COPY requirements.txt /src
RUN pip install -r requirements.txt 
COPY ./oops /src/oops
COPY ./odincal /src/odincal
RUN pip install ./oops ./odincal
RUN useradd jenkins --uid 386 --shell /bin/bash --create-home
CMD level0file_server
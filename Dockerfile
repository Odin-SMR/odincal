from docker2.molflow.com/devops/odincal_base
workdir /src
run set -x && \
    apt-get update
run apt-get install -y \
            build-essential \
            libcfitsio-dev \
            libhdfeos-dev \
            python-pyinotify 
run pip install sqlalchemy
copy . /src
run cd oops && python setup.py install
run cd odincal && python setup.py install
cmd level0file_server


FROM louvainverificationlab/pynusmv-build:latest
ENV TZ=Europe/Amsterdam
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./inv_mc.py /pynusmv/

COPY ./examples/ /pynusmv/

VOLUME vol1

# install missing packages
RUN pip install pyparsing

WORKDIR /home/

# clone pynusmv binaries from github
RUN git clone https://github.com/LouvainVerificationLab/pynusmv.git

# install binaries   
RUN cd pynusmv/ && \
    python3 setup.py install

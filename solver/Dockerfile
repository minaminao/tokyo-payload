FROM ubuntu:23.10
WORKDIR /solver

RUN apt-get update -y && apt-get install curl git python3-pip python-is-python3 -y
RUN pip install --break-system-packages pwntools pyelftools==0.29

ENV SHELL /bin/bash
RUN curl -L https://foundry.paradigm.xyz | bash
ENV PATH $PATH:/root/.foundry/bin
RUN foundryup

COPY . .

RUN forge install foundry-rs/forge-std --no-git

CMD ["python", "solve.py"]

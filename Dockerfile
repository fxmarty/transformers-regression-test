FROM nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

ARG USER_ID
ARG GROUP_ID

RUN addgroup --gid $GROUP_ID user
RUN adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID user

RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    git \
    python3.10 \
    python3.10-dev \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    python -m pip install -U pip

RUN adduser user sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER user
WORKDIR /home/user

RUN pip install torch accelerate

# We need ONNX here because the dummy input generator relies on the ONNX config in Optimum, which is unwanted and needs to be fixed.
RUN pip install optimum omegaconf==2.3.0 hydra-core==1.3.2 hydra_colorlog==1.2.0 py3nvml psutil pandas onnx

RUN git clone https://github.com/fxmarty/optimum-benchmark.git && \
    cd optimum-benchmark && git checkout wip-ci && \
    pip install -e .

ARG COMMIT_SHA
ENV COMMIT_SHA=${COMMIT_SHA}
COPY transformers /home/user/transformers
RUN cd /home/user/transformers && git checkout $COMMIT_SHA && pip install -e .

# Format commit date as e.g. "2023-07-26_14:09:17"
RUN export COMMIT_DATE_GMT=`TZ=GMT git show -s --format=%cd --date=iso-local $COMMIT_SHA | rev | cut -c 7- | rev` && export COMMIT_DATE_GMT="${COMMIT_DATE_GMT// /_}"

WORKDIR /home/user/transformers-regression
CMD bash run_benchmark.sh

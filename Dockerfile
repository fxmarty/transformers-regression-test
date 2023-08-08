FROM nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG COMMIT_SHA

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3.10 \
    python3.10-dev \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    python -m pip install -U pip

RUN pip install torch accelerate

# We need ONNX here because the dummy input generator relies on the ONNX config in Optimum, which is unwanted and needs to be fixed.
RUN pip install optimum omegaconf==2.3.0 hydra-core==1.3.2 hydra_colorlog==1.2.0 py3nvml psutil pandas onnx

RUN git clone https://github.com/fxmarty/optimum-benchmark.git && \
    cd optimum-benchmark && git checkout wip-ci && \
    pip install -e .

COPY transformers /transformers
RUN cd /transformers && git checkout $COMMIT_SHA

WORKDIR /transformers-regression
CMD bash run_benchmark.sh

# IceGuard runtime for AWS Lambda (Python 3.12) with Java + PySpark.
# Base image: https://gallery.ecr.aws/lambda/python
FROM public.ecr.aws/lambda/python:3.12

RUN dnf install -y java-17-amazon-corretto-headless \
    && dnf clean all

ENV JAVA_HOME=/usr/lib/jvm/java-17-amazon-corretto
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV PYSPARK_PYTHON=/var/lang/bin/python3

ARG ICEGUARD_VERSION=1.0.0
RUN pip install --no-cache-dir "iceguard[spark,iceberg,otel]==${ICEGUARD_VERSION}"

LABEL org.opencontainers.image.source="https://github.com/vaquarkhan/IceGuard"
LABEL org.opencontainers.image.title="iceguard"
LABEL org.opencontainers.image.description="IceGuard Lambda Python 3.12 image with Java and PySpark"

# Demo handler; override CMD when you COPY your own handler.py
COPY examples/sam/handler.py ${LAMBDA_TASK_ROOT}/
CMD ["handler.lambda_handler"]

ARG BASE=python:3.10-alpine

FROM $BASE as pandas-base

WORKDIR /app

COPY requirements.txt .
RUN apk add --virtual build-dependencies build-base \
    && pip install $(grep "pandas\|numpy" requirements.txt) \
    && apk del build-dependencies
RUN apk add --no-cache libstdc++


FROM $BASE AS builder

WORKDIR /app

COPY napkon_string_matching napkon_string_matching
COPY README.md .
COPY pyproject.toml .

RUN pip install --upgrade build
RUN python -m build


FROM pandas-base

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt 

COPY main.py .

COPY --from=builder /app/dist/*.whl .
RUN pip install $(find . -name "*.whl")

ENTRYPOINT [ "python", "main.py" ]
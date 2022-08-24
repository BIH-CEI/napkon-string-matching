ARG BASE=python:3.10-alpine

FROM $BASE AS builder

WORKDIR /app

COPY napkon_string_matching napkon_string_matching
COPY README.md .
COPY pyproject.toml .

RUN pip install --upgrade build
RUN python -m build


FROM ghcr.io/bih-cei/napkon-string-matching-base:main

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

COPY --from=builder /app/dist/*.whl .
RUN pip install $(find . -name "*.whl")

ENTRYPOINT [ "python", "main.py" ]
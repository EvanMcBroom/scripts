FROM python:3.8-alpine

WORKDIR /opt
RUN apk add --no-cache git gcc libffi-dev musl-dev python3-dev && \
    python3 -m pip install -q virtualenv && \
    virtualenv -p python venv
ENV PATH="/opt/venv/bin:$PATH"
RUN git clone --depth 1 https://github.com/EvanMcBroom/scripts.git && \
    python3 -m pip install -q scripts/

FROM python:3.8-alpine
COPY --from=0 /opt/venv /opt/venv
COPY --from=0 /opt/scripts /opt/scripts
ENV PATH="/opt/venv/bin:$PATH"
ENTRYPOINT ["/bin/sh"]

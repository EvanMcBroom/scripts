FROM python:3.8-alpine
WORKDIR /opt
RUN apk add --no-cache git python3 python3-pip python3-venv && \
    virtualenv -p python venv
ENV PATH="/opt/venv/bin:$PATH"
RUN git clone --depth 1 https://github.com/EvanMcBroom/scripts.git && \
    python3 -m pip install scripts/

FROM python:3.8-alpine
COPY --from=0 /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENTRYPOINT ["/bin/sh"]
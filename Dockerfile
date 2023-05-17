FROM python:3.11-slim

WORKDIR /tmp
COPY dist/* .

RUN pip install --no-cache hypercorn "`ls sp_project*.whl`[web-server]"

EXPOSE 80
# EXPOSE 443

WORKDIR /home

COPY hypercorn-config.toml .

CMD ["hypercorn","-c","hypercorn-config.toml","sp_project.backend_server.main:app"]
FROM python:3.11-slim

WORKDIR /tmp
COPY dist/sp_project-0.1.0-py3-none-any.whl .

RUN pip install --no-cache hypercorn "sp_project-0.1.0-py3-none-any.whl[web-server]"

EXPOSE 80
# EXPOSE 443

WORKDIR /home

COPY hypercorn-config.toml .

CMD ["hypercorn","-c","hypercorn-config.toml","sp_project.backend_server.main:app"]
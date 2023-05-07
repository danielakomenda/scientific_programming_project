FROM python:3.11-slim

WORKDIR /tmp
COPY dist/sp_project-0.1.0-py3-none-any.whl .

RUN pip install --no-cache hypercorn "sp_project-0.1.0-py3-none-any.whl[web-server]"

EXPOSE 8000
# EXPOSE 443

WORKDIR /home

CMD ["hypercorn", "sp_project.backend_server.main:app"]
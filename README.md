# sp_project

## Server

### Dev enironment requirements

You need `docker` and `python3`.
Then, run
```bash
# install the "build" library into your local python env
pip install build 
```

### Build

From the top-level directory of the repository, run the following commands:
```bash
# build the sp_project library -> outputs a wheel into dist/
python -m build  --wheel

# create the docker image named "sp-project-server"
docker build . -t sp-project-server
```

### Test

To test the server, launch the server docker image using
```bash
docker run -p 8000:80 -t sp-project-server
```

Now you can surf to `localhost:8000` with your browser and test the server.

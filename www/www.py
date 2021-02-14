from . import app, Response, db

@app.view('/')
def homepage(req):
    print(dir(db))
    return Response('Homepage!')

# ---------------------------------------
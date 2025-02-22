from flask import Flask
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)

@app.route('/')
def hw():
    app.logger.info("GET request at /")
    return "<p>Hello World</p>"

if __name__ == "__main__":
    app.logger.info("Starting Flask App")
    app.run(port=9090, debug=False)
    app.logger.info("Flask App terminated")
from flask import Flask

import config
from hub_api import hub_api
from twilio_api import twilio_api

app = Flask('hot_hub_vs_virus')
app.register_blueprint(hub_api)
app.register_blueprint(twilio_api)
config.cache.init_app(app)


@app.before_request
def _db_connect():
    config.DATABASE.connect()


@app.teardown_request
def _db_close(exc):
    if not config.DATABASE.is_closed():
        config.DATABASE.close()


if __name__ == '__main__':
    app.run(debug=config.DEBUG)

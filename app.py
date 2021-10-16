"""Primary application.
"""
import json
import logging
import logging.config
import os
import sys

from flask import url_for, render_template, redirect, request
from i_xero2 import XeroInterfaceUI
from i_xero2.i_flask import FlaskInterface
from utils import jsonify, serialize_model


# initialize logging
# The SlackBot app doesn't handle logging in the same way.
# I tried to pass in a logger object from aracnid_logger,
# but it seems to disable all loggers
logging_filename = os.environ.get('LOGGING_CONFIG_FILE')
command_dir = os.path.dirname(sys.argv[0])
logging_dir = os.path.join(os.getcwd(), command_dir)
logging_path = os.path.join(os.getcwd(), logging_filename)
with open(logging_path, 'rt') as file:
    logging_config = json.load(file)
formatter = os.environ.get('LOGGING_FORMATTER')
logging_config['handlers']['console']['formatter'] = formatter
logging.config.dictConfig(logging_config)

env_str = os.environ.get('LOG_UNHANDLED_EXCEPTIONS')
LOG_UNHANDLED_EXCEPTIONS = env_str.lower() in ('true', 'yes') if env_str else False

# configure flask application
flask_app = FlaskInterface(__name__).get_app()

# configure xero application
xero_app = XeroInterfaceUI(flask_app)


@flask_app.route("/")
def index():
    xero_access = dict(xero_app.obtain_xero_oauth2_token() or {})
    return render_template(
        "code.html",
        title="Home | oauth token",
        code=jsonify(xero_access),
    )

@flask_app.route("/login")
def login():
    redirect_url = url_for("oauth_callback", _external=True)
    response = xero_app.oauth_app.authorize(callback_uri=redirect_url)
    return response

@flask_app.route("/callback")
def oauth_callback():
    try:
        response = xero_app.oauth_app.authorized_response()
    except Exception as e:
        print(e)
        raise
    # todo validate state value
    if response is None or response.get("access_token") is None:
        return "Access denied: response=%s" % response
    xero_app.store_xero_oauth2_token(response)
    return redirect(url_for("index", _external=True))


@flask_app.route("/logout")
def logout():
    xero_app.store_xero_oauth2_token(None)
    return redirect(url_for("index", _external=True))


@flask_app.route("/refresh-token")
def refresh_token():
    xero_token = xero_app.obtain_xero_oauth2_token()
    new_token = xero_app.refresh_token()

    return render_template(
        "code.html",
        title="Xero OAuth2 token",
        code=jsonify({"Old Token": xero_token, "New token": new_token}),
        sub_title="token refreshed",
    )

@flask_app.route("/tenants")
def tenants():
    available_tenants = xero_app.get_tenants()

    if available_tenants is None:
        return redirect(url_for("login", _external=True))

    return render_template(
        "code.html",
        title="Xero Tenants",
        code=jsonify(available_tenants),
    )
    
@flask_app.route("/invoices")
def get_invoices():
    invoices = xero_app.get_invoices()

    if invoices is None:
        return redirect(url_for("login", _external=True))

    code = serialize_model(invoices)
    sub_title = "Total invoices found: {}".format(len(invoices.invoices))

    return render_template(
        "code.html", title="Invoices", code=code, sub_title=sub_title
    )


# start the app locally
if __name__ == '__main__':
    flask_app.run(host='localhost', port=5000)

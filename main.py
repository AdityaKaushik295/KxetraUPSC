from flask import Flask, request, redirect, make_response, jsonify, session
import secrets
import httpx
from oauthlib.oauth2 import WebApplicationClient
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Ensure you have a strong secret key for session management

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Notion OAuth credentials
client_id = "client_id_hehe"
client_secret = "client_secret_hehe"
redirect_uri = "http://localhost:3000/redirect"


class NotionAppClient(WebApplicationClient):
    def __init__(self, client_id, client_secret, **kwargs):
        super().__init__(client_id, **kwargs)
        self.client_secret = client_secret
        self.token_url = "https://api.notion.com/v1/oauth/token"

    def login_link(self, redirect_uri, state):
        base_url = "https://api.notion.com/v1/oauth/authorize"
        return self.prepare_request_uri(base_url, redirect_uri=redirect_uri, state=state)

    def fetch_token(self, code):
        token_request = self.token_url
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        response = httpx.post(token_request, json=body)

        if response.status_code != 200:
            logging.error(f"Token exchange failed: {response.text}")
            raise Exception("Failed to exchange token")

        return response.json()  # Return the parsed token response


# Initialize Notion OAuth client
notion_oauth_client = NotionAppClient(client_id=client_id, client_secret=client_secret)


@app.route('/login')
def login():
    # Generate a secure state token
    state = secrets.token_urlsafe(16)

    # Store the state in the session
    session['oauth_state'] = state
    logging.debug(f"Setting session oauth_state: {state}")

    # Create the login URL
    login_url = f"https://api.notion.com/v1/oauth/authorize?response_type=code&client_id=10ed872b-594c-804f-a0c3-0037d3755867&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fredirect&state={state}"

    logging.debug(f"Redirecting to login URL: {login_url}")

    return redirect(login_url)


@app.route('/redirect')
def oauth_redirect():
    logging.debug(f"Cookies received on redirect: {request.cookies}")

    # Get the state and code from the request
    returned_state = request.args.get('state')
    code = request.args.get('code')

    # Retrieve the stored state from the session
    stored_state = session.get('oauth_state')
    logging.debug(f"Returned State: {returned_state}")
    logging.debug(f"Stored State: {stored_state}")

    # Check if the state matches to avoid CSRF
    if returned_state != stored_state:
        logging.error(f"State mismatch: expected {stored_state}, got {returned_state}")
        return "State mismatch! Possible CSRF attack detected.", 400

    # Proceed to exchange the authorization code for the access token
    try:
        token = notion_oauth_client.parse_response(code, redirect_uri)
        session['oauth_token'] = token  # Store token in session
        return jsonify({"message": "Login successful!"})
    except Exception as e:
        return f"Failed to exchange code: {str(e)}", 400


# Ensure you clear the state after redirect to prevent reuse
@app.after_request
def after_request(response):
    session.pop('oauth_state', None)  # Clear the state after the redirect
    return response


@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect('/login'))
    resp.set_cookie('oauth_state', '', expires=0)
    logging.debug("Logged out and cleared session.")
    return resp


if __name__ == '__main__':
    app.run(port=3000, debug=True,threaded=False)

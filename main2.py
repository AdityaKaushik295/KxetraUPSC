from flask import Flask, request, redirect, make_response, jsonify, session
import secrets
import httpx
from oauthlib.oauth2 import WebApplicationClient
import logging
import os

app = Flask(__name__)

# Configure Flask's built-in session with a fixed SECRET_KEY
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_fixed_development_secret_key')  # Use a strong, fixed key in production
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Optionally, set SESSION_COOKIE_SECURE to True in production with HTTPS
# app.config['SESSION_COOKIE_SECURE'] = True

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Notion OAuth credentials
client_id = "client_id_hehe"
client_secret = "client_secret_hehe" # Use environment variable in production
redirect_uri = "http://localhost:3000/redirect"  # Use 'localhost' as per Notion's requirement

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

        # Send form data instead of JSON
        response = httpx.post(token_request, data=body)

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
    login_url = notion_oauth_client.login_link(redirect_uri, state)

    logging.debug(f"Redirecting to login URL: {login_url}")

    return redirect(login_url)

@app.route('/redirect')
def oauth_redirect():
    logging.debug(f"Cookies received on redirect: {request.cookies}")

    # Log entire session data for debugging
    logging.debug(f"Session data: {dict(session)}")

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

    # Clear the state after successful validation to prevent reuse
    session.pop('oauth_state', None)

    # Proceed to exchange the authorization code for the access token
    try:
        token = notion_oauth_client.fetch_token(code)
        session['oauth_token'] = token  # Store token in session
        logging.debug(f"Stored oauth_token in session: {token}")
        return jsonify({"message": "Login successful!", "token": token})
    except Exception as e:
        logging.error(f"Failed to exchange code: {str(e)}")
        return f"Failed to exchange code: {str(e)}", 400

@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect('/login'))
    logging.debug("Logged out and cleared session.")
    return resp

@app.route('/session')
def display_session():
    # For debugging purposes only. Remove or secure in production.
    return jsonify(dict(session))

if __name__ == '__main__':
    # Access the app via localhost to match redirect_uri
    app.run(host='localhost', port=3000, debug=True)

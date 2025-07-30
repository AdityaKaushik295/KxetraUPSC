import json
from flask import Flask, request, redirect, make_response, jsonify, session, render_template, url_for
import secrets
import httpx
from oauthlib.oauth2 import WebApplicationClient
from notion_client import Client as NotionClient
from mailing import *
import mysql.connector
import logging
import os
import datetime
import random
from newsfeed import buildnewsfeed
from videofeed import buildvideofeed, buildvideosummary
from notesgen import generate_mcqs_from_text

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
client_id = ""
client_secret = ""
redirect_uri = "https://thecodeworks.in/kxetra/redirect"  # Use 'localhost' as per Notion's requirement

dailyNotes = []
dailyNotesv = []
book_files = ['book1.json']
quiz_files=['quiz.json']
username="Adi A"
profilepic=""

books = []
json_data=[]
quizzes=[]

for book_file in book_files:
    with open(book_file, 'r') as f:
        book = json.load(f)
        books.append(book)

for quiz_file in quiz_files:
    with open(quiz_file, 'r') as f:
        quiz = json.load(f)
        quizzes.append(quiz)




#################################### LOGIN SYSTEMS ############################################################
class NotionAppClient(WebApplicationClient):
    def __init__(self, client_id, client_secret, **kwargs):
        super().__init__(client_id, **kwargs)
        self.client_secret = client_secret
        self.token_url = "https://api.notion.com/v1/oauth/token"

    def login_link(self, redirect_uri, state):
        base_url = "https://api.notion.com/v1/oauth/authorize"
        return self.prepare_request_uri(base_url, redirect_uri=redirect_uri, state=state)

    def fetch_token(self, code, redirect_uri):
        token_request = self.token_url
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
    
        auth = (self.client_id, self.client_secret)
    
        response = httpx.post(token_request, data=body, auth=auth)
    
        if response.status_code != 200:
            logging.error("Token exchange failed: %s", response.text.encode("ascii", "replace").decode())
            raise Exception("Failed to exchange token")
    
        return response.json()


# Initialize Notion OAuth client
notion_oauth_client = NotionAppClient(client_id=client_id, client_secret=client_secret)

def check_new_user_sql(email):
    host="localhost"
    user = "thecodew_kxetra_user"
    password = "thecodew_kxetra_user"
    database = "thecodew_kxetra_db"

    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
    ssl_disabled=True

    )

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email_id LIKE %s",(email))

    acc = cursor.fetchone()
    cursor.close()
    connection.close()

    if acc:
        return "Account Exists Login"
    else:
        return "Create Account"

def login_sql(email,passw):
    host="localhost"
    user = "thecodew_kxetra_user"
    password = "thecodew_kxetra_user"
    database = "thecodew_kxetra_db"

    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
    ssl_disabled=True

    )

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email_id LIKE %s and password LIKE %s",(email,passw))

    acc = cursor.fetchone()
    cursor.close()
    connection.close()

    if acc:
        session['email'] = email
        session['id_logged']=acc[0]
        session['name'] = acc[3]
        session['profile_picture_url'] = acc[4]
        session['auth_token_user']=acc[5]
        session['score']=acc[6]
        session['parent_page_notes_token']=acc[7]
        return "logged in"

    else:
        return "incorrect credentials"







def create_new_user(email,passw):
    host="localhost"
    user = "thecodew_kxetra_user"
    password = "thecodew_kxetra_user"
    database = "thecodew_kxetra_db"


    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
    ssl_disabled=True

    )

    cursor = connection.cursor()
    cursor.execute("INSERT INTO users(email_id,password) values(%s,%s)",(email,passw))
    connection.commit()
    cursor.close()
    connection.close()


def create_verification_code():
    return random.randint(1000,9999)




###########################################################################################





articles=buildnewsfeed()
videos=buildvideofeed("https://www.youtube.com/feeds/videos.xml?channel_id=UC7Q0EfPzTwtanMVSWuK_QXA")


@app.route("/")
def land():
    session['register_message'] = ""
    session['verification_code'] = None
    session['email_temp'] = ""
    session['password_temp'] = ""
    session['verify_message'] = ""
    session['message_after_new_account'] = ""
    session['login_message'] = ""

    session['username_logged'] = ""
    session['id_logged'] = ""
    session['fp_email'] = ""
    session['fp_user_id'] = ""
    return render_template("land.html")


@app.route("/register")
def register():
    return render_template("register.html",message=session['register_message'])


@app.route("/process_register", methods=['POST'])
def new_user():
      email_input = request.form['email id']
      password_input=request.form['password']
      confirm_password_input = request.form['confirm_password']
      email_input_tuple=(email_input,)

      register_control = check_new_user_sql(email_input_tuple)

      if register_control == "Account Exists Login":
          session['register_message']="Email id already an account, login"
          return render_template("register.html", message=session['register_message'])
      elif register_control == "Create Account":
          if password_input == confirm_password_input:
              session['verification_code']=None
              session['email_temp'] = email_input
              session['password_temp'] = password_input
              code1=create_verification_code()
              session['verification_code'] = code1
              send_verification(email_input,code1)
              return render_template("verify_new.html",message=session['verify_message'])
          else:
              session['register_message'] = "Passwords don't match, try again"
              return render_template("register.html", message=session['register_message'])
      else:
          print("404")

@app.route("/verify_new",methods=['POST'])
def verify_new():
    code_input = request.form['code']

    if int(code_input)== int(session['verification_code']):
        create_new_user(session['email_temp'],session['password_temp'])
        session['message_after_new_account']="Account successfully created. Login in to your account"
        return redirect("register_notion")
    else:
        session['verify_message'] = "Incorrect code. Check again"
        return render_template("verify_new.html",message=session['verify_message'])


@app.route("/register_notion")
def register_notion():
    state = secrets.token_urlsafe(16)

    # Store the state in the session
    session['oauth_state'] = state
    logging.debug(f"Setting session oauth_state: {state}")

    # Create the login URL
    login_url = notion_oauth_client.login_link(redirect_uri, state)

    logging.debug(f"Redirecting to login URL: {login_url}")

    return redirect(login_url)



@app.route("/login")
def login():
    if not session['login_message'] :
        session['login_message'] = ""
    return render_template("login.html", message=session['login_message'])

@app.route("/process_login", methods=['POST'])
def process_login():
    email_input = request.form['email_login']
    session['email_temp'] = email_input
    password_input = request.form['password_login']
    #email_input_tuple = (email_input,password_input)
    login_control = login_sql(email_input,password_input)

    if login_control == "logged in":

        host="localhost"
        user = "thecodew_kxetra_user"
        password = "thecodew_kxetra_user"
        database = "thecodew_kxetra_db"
    
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
        ssl_disabled=True
    
        )

        cursor = connection.cursor()


        query = """
            SELECT *
            FROM users
            WHERE email_id = %s
              AND auth_token IS NOT NULL
              AND parent_page_notes_token IS NOT NULL;
            """

        cursor.execute(query, (email_input,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            host="localhost"
            user = "thecodew_kxetra_user"
            password = "thecodew_kxetra_user"
            database = "thecodew_kxetra_db"
        
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
            ssl_disabled=True
        
            )
            cursor = connection.cursor()

            # SQL query to fetch auth_token and parent_page_notes_token for a specific email_id
            query = """
                SELECT auth_token, parent_page_notes_token
                FROM users
                WHERE email_id = %s
                """
            # Execute the query with the given email
            cursor.execute(query, (email_input,))

            # Fetch the result (if exists)
            result = cursor.fetchone()

            cursor.close()
            connection.close()
            session['auth_token'],session['parent_page_notes_token']=result
            return redirect("home")
        else:
            return redirect("register_notion")



    elif login_control == "incorrect credentials":
        session['login_message'] = "Incorrect credentials. Try again"
        return render_template("login.html", message=session['login_message'])
    else:
        return "404"

@app.route("/forgot_password")
def forgot_password():
    return render_template("change_password.html")

@app.route("/process_forgot_password",methods=["POST"])
def process_forgot_password():
    fp_email = request.form['fp_email']
    host="localhost"
    user = "thecodew_kxetra_user"
    password = "thecodew_kxetra_user"
    database = "thecodew_kxetra_db"

    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
    ssl_disabled=True

    )

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email_id LIKE %s", (fp_email,))

    acc = cursor.fetchone()
    cursor.close()
    connection.close()

    if acc:

        code1 = create_verification_code()
        session['verification_code'] = code1
        session['fp_email'] = fp_email
        session['fp_user_id'] = int(acc[0])
        send_forgot_password(fp_email, code1)
        return render_template("change_password_2.html")

    else:
        return render_template("change_password.html",message="Email not registered, don't scam")



@app.route("/process_forgot_password2",methods=["POST"])
def process_forgot_password2():
    fp_code= request.form['fp_code']
    fp_new_password = request.form['fp_new_password']
    fp_confirm = request.form['fp_new_confirm']
    print(fp_code)
    print(session['verification_code'])
    print(session['fp_email'])
    print(session['fp_user_id'])
    print(type(session['fp_user_id']))
    if int(fp_code) == int(session['verification_code']) and fp_new_password == fp_confirm:
        print("1")
        host="localhost"
        user = "thecodew_kxetra_user"
        password = "thecodew_kxetra_user"
        database = "thecodew_kxetra_db"
    
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
        ssl_disabled=True
    
        )

        cursor = connection.cursor()

        print(session['fp_user_id'])

        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (fp_new_password,session['fp_user_id']))

        cursor.close()
        connection.commit()
        connection.close()
        return "success"

    elif fp_new_password != fp_confirm:
        print("2")
        return render_template("change_password_2.html",message="Passwords don't match")
    elif int(fp_code) != int(session['verification_code']):
        print("3")
        return render_template("change_password_2.html", message="Wrong verification code")
    else:
        return render_template("home.html")




"""
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


"""

@app.route('/redirect')
def oauth_redirect():
    def safe_str(obj):
        """Safely convert object to string, handling Unicode properly"""
        return str(obj).encode('utf-8', 'replace').decode('utf-8')

    try:
        # Logging with safe string conversion
        logging.debug(f"Cookies received on redirect: {safe_str(request.cookies)}")
        logging.debug(f"Session data: {safe_str(dict(session))}")

        # Get the state and code from the request
        returned_state = request.args.get('state')
        code = request.args.get('code')

        # Retrieve the stored state from the session
        stored_state = session.get('oauth_state')
        logging.debug(f"Returned State: {safe_str(returned_state)}")
        logging.debug(f"Stored State: {safe_str(stored_state)}")

        # Check if the state matches to avoid CSRF
        if returned_state != stored_state:
            error_msg = f"State mismatch: expected {safe_str(stored_state)}, got {safe_str(returned_state)}"
            logging.error(error_msg)
            return "State mismatch! Possible CSRF attack detected.", 400

        # Clear the state after successful validation to prevent reuse
        session.pop('oauth_state', None)

        # Proceed to exchange the authorization code for the access token
        token = notion_oauth_client.fetch_token(code, redirect_uri)
        
        # Safely extract values with proper encoding handling
        user_info = token.get('owner', {}).get('user', {})
        username = safe_str(user_info.get('name', ''))
        profilepic = safe_str(user_info.get('avatar_url', ''))
        auth_token = safe_str(token.get('access_token', ''))
        template_page_id = safe_str(token.get('duplicated_template_id', ''))

        # Database operations
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="thecodew_kxetra_user",
                password="thecodew_kxetra_user",
                database="thecodew_kxetra_db",
                ssl_disabled=True,
                charset='utf8mb4'  # Ensure UTF-8 support in MySQL
            )

            cursor = connection.cursor()
            query = """
            UPDATE users
            SET auth_token = %s, parent_page_notes_token = %s, name = %s, profile_picture_url = %s
            WHERE email_id = %s
            """
            cursor.execute(query, (
                auth_token,
                template_page_id,
                username,
                profilepic,
                session.get('email_temp')
            ))
            connection.commit()

        except Exception as db_error:
            logging.error(f"Database error: {safe_str(db_error)}")
            return "Database operation failed", 500
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

        # Store token in session
        session['oauth_token'] = token
        session['username'] = username
        session['profile_picture_url'] = profilepic
        
        return redirect(url_for('home'))

    except Exception as e:
        error_msg = safe_str(e)
        logging.error(f"OAuth redirect failed: {error_msg}")
        return f"Authentication failed: {error_msg}", 500


@app.route("/home")
def home():




    return render_template('home3.html', articles=articles, videos=videos,books=books,username=username,profilepic=profilepic, enumerate=enumerate)

@app.route("/newsfeed")
def newsfeed():
    return render_template('newsfeed.html', articles=articles,enumerate=enumerate)

@app.route("/videofeed")
def videofeed():
    return render_template('videofeed.html', videos=videos,enumerate=enumerate)

@app.route("/library")
def library():
    return render_template('library.html',books=books ,enumerate=enumerate)

@app.route("/tests")
def tests():
    return render_template('tests.html',books=books ,enumerate=enumerate)

@app.route("/interview")
def interview():
    return render_template("interview.html")



@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect('/login'))
    logging.debug("Logged out and cleared session.")
    return resp

"""
@app.route('/session')
def display_session():
    # For debugging purposes only. Remove or secure in production.
    return jsonify(dict(session))

"""

@app.route('/updatenotes', methods=['POST'])
def update_notes():
    index = int(request.args.get('index', -1))
    if 0 <= index < len(articles):
        if articles[index] not in dailyNotes:
            dailyNotes.append(articles[index])
    return jsonify({'status': 'success', 'notes_count': len(dailyNotes)})

# Route for saving videos to notes
@app.route('/updatenotesv', methods=['POST'])
def update_notesv():
    index = int(request.args.get('index', -1))
    if 0 <= index < len(videos):
        if videos[index] not in dailyNotesv:
            dailyNotesv.append(videos[index])
    return jsonify({'status': 'success', 'notes_count': len(dailyNotesv)})

@app.route('/create_pages', methods=['POST'])
def create_page():
    print("ping heheh1")
    global dailyNotes, dailyNotesv
    token_data = session['auth_token']
    print(token_data)

    if not token_data:
        return jsonify({"status": "error", "message": "Not logged in"}), 303

    # Use async version of Notion client
    notion = NotionClient(auth=token_data)

    datetoday = datetime.datetime.now()
    titleDate = datetoday.strftime("%A") + ", " + datetoday.strftime("%d") + " " + datetoday.strftime(
        "%B") + ", " + datetoday.strftime("%Y")

    choiceControl = 0
    try:
        pages = notion.search(filter={"property": "object", "value": "page"})  # await the search
        for page in pages["results"]:
            if page["properties"]["title"]["title"][0]["plain_text"] == titleDate:
                page_id1 = page["id"]
                choiceControl = 1
        if choiceControl == 0:
            page_id1=session['parent_page_notes_token']

        print(page_id1,choiceControl)

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": f"Failed to retrieve pages: {str(e)}"})

    noteBlocks = []

    # Handle dailyNotes (News)
    if dailyNotes:
        for item in dailyNotes:
            titleBlock = {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": item["title"]}}
                    ]
                }
            }

            summaryBlock = {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": item["summary"]}}
                    ]
                }
            }

            noteBlocks.append(titleBlock)
            noteBlocks.append(summaryBlock)

    # Handle dailyNotesv (Videos)
    if dailyNotesv:
        for item in dailyNotesv:
            video_id = item["video_link"].split("=")[1]
            page_blocks = buildvideosummary(video_id)
            noteBlocks.extend(page_blocks)  # Append the video blocks to the existing noteBlocks

    # New page or content structure (combined)
    new_page = {
        "parent": {"type": "page_id", "page_id": page_id1},
        "properties": {
            "title": [
                {
                    "type": "text",
                    "text": {"content": titleDate}
                }
            ]
        },
        "children": noteBlocks
    }

    new_content = {
        "children": noteBlocks,
    }

    # Attempt to create or append content
    try:
        if choiceControl == 0 and (dailyNotes or dailyNotesv):
            response = notion.pages.create(**new_page)
            dailyNotes.clear()
            dailyNotesv.clear()
        elif choiceControl == 1 and (dailyNotes or dailyNotesv):
            notion.blocks.children.append(block_id=page_id1, children=noteBlocks)  # append to existing page
            dailyNotes.clear()
            dailyNotesv.clear()

        return jsonify({"status": "success", "message": "Notes successfully created!"})

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to create notes: {str(e)}"})


@app.route('/books/<book_name>')
def book_page(book_name):
    # Find the book in the list by book_name
    book = next((b for b in books if b['book_name'] == book_name), None)

    if not book:
        return "Book not found", 404

    return render_template('book_page.html', book_name=book_name, chapters=book['chapters'],enumerate=enumerate)


@app.route('/books/<book_name>/<int:chapter_id>')
def chapter_page(book_name, chapter_id):
    # Find the book in the list by book_name
    global json_data
    book = next((b for b in books if b['book_name'] == book_name), None)

    quiz=next((b for b in quizzes if b['book_name'] == book_name), None)

    if not book:
        return "Book not found", 404

    # Check if the chapter_id is within the range of available chapters
    if chapter_id < 0 or chapter_id >= len(book['chapters']):
        return "Chapter not found", 404
    if chapter_id >= 0 and  chapter_id < len(quiz['chapters']):
        json_data=quiz['chapters'][chapter_id]['mcqs']


    chapter = book['chapters'][chapter_id]  # Access chapter by index
    return render_template('chapter_page.html', book_name=book_name, chapter=chapter,enumerate=enumerate)


@app.route("/chapterquiz")
def chapterquiz():
    return render_template('quiz.html', total_questions=len(json_data))


def get_notion_page_text_by_title(notion,parent_page_id, title):

        # Retrieve the page's content
    page_content = notion.blocks.children.list(parent_page_id)
    text_content = ''

    for block in page_content['results']:
        # Only retrieve paragraph-type blocks
        if block['type'] == 'paragraph':
            text_content += block['paragraph']['text'][0]['plain_text'] + '\n'

    print(page_content)
    return text_content.strip()


@app.route("/dailytest")
def dailyTest():
    token_data = session['auth_token']
    global json_data

    if not token_data :
        return jsonify({"error": "OAuth token not found"}), 401

    try:
        notion = NotionClient(auth=token_data)
    except Exception as e:
        return jsonify({"error": f"Notion Client initialization failed: {str(e)}"}), 500

    # Generate the title for today's date
    datetoday = datetime.datetime.now()
    titleDate = datetoday.strftime("%A") + ", " + datetoday.strftime("%d") + " " + datetoday.strftime(
        "%B") + ", " + datetoday.strftime("%Y")

    page_title = titleDate

    # Step 1: Search for the page
    try:
        pages = notion.search(filter={"property": "object", "value": "page"})

        parent_page_id_dt = None
        for page in pages["results"]:
            if "properties" in page and "title" in page["properties"]:
                title_property = page["properties"]["title"]
                if title_property["title"]:
                    # Concatenate all plain_text parts in title
                    page_title_text = ''.join([t['plain_text'] for t in title_property["title"]])
                    if page_title_text.strip() == page_title:
                        parent_page_id_dt = page["id"]
                        break

        if not parent_page_id_dt:
            return jsonify({"error": "No page found with today's date title"}), 404

    except Exception as e:
        return jsonify({"error": f"Error searching for the page: {str(e)}"}), 500

    # Step 2: Retrieve page content and extract text
    try:
        text_content = ""

        # Recursive function to handle nested blocks
        def extract_text(blocks):
            nonlocal text_content
            for block in blocks:
                block_type = block.get('type')
                if not block_type:
                    continue

                if block_type == 'paragraph' and 'rich_text' in block['paragraph']:
                    for part in block['paragraph']['rich_text']:
                        text_content += part.get('plain_text', '') + " "
                    text_content += "\n"

                elif block_type == 'bulleted_list_item' and 'rich_text' in block['bulleted_list_item']:
                    bullet = "- "  # Bullet point symbol
                    for part in block['bulleted_list_item']['rich_text']:
                        text_content += bullet + part.get('plain_text', '') + " "
                    text_content += "\n"

                elif block_type == 'numbered_list_item' and 'rich_text' in block['numbered_list_item']:
                    number = "1. "  # Numbered list symbol
                    for part in block['numbered_list_item']['rich_text']:
                        text_content += number + part.get('plain_text', '') + " "
                    text_content += "\n"

                elif block_type in ['heading_1', 'heading_2', 'heading_3'] and 'rich_text' in block[block_type]:
                    if block_type == 'heading_1':
                        prefix = "# "
                    elif block_type == 'heading_2':
                        prefix = "## "
                    elif block_type == 'heading_3':
                        prefix = "### "

                    for part in block[block_type]['rich_text']:
                        text_content += prefix + part.get('plain_text', '') + "\n"

                elif block_type == 'to_do' and 'rich_text' in block['to_do']:
                    checkbox = "[ ] "  # To-do checkbox symbol
                    for part in block['to_do']['rich_text']:
                        text_content += checkbox + part.get('plain_text', '') + "\n"

                elif block_type == 'toggle' and 'rich_text' in block['toggle']:
                    toggle_text = "▶ "  # Toggle symbol
                    for part in block['toggle']['rich_text']:
                        text_content += toggle_text + part.get('plain_text', '') + "\n"

                # Handle other block types as needed

                # If the block has children, recursively extract their text
                if block.get('has_children'):
                    children = notion.blocks.children.list(block_id=block['id'])
                    extract_text(children['results'])

        # Initial fetch of page content
        page_content = notion.blocks.children.list(block_id=parent_page_id_dt, page_size=100)
        extract_text(page_content['results'])

        # Log the extracted text for debugging
        print("Extracted Text Content:")
        print(text_content)

        if not text_content.strip():
            return jsonify({"error": "No text content found in the page"}), 404

        # Step 3: Send text to Gemini API to generate MCQs
        mcq_json = generate_mcqs_from_text(text_content)
        json_data = json.loads(mcq_json)
        print(json_data)
        print(jsonify(json_data))
        print(len(json_data))
        return render_template('quiz.html', total_questions=len(json_data))

        # Return the generated MCQs
        #return jsonify(mcq_json)

    except Exception as e:
        return jsonify({"error": f"Error retrieving page content: {str(e)}"}), 500

@app.route("/weeklytest")
def weeklyTest():
    token_data = session['auth_token']
    global json_data

    if not token_data :
        return jsonify({"error": "OAuth token not found"}), 401

    try:
        notion = NotionClient(auth=token_data)
    except Exception as e:
        return jsonify({"error": f"Notion Client initialization failed: {str(e)}"}), 500

    # Generate date range for the past 7 days
    today = datetime.datetime.now()
    week_dates = [
        (today - datetime.timedelta(days=i)).strftime("%A, %d %B, %Y")
        for i in range(7)
    ]

    # Step 1: Search for the pages
    try:
        pages = notion.search(filter={"property": "object", "value": "page"})

        parent_page_ids_wt = []
        for page in pages["results"]:
            if "properties" in page and "title" in page["properties"]:
                title_property = page["properties"]["title"]
                if title_property["title"]:
                    page_title_text = ''.join([t['plain_text'] for t in title_property["title"]]).strip()
                    if page_title_text in week_dates:
                        parent_page_ids_wt.append(page["id"])

        if not parent_page_ids_wt:
            return jsonify({"error": "No pages found for the past week"}), 404

    except Exception as e:
        return jsonify({"error": f"Error searching for the pages: {str(e)}"}), 500

    # Step 2: Retrieve page content and extract text
    try:
        text_content = ""

        # Recursive function to handle nested blocks
        def extract_text(blocks):
            nonlocal text_content
            for block in blocks:
                block_type = block.get('type')
                if not block_type:
                    continue

                if block_type == 'paragraph' and 'rich_text' in block['paragraph']:
                    for part in block['paragraph']['rich_text']:
                        text_content += part.get('plain_text', '') + " "
                    text_content += "\n"

                elif block_type == 'bulleted_list_item' and 'rich_text' in block['bulleted_list_item']:
                    bullet = "- "  # Bullet point symbol
                    for part in block['bulleted_list_item']['rich_text']:
                        text_content += bullet + part.get('plain_text', '') + " "
                    text_content += "\n"

                elif block_type == 'numbered_list_item' and 'rich_text' in block['numbered_list_item']:
                    number = "1. "  # Numbered list symbol
                    for part in block['numbered_list_item']['rich_text']:
                        text_content += number + part.get('plain_text', '') + " "
                    text_content += "\n"

                elif block_type in ['heading_1', 'heading_2', 'heading_3'] and 'rich_text' in block[block_type]:
                    if block_type == 'heading_1':
                        prefix = "# "
                    elif block_type == 'heading_2':
                        prefix = "## "
                    elif block_type == 'heading_3':
                        prefix = "### "

                    for part in block[block_type]['rich_text']:
                        text_content += prefix + part.get('plain_text', '') + "\n"

                elif block_type == 'to_do' and 'rich_text' in block['to_do']:
                    checkbox = "[ ] "  # To-do checkbox symbol
                    for part in block['to_do']['rich_text']:
                        text_content += checkbox + part.get('plain_text', '') + "\n"

                elif block_type == 'toggle' and 'rich_text' in block['toggle']:
                    toggle_text = "▶ "  # Toggle symbol
                    for part in block['toggle']['rich_text']:
                        text_content += toggle_text + part.get('plain_text', '') + "\n"

                # Handle other block types as needed

                # If the block has children, recursively extract their text
                if block.get('has_children'):
                    children = notion.blocks.children.list(block_id=block['id'], page_size=100)
                    extract_text(children['results'])

        # Retrieve content from each page in the past week
        for parent_page_id in parent_page_ids_wt:
            page_content = notion.blocks.children.list(block_id=parent_page_id, page_size=100)
            extract_text(page_content['results'])

        # Log the extracted text for debugging
        print("Extracted Text Content for Weekly Test:")
        print(text_content)

        if not text_content.strip():
            return jsonify({"error": "No text content found in the pages"}), 404

        # Step 3: Send text to Gemini API to generate MCQs
        mcq_response = generate_mcqs_from_text(text_content)

        # Debug: Print the Gemini API response
        print("Response from Gemini API:")
        print(mcq_response)

        # Log the type of mcq_response
        print(f"Type of mcq_response: {type(mcq_response)}")

        # Handle the response based on its type
        if isinstance(mcq_response, str):
            # If it's a JSON string, parse it
            try:
                json_data = json.loads(mcq_response)
                print("Decoded JSON successfully")
            except json.JSONDecodeError as json_err:
                print(f"JSON decoding error: {json_err}")
                print(f"Problematic JSON: {mcq_response}")
                return jsonify({"error": f"JSON decoding failed: {str(json_err)}"}), 500
        elif isinstance(mcq_response, list) or isinstance(mcq_response, dict):
            # If it's already a Python object, use it directly
            json_data = mcq_response
        else:
            # Unexpected format
            return jsonify({"error": "Unexpected response format from Gemini API"}), 500

        # Ensure that json_data is a list
        if not isinstance(json_data, list):
            return jsonify({"error": "MCQ data is not a list"}), 500

        # Return the generated MCQs (you can adjust this as needed)
        return render_template('quiz.html', total_questions=len(json_data))

    except Exception as e:
        return jsonify({"error": f"Error retrieving page content: {str(e)}"}), 500

@app.route("/generate_mock_paper")
def generate_mock_paper():
    # Call the function that generates the mock paper PDF
    pdf_path = "paper_generator_files/question_paper/paper1.pdf"  # Ensure this is the correct path

    # Ensure the file exists before sending
    if not os.path.exists(pdf_path):
        return "Mock Paper generation failed!", 500

    # Send file as a downloadable attachment
    return send_file(pdf_path, as_attachment=True, download_name="Mock_Paper.pdf")

@app.route('/get_question/<int:question_id>')
def get_question(question_id):
    global json_data
    if 0 <= question_id < len(json_data):
        print(json_data[question_id])
        print(question_id)
        return jsonify(json_data[question_id])
    else:
        return jsonify({"error": "Invalid question ID"})

@app.route('/check_answer', methods=['POST'])
def check_answer():
    global json_data
    data = request.get_json()
    question_id = data['question_id']
    selected_answer = data['selected_answer']

    correct_answer = json_data[question_id]['answer']  # Corrected from `questions` to `quiz_data`

    if selected_answer == correct_answer:
        return jsonify({'is_correct': True})
    else:
        return jsonify({'is_correct': False})







if __name__ == '__main__':
    # Access the app via localhost to match redirect_uri
    app.run(host='localhost', port=3000, debug=True)

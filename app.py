from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'chat-app'

def get_conn():
    mysql = pymysql.connect(
    host = app.config['MYSQL_HOST'],
    user = app.config['MYSQL_USER'],
    password= app.config['MYSQL_PASSWORD'],
    db = app.config['MYSQL_DB']
    )
    return mysql


def check_username(username):
    connection = get_conn()
    cursor = connection.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"

    try:
        cursor.execute(query)
        result = cursor.fetchone()
    except Exception as e:
        print("Error executing query:", e)
        return True  # Assuming an error means the username is already in use

    cursor.close()
    connection.close()

    if result:
        return True  # Username is already in use
    else:
        return False  # Username is not in use


def get_login(username, password):
    connection = get_conn()
    cursor = connection.cursor()

    # Assuming you have a table named 'students' with columns 'student_id' and 'name'
    query = f"SELECT * FROM users WHERE username = '{username}' and password = '{password}'"
    try:
        cursor.execute(query)
        result = cursor.fetchone()
    except Exception:
        return False


    cursor.close()
    connection.close()

    if result:
        return result
    else:
        return None
    
@app.route('/create_chat', methods=['POST'])
def create_chat():
    try:
        # Get data from request
        data = request.json
        user1_id = data['user1_id']
        user2_id = data['user2_id']
        # Connect to MySQL
        connection = get_conn()
        cursor = connection.cursor()

        if not user1_id or not user2_id:
            return jsonify({'error': 'user1_id and user2_id are required'}), 400
        
        change_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert data into the table
        sql = "INSERT INTO chats (user1_id, user2_id, change_date) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user1_id, user2_id, change_date))

        # Commit the transaction
        connection.commit()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify({'status': True, 'message': 'Chat created successfully!'})
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 404


@app.route('/register', methods=['POST'])
def register():
    try:
        # Get data from request
        data = request.json
        username = data['username']
        password = data['password']
        # Connect to MySQL
        connection = get_conn()
        cursor = connection.cursor()

        if check_username(username):
            return jsonify({'status': False, 'error': "Username is already in use."})

        # Insert data into the table
        sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(sql, (username, password))

        # Commit the transaction
        connection.commit()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify({'status': True, 'message': 'Account created successfully!'})
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)})

# Flask route to handle requests for getting student name
@app.route('/login', methods=['GET'])
def login():
    username = request.args.get('username')
    password = request.args.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and Password are required'}), 400

    status  = get_login(username, password)


    if status:
        response = jsonify({'status': True , "id": status[0]})
    else:
        response = jsonify({'status': False, "error" : 'Invalid username or password'})

    return response

@app.route('/get_chats', methods=['GET'])
def get_chats():
    user_id = request.args.get('user_id')
    connection = get_conn()

    try:
        with connection.cursor() as cursor:
            # Execute the SQL query
            cursor.execute(f'SELECT * FROM chats WHERE user1_id = {user_id} or user2_id = {user_id}')

            # Fetch all the results
            chats = cursor.fetchall()

    finally:
        connection.close()

    formatted_users = [{'id': chat[0], 'user1_id': chat[1], "user2_id" : chat[2], "change_date": chat[3], "last_message" : chat[4] } for chat in chats] 

    return jsonify(formatted_users)

@app.route('/get_users', methods=['GET'])
def get_users():
    connection = get_conn()

    try:
        with connection.cursor() as cursor:
            # Execute the SQL query
            cursor.execute('SELECT id, username FROM users')

            # Fetch all the results
            users = cursor.fetchall()

    finally:
        connection.close()

    formatted_users = [{'id': user[0], 'username': user[1]} for user in users] 

    return jsonify(formatted_users)

@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        # Get data from request
        data = request.json
        chat_id = data['chatId']
        sender_id = data['senderId']
        content = data['content']
        # Connect to MySQL
        connection = get_conn()
        cursor = connection.cursor()

        # Insert data into the messages table
        sql_insert_message = "INSERT INTO messages (chat_id, sender_id, content) VALUES (%s, %s, %s)"
        cursor.execute(sql_insert_message, (chat_id, sender_id, content))

        # Update change_date and last_message in the chats table
        change_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql_update_chat = "UPDATE chats SET change_date = %s, last_message = %s WHERE id = %s"
        cursor.execute(sql_update_chat, (change_date, content, chat_id))

        # Commit the transaction
        connection.commit()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify({'status': True, 'message': 'Message sent successfully!'})
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)})

    
@app.route('/get_messages', methods=['GET'])
def get_messages():
    chat_id = request.args.get('chat_id')
    connection = get_conn()

    try:
        with connection.cursor() as cursor:
            # Execute the SQL query
            cursor.execute(f'SELECT * FROM messages WHERE chat_id = {chat_id}')

            # Fetch all the results
            messages = cursor.fetchall()

    finally:
        connection.close()

    formatted_messages = [{'id': message[0], 'chat_id': message[1], "sender_id" : message[2], "content": message[3], "timestamp": message[4] } for message in messages] 

    return jsonify(formatted_messages)

@app.before_request
def before_request():
    if request.method == "OPTIONS":
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

if __name__ == '__main__':
    app.run(debug= True, port= 3000)
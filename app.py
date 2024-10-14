from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime

app = Flask(__name__)

# Webex API base URL
WEBEX_BASE_URL = "https://webexapis.com/v1"

# Custom filter to format dates
@app.template_filter('format_date')
def format_date(value, format='%Y-%m-%d %H:%M:%S'):
    try:
        date_obj = datetime.fromisoformat(value)
        return date_obj.strftime(format)
    except ValueError:
        return "Invalid Date"
    
# Register the filter
app.jinja_env.filters['format_date'] = format_date

# Route for the home page where the user enters the Webex token
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        access_token = request.form['access_token']
        return redirect(url_for('menu', access_token=access_token))
    return render_template('index.html')

# Route for the main menu
@app.route('/menu/<access_token>', methods=['GET'])
def menu(access_token):
    return render_template('menu.html', access_token=access_token)

# Test connection to the Webex server
@app.route('/test_connection/<access_token>', methods=['GET'])
def test_connection(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(f"{WEBEX_BASE_URL}/people/me", headers=headers)
    
    if response.status_code == 200:
        message = "Connection to Webex server successful!"
    else:
        message = "Failed to connect to Webex server."
    
    return render_template('test_connection.html', message=message, access_token=access_token)

# Display user information with avatar
@app.route('/user_info/<access_token>', methods=['GET'])
def user_info(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(f"{WEBEX_BASE_URL}/people/me", headers=headers)
    
    if response.status_code == 200:
        user_info = response.json()
        user_email = user_info.get('emails', ['No email available'])[0]
        display_name = user_info.get('displayName', 'No name available')
        avatar_url = user_info.get('avatar', None)
    else:
        user_info = None
        user_email = 'Error retrieving email'
        display_name = 'Error retrieving name'
        avatar_url = None
    
    return render_template(
        'user_info.html', 
        user_info=user_info, 
        user_email=user_email, 
        display_name=display_name, 
        avatar_url=avatar_url,
        access_token=access_token
    )

# List 5 rooms and handle message sending
@app.route('/rooms/<access_token>', methods=['GET', 'POST'])
def rooms(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(f"{WEBEX_BASE_URL}/rooms", headers=headers)
    rooms = response.json().get('items', [])[:5] if response.status_code == 200 else []
    
    if request.method == 'POST':
        room_id = request.form['room_id']
        message = request.form['message']
        message_response = send_message_to_room(access_token, room_id, message)
        return redirect(url_for('message_confirmation', access_token=access_token, room_id=room_id, user_message=message))
    
    return render_template('rooms.html', rooms=rooms, access_token=access_token)

# Message confirmation page
@app.route('/message_confirmation/<access_token>/<room_id>/<user_message>', methods=['GET'])
def message_confirmation(access_token, room_id, user_message):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(f"{WEBEX_BASE_URL}/rooms/{room_id}", headers=headers)
    
    if response.status_code == 200:
        room_title = response.json().get('title', 'Unknown Room')
    else:
        room_title = 'Unknown Room'
    
    return render_template('message.html', access_token=access_token, room_title=room_title, user_message=user_message)

# Create a room
@app.route('/create_room/<access_token>', methods=['GET', 'POST'])
def create_room(access_token):
    if request.method == 'POST':
        room_title = request.form['room_title']
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {"title": room_title}
        response = requests.post(f"{WEBEX_BASE_URL}/rooms", headers=headers, json=payload)
        if response.status_code == 200:
            message = "Room created successfully!"
        else:
            message = "Failed to create room."
        return render_template('create_room.html', access_token=access_token, message=message)
    
    return render_template('create_room.html', access_token=access_token)

# Send message to a room
def send_message_to_room(access_token, room_id, message):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {"roomId": room_id, "text": message}
    response = requests.post(f"{WEBEX_BASE_URL}/messages", headers=headers, json=payload)
    return "Message sent successfully!" if response.status_code == 200 else "Failed to send message."

# Logout route
@app.route('/logout')
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

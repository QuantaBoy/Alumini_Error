from flask import request
from flask_socketio import emit, join_room
from datetime import datetime
from .chat_state import users, sid_to_user, message_history, get_room_id
from app import socketio

@socketio.on("connect")
def connect():
    print("Connected:", request.sid)

@socketio.on("register")
def register(data):
    username = data.get("username")
    if not username:
        return

    users[username] = request.sid
    sid_to_user[request.sid] = username

    emit("update_user_list", list(users.keys()), broadcast=True)
    
    # Send the list of people this user has messaged previously
    active_partners = set()
    for room_id in message_history.keys():
        if username in room_id:
            # room_id is like "user1_user2"
            partners = room_id.split("_")
            if username in partners:
                partner = partners[0] if partners[1] == username else partners[1]
                active_partners.add(partner)
    
    for partner in active_partners:
        room_id = get_room_id(username, partner)
        history = message_history.get(room_id, [])
        if history:
            last_msg = history[-1]
            emit("new_message_notification", {
                "sender": last_msg["sender"],
                "partner": partner,
                "message": last_msg.get("message", ""),
                "image": last_msg.get("image"),
                "timestamp": last_msg["timestamp"],
                "is_self": last_msg["sender"] == username
            })

@socketio.on("request_active_chats")
def handle_request_active_chats(data):
    username = data.get("username")
    # Same logic as above, can be refactored if needed
    active_partners = set()
    for room_id in message_history.keys():
        if username in room_id:
            partners = room_id.split("_")
            if username in partners:
                partner = partners[0] if partners[1] == username else partners[1]
                active_partners.add(partner)
    
    for partner in active_partners:
        room_id = get_room_id(username, partner)
        history = message_history.get(room_id, [])
        if history:
            last_msg = history[-1]
            emit("new_message_notification", {
                "sender": last_msg["sender"],
                "partner": partner,
                "message": last_msg.get("message", ""),
                "image": last_msg.get("image"),
                "timestamp": last_msg["timestamp"],
                "is_self": last_msg["sender"] == username
            })

@socketio.on("join_private_chat")
def join_private(data):
    room = get_room_id(data["username"], data["target"])
    join_room(room)
    emit("message_history", message_history.get(room, []))

@socketio.on("private_message")
def private_message(data):
    sender = data["sender"]
    receiver = data["receiver"]

    room = get_room_id(sender, receiver)
    timestamp = datetime.now().strftime("%H:%M")

    msg = {
        "sender": sender,
        "message": data.get("message"),
        "image": data.get("image"),
        "timestamp": timestamp
    }

    message_history.setdefault(room, []).append(msg)
    
    # Emit to the specific chat room
    emit("new_message", msg, room=room)

    # Also notify both sender and receiver to update their "Active Chats" lists
    notification_data = {
        "sender": sender,
        "receiver": receiver,
        "partner": receiver, # For the sender's sidebar update
        "message": msg["message"],
        "image": msg["image"],
        "timestamp": timestamp,
        "is_self": False
    }

    # Notify receiver
    if receiver in users:
        emit("new_message_notification", {**notification_data, "partner": sender}, room=users[receiver])

    # Notify sender (to update their own sidebar immediately)
    if sender in users:
        emit("new_message_notification", {**notification_data, "partner": receiver, "is_self": True}, room=users[sender])

@socketio.on("typing")
def handle_typing(data):
    sender = data["sender"]
    receiver = data["receiver"]
    if receiver in users:
        emit("user_typing", {"username": sender}, room=users[receiver])

@socketio.on("stop_typing")
def handle_stop_typing(data):
    sender = data["sender"]
    receiver = data["receiver"]
    if receiver in users:
        emit("user_stop_typing", {"username": sender}, room=users[receiver])

from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app and SocketIO
app = Flask(__name__)

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    transports=['websocket'],
    async_mode='threading'
)

# Store socket IDs and map them to Django user IDs
socket_ids = set()
user_socket_ids = {}
socket_user_ids = {}

@socketio.on('connect')
def handle_connect():
    """Handle new client connections"""
    socket_id = request.sid
    logger.info(f'A user connected: {socket_id}')
    socket_ids.add(socket_id)

    # Send current connections list to all clients
    socketio.emit('connections', list(socket_ids))

    # Join a room for this socket
    join_room(socket_id)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnections"""
    socket_id = request.sid
    logger.info(f'User disconnected: {socket_id}')
    socket_ids.discard(socket_id)

    user_id = socket_user_ids.pop(socket_id, None)
    if user_id and user_socket_ids.get(user_id) == socket_id:
        user_socket_ids.pop(user_id, None)

    # Notify all clients about updated connections
    socketio.emit('connections', list(socket_ids))

    # Leave room on disconnect
    leave_room(socket_id)

@socketio.on('register')
def handle_register(payload):
    """Register a socket connection with a Django user ID"""
    user_id = payload.get('userId')
    if user_id:
        user_id = str(user_id)
        previous_socket_id = user_socket_ids.get(user_id)
        if previous_socket_id and previous_socket_id != request.sid:
            socket_user_ids.pop(previous_socket_id, None)
        user_socket_ids[user_id] = request.sid
        socket_user_ids[request.sid] = user_id
        logger.info(f'Registered user {user_id} with socket {request.sid}')
        emit('registered', {'userId': user_id}, room=request.sid)

@socketio.on('offer')
def handle_offer(payload):
    """Handle WebRTC offer"""
    target_user_id = payload.get('targetUserId') or payload.get('target')
    offer = payload.get('offer')
    logger.info(f'Forwarding offer from {request.sid} to {target_user_id}')

    target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
    if target_socket_id:
        socketio.emit('offer', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid), 'offer': offer}, room=target_socket_id)
    else:
        emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)

@socketio.on('answer')
def handle_answer(payload):
    """Handle WebRTC answer"""
    target_user_id = payload.get('targetUserId') or payload.get('target')
    answer = payload.get('answer')
    logger.info(f'Forwarding answer from {request.sid} to {target_user_id}')

    target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
    if target_socket_id:
        socketio.emit('answer', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid), 'answer': answer}, room=target_socket_id)
    else:
        emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)

@socketio.on('ice-candidate')
def handle_ice_candidate(payload):
    """Handle ICE candidate"""
    target_user_id = payload.get('targetUserId') or payload.get('target')
    candidate = payload.get('candidate')
    logger.info(f'Forwarding ICE candidate from {request.sid} to {target_user_id}')

    target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
    if target_socket_id:
        socketio.emit('ice-candidate', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid), 'candidate': candidate}, room=target_socket_id)
    else:
        emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)

@socketio.on('connections')
def handle_connections():
    """Send list of current connections"""
    emit('connections', list(socket_ids))

@socketio.on('call-request')
def handle_call_request(data):
    target_user_id = data.get('targetUserId') or data.get('target')
    target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
    if target_socket_id:
        emit('call-request', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid)}, room=target_socket_id)
    else:
        emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)

@socketio.on('call-accept')
def handle_call_accept(data):
    target_user_id = data.get('targetUserId') or data.get('target')
    target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
    if target_socket_id:
        emit('call-accept', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid)}, room=target_socket_id)
    else:
        emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)

@socketio.on('call-decline')
def handle_call_decline(data):
    target_user_id = data.get('targetUserId') or data.get('target')
    target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
    if target_socket_id:
        emit('call-decline', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid)}, room=target_socket_id)
    else:
        emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)

@socketio.on('call-disconnect')
def handle_call_disconnect(data):
    target_user_id = data.get('targetUserId') or data.get('target')
    target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
    if target_socket_id:
        emit('call-disconnect', {}, room=target_socket_id)

if __name__ == '__main__':
    logger.info('Signaling server running on port 5001')
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
import os
import logging
import eventlet
eventlet.monkey_patch()

from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room

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

SIGNALING_HOST = os.getenv('SIGNALING_HOST', '0.0.0.0')
SIGNALING_PORT = int(os.getenv('SIGNALING_PORT', '5001'))

# Store socket IDs and map them to Django user IDs
socket_ids = set()
user_socket_ids = {}
socket_user_ids = {}

@socketio.on('connect')
def handle_connect():
    """Handle new client connections"""
    try:
        socket_id = request.sid
        logger.info(f'A user connected: {socket_id}')
        socket_ids.add(socket_id)

        # Send current connections list to all clients
        socketio.emit('connections', list(socket_ids))

        # Join a room for this socket
        join_room(socket_id)
    except Exception as e:
        logger.error(f'Error in handle_connect: {e}', exc_info=True)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnections"""
    try:
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
    except Exception as e:
        logger.error(f'Error in handle_disconnect: {e}', exc_info=True)

@socketio.on('register')
def handle_register(payload):
    """Register a socket connection with a Django user ID"""
    try:
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
    except Exception as e:
        logger.error(f'Error in handle_register: {e}', exc_info=True)
        emit('error', {'message': f'Registration failed: {str(e)}'})

@socketio.on('offer')
def handle_offer(payload):
    """Handle WebRTC offer"""
    try:
        target_user_id = payload.get('targetUserId') or payload.get('target')
        offer = payload.get('offer')
        logger.info(f'Forwarding offer from {request.sid} to {target_user_id}')

        target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
        if target_socket_id:
            socketio.emit('offer', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid), 'offer': offer}, room=target_socket_id)
        else:
            emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)
    except Exception as e:
        logger.error(f'Error in handle_offer: {e}', exc_info=True)
        emit('call-error', {'message': f'Offer failed: {str(e)}'})

@socketio.on('answer')
def handle_answer(payload):
    """Handle WebRTC answer"""
    try:
        target_user_id = payload.get('targetUserId') or payload.get('target')
        answer = payload.get('answer')
        logger.info(f'Forwarding answer from {request.sid} to {target_user_id}')

        target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
        if target_socket_id:
            socketio.emit('answer', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid), 'answer': answer}, room=target_socket_id)
        else:
            emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)
    except Exception as e:
        logger.error(f'Error in handle_answer: {e}', exc_info=True)
        emit('call-error', {'message': f'Answer failed: {str(e)}'})

@socketio.on('ice-candidate')
def handle_ice_candidate(payload):
    """Handle ICE candidate"""
    try:
        target_user_id = payload.get('targetUserId') or payload.get('target')
        candidate = payload.get('candidate')
        logger.info(f'Forwarding ICE candidate from {request.sid} to {target_user_id}')

        target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
        if target_socket_id:
            socketio.emit('ice-candidate', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid), 'candidate': candidate}, room=target_socket_id)
        else:
            emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)
    except Exception as e:
        logger.error(f'Error in handle_ice_candidate: {e}', exc_info=True)
        emit('call-error', {'message': f'ICE candidate failed: {str(e)}'})

@socketio.on('connections')
def handle_connections():
    """Send list of current connections"""
    try:
        emit('connections', list(socket_ids))
    except Exception as e:
        logger.error(f'Error in handle_connections: {e}', exc_info=True)

@socketio.on('call-request')
def handle_call_request(data):
    try:
        target_user_id = data.get('targetUserId') or data.get('target')
        target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
        if target_socket_id:
            emit('call-request', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid)}, room=target_socket_id)
        else:
            emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)
    except Exception as e:
        logger.error(f'Error in handle_call_request: {e}', exc_info=True)
        emit('call-error', {'message': f'Call request failed: {str(e)}'})

@socketio.on('call-accept')
def handle_call_accept(data):
    try:
        target_user_id = data.get('targetUserId') or data.get('target')
        target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
        if target_socket_id:
            emit('call-accept', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid)}, room=target_socket_id)
        else:
            emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)
    except Exception as e:
        logger.error(f'Error in handle_call_accept: {e}', exc_info=True)
        emit('call-error', {'message': f'Call accept failed: {str(e)}'})

@socketio.on('call-decline')
def handle_call_decline(data):
    try:
        target_user_id = data.get('targetUserId') or data.get('target')
        target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
        if target_socket_id:
            emit('call-decline', {'from': socket_user_ids.get(request.sid), 'fromUserId': socket_user_ids.get(request.sid)}, room=target_socket_id)
        else:
            emit('call-error', {'message': 'Target user is not connected'}, room=request.sid)
    except Exception as e:
        logger.error(f'Error in handle_call_decline: {e}', exc_info=True)
        emit('call-error', {'message': f'Call decline failed: {str(e)}'})

@socketio.on('call-disconnect')
def handle_call_disconnect(data):
    try:
        target_user_id = data.get('targetUserId') or data.get('target')
        target_socket_id = user_socket_ids.get(str(target_user_id)) if target_user_id else None
        if target_socket_id:
            emit('call-disconnect', {}, room=target_socket_id)
    except Exception as e:
        logger.error(f'Error in handle_call_disconnect: {e}', exc_info=True)
        emit('call-error', {'message': f'Call disconnect failed: {str(e)}'})


# Global error handler for SocketIO
@socketio.on_error_default
def default_error_handler(e):
    """Global error handler for all SocketIO events"""
    logger.error(f'SocketIO Error: {e}', exc_info=True)
    emit('error', {'message': f'Server error: {str(e)}'})


if __name__ == '__main__':
    logger.info(f'Signaling server running on {SIGNALING_HOST}:{SIGNALING_PORT}')
    socketio.run(app, host=SIGNALING_HOST, port=SIGNALING_PORT, debug=False, allow_unsafe_werkzeug=True)
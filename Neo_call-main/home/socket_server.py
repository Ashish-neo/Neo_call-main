from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production

# Initialize SocketIO with similar configuration
socketio = SocketIO(app, 
    cors_allowed_origins="*",  # Equivalent to cors: { origin: "*" }
    transports=['websocket'],   # Same transport restriction
    async_mode='threading'      # You can also use 'eventlet' or 'gevent' for better performance
)

# Store socket IDs (equivalent to Set in JS)
socket_ids = set()

@socketio.on('connect')
def handle_connect():
    """Handle new client connections"""
    socket_id = requests.sid
    logger.info(f'A user connected: {socket_id}')
    socket_ids.add(socket_id)
    
    # Join a default room for this socket (optional, but useful)
    join_room(socket_id)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnections"""
    socket_id = requests.sid
    logger.info(f'User disconnected: {socket_id}')
    socket_ids.discard(socket_id)  # discard() won't raise KeyError if not found
    
    # Leave room on disconnect (optional)
    leave_room(socket_id)

@socketio.on('offer')
def handle_offer(payload):
    """Handle WebRTC offer"""
    target = payload.get('target')
    offer = payload.get('offer')
    logger.info(f'offer {target} {offer}')
    
    # Emit to specific target socket
    emit('offer', {'from': requests.sid, 'offer': offer}, room=target)

@socketio.on('answer')
def handle_answer(payload):
    """Handle WebRTC answer"""
    target = payload.get('target')
    answer = payload.get('answer')
    logger.info(f'answer {target} {answer}')
    
    # Emit to specific target socket
    emit('answer', {'from': requests.sid, 'answer': answer}, room=target)

@socketio.on('ice-candidate')
def handle_ice_candidate(payload):
    """Handle ICE candidate"""
    target = payload.get('target')
    candidate = payload.get('candidate')
    logger.info(f'ice-candidate {target} {candidate}')
    
    # Emit to specific target socket
    emit('ice-candidate', {'from': requests.sid, 'candidate': candidate}, room=target)

@socketio.on('connections')
def handle_connections():
    """Send list of current connections"""
    emit('connections', list(socket_ids))

if __name__ == '__main__':
    logger.info('Signaling server running on port 5001')
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
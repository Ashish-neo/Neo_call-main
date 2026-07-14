import asyncio
import logging
import os
import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Socket.IO client
sio = socketio.AsyncClient(
    reconnection=True,
    reconnection_attempts=3,
    reconnection_delay=0.1,
)

class DummyVideoStreamTrack(VideoStreamTrack):
    """
    A dummy video track for testing.
    """
    async def recv(self):
        await asyncio.sleep(1/30)
        return None  # No actual video frame

class WebRTCClient:
    def __init__(self):
        self.pc = None
        self.my_id = None
        self.remote_id = None
        self.is_connected = False

    async def create_peer_connection(self):
        self.pc = RTCPeerConnection(
            iceServers=[
                {"urls": "stun:stun1.l.google.com:19302"},
                {"urls": "stun:stun2.l.google.com:19302"}
            ]
        )

        @self.pc.on("icecandidate")
        async def on_icecandidate(event):
            if event.candidate and self.remote_id:
                logger.info(f"Sending ICE candidate to {self.remote_id}")
                await sio.emit('ice-candidate', {
                    'target': self.remote_id,
                    'candidate': {
                        'candidate': event.candidate.candidate,
                        'sdpMid': event.candidate.sdpMid,
                        'sdpMLineIndex': event.candidate.sdpMLineIndex
                    }
                })

        @self.pc.on("track")
        def on_track(track):
            logger.info(f"Track received: {track.kind}")

        # Add dummy video track
        self.pc.addTrack(DummyVideoStreamTrack())

    async def make_call(self, target_id):
        self.remote_id = target_id
        await self.create_peer_connection()
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        logger.info(f"Sending offer to {target_id}")
        await sio.emit('offer', {
            'target': target_id,
            'offer': {
                'type': offer.type,
                'sdp': offer.sdp
            }
        })

    async def handle_offer(self, from_id, offer_data):
        self.remote_id = from_id
        await self.create_peer_connection()
        await self.pc.setRemoteDescription(
            RTCSessionDescription(offer_data['sdp'], offer_data['type'])
        )
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        logger.info(f"Sending answer to {from_id}")
        await sio.emit('answer', {
            'target': from_id,
            'answer': {
                'type': answer.type,
                'sdp': answer.sdp
            }
        })

    async def handle_answer(self, answer_data):
        logger.info("Received answer")
        await self.pc.setRemoteDescription(
            RTCSessionDescription(answer_data['sdp'], answer_data['type'])
        )

    async def handle_ice_candidate(self, candidate_data):
        logger.info("Received ICE candidate")
        candidate = candidate_data
        await self.pc.addIceCandidate(candidate)

webrtc_client = WebRTCClient()

@sio.event
async def connect():
    logger.info("Connected to signaling server")
    webrtc_client.my_id = sio.sid
    webrtc_client.is_connected = True

@sio.event
async def disconnect():
    logger.info("Disconnected from signaling server")
    webrtc_client.is_connected = False

@sio.event
async def connect_error(data):
    logger.error(f"Connection failed: {data}")

@sio.event
async def offer(data):
    logger.info(f"Received offer from {data['from']}")
    await webrtc_client.handle_offer(data['from'], data['offer'])

@sio.event
async def answer(data):
    logger.info(f"Received answer from {data['from']}")
    await webrtc_client.handle_answer(data['answer'])

@sio.event
async def ice_candidate(data):
    logger.info(f"Received ICE candidate from {data['from']}")
    await webrtc_client.handle_ice_candidate(data['candidate'])

@sio.event
async def connections(data):
    logger.info(f"Current connections: {data}")

async def command_loop():
    while True:
        cmd = input("Enter command (list, call <id>, exit): ").strip()
        if cmd == "list":
            await sio.emit('connections')
        elif cmd.startswith("call "):
            _, target_id = cmd.split(maxsplit=1)
            await webrtc_client.make_call(target_id)
        elif cmd == "exit":
            await sio.disconnect()
            break
        else:
            print("Unknown command.")

async def main():
    signaling_url = os.getenv('SIGNALING_SERVER_URL', '').strip() or 'http://localhost:5001'
    await sio.connect(signaling_url, transports=['websocket'])
    await asyncio.gather(
        sio.wait(),
        command_loop()
    )

if __name__ == '__main__':
    asyncio.run(main())

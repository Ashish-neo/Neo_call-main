const configuration = { 
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' } // Google's public STUN server
    ]
};

let peerConnection = new RTCPeerConnection(configuration);
let localStream = null;

const socket = new WebSocket(
    'ws://' + window.location.host + '/ws/call/'
);

async function startCall() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ 
            audio: true, 
            video: false 
        });
        
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });

        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        
        socket.send(JSON.stringify({
            type: 'offer',
            offer: offer
        }));
    } catch (err) {
        console.error('Error:', err);
    }
}

socket.onmessage = async function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'offer') {
        await peerConnection.setRemoteDescription(
            new RTCSessionDescription(data.offer)
        );
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        
        socket.send(JSON.stringify({
            type: 'answer',
            answer: answer
        }));
    } else if (data.type === 'answer') {
        await peerConnection.setRemoteDescription(
            new RTCSessionDescription(data.answer)
        );
    } else if (data.type === 'candidate') {
        await peerConnection.addIceCandidate(
            new RTCIceCandidate(data.candidate)
        );
    }
};

peerConnection.onicecandidate = event => {
    if (event.candidate) {
        socket.send(JSON.stringify({
            type: 'candidate',
            candidate: event.candidate
        }));
    }
};

peerConnection.ontrack = event => {
    const remoteAudio = document.getElementById('remoteAudio');
    remoteAudio.srcObject = event.streams[0];
};
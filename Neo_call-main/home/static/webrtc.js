'use strict';

let otherUser;
let remoteRTCMessage;

let iceCandidatesFromCaller = [];
let peerConnection;
let remoteStream;
let localStream;
let callInProgress = true;

// event from html
function call() {
    // create peer connection
    let userToCall = document.getElementById("Phone_no");
    otherUser = userToCall;
    beReady().then(Boolean => {
        console.log("here boolean", Boolean)
        processCall(userToCall)
    })
}

// event from html
function answer() {
    // do the event firing
    beReady().then(Boolean => {
        processAccept();
    })
    document.getElementById("answer").style.display = "None";
}

// create a connection to the WebSocket
function connectSocket() {
    let ws_schema = window.location.protocol == "https:" ? "wss://" : "ws://";
    console.log(ws_schema);

    callSocket = new WebSocket(
        ws_schema
        + window.location.host
        + '/ws/call/'
    );
    const socket = new WebSocket("ws://127.0.0.1:8000/ws/connection/");
    callSocket.onopen = function(event) {
        //let's send myName to the socket
        console.log("webSocket connection opened ")
        callSocket.send(JSON.stringify({
            type: 'login',
            data: {
                name: Unknow
            }
        }));
    }

    callSocket.onmessage = (e) => {
        let response = JSON.parse(e.data);
        // console.log(response);
        let type = response.type;
        if (type == 'connection') {
            console.log(response.data.message)
        }
        if (type == 'call_received') {
            // console.log(response);
            onNewCall(response.data)
        }
        if (type == 'call_answered') {
            onCallAnswered(response.data);
        }
        if (type == 'ICEcandidate') {
            onICECandidate(response.data);
        }
    }

    const onNewCall = (data) => {
        //when other called you
        //show answer button
        otherUser = data.caller;
        remoteRTCMessage = data.rtcMessage
        // store the ice candidate
        peerConnection.setRemoteDescription(new RTCSessionDescription(remoteRTCMessage));
    
        iceCandidatesFromCaller.forEach(candidate => {
            peerConnection.addIceCandidate(candidate);
        });
        iceCandidatesFromCaller = [];

        // document.getElementById("profileImageA").src = baseURL + callerProfile.image;
        document.getElementById("callerName").innerHTML = otherUser;
        document.getElementById("call").style.display = "none";
        document.getElementById("answer").style.display = "block";
    }

    const onCallAnswered = (data) => {
        //when other accept our call
        remoteRTCMessage = data.rtcMessage
        peerConnection.setRemoteDescription(new RTCSessionDescription(remoteRTCMessage));
        // store ice candidate
        iceCandidatesFromCaller.forEach(candidate => {
            peerConnection.addIceCandidate(candidate);
        });
        iceCandidatesFromCaller = [];

        document.getElementById("calling").style.display = "none";

        console.log("Call Started. They Answered");
        // console.log(pc);
        console.log("call in process:", callInProgress);
    }

    const onICECandidate = (data) => {
        // console.log(data);
        console.log("GOT ICE candidate");
        let message = data.rtcMessage
        let candidate = new RTCIceCandidate({
            sdpMLineIndex: message.label,
            candidate: message.candidate
        });

        if (peerConnection) {
            console.log("ICE candidate Added");
            peerConnection.addIceCandidate(candidate);
        } else {
            console.log("ICE candidate Pushed");
            iceCandidatesFromCaller.push(candidate);
        }
    }
}

// function for call answer and icecandidate 
function sendCall(data) {
    //to send a call
    console.log("Send Call");

    // socket.emit("call", data);
    callSocket.send(JSON.stringify({
        type: 'call',
        data
    }));

    document.getElementById("call").style.display = "none";
    // document.getElementById("profileImageCA").src = baseURL + otherUserProfile.image;
    document.getElementById("otherUserNameCA").innerHTML = otherUser;
    document.getElementById("calling").style.display = "block";
}

function answerCall(data) {
    //to answer a call
    // socket.emit("answerCall", data);
    callSocket.send(JSON.stringify({
        type: 'answer_call',
        data
    }));
    console.log("call in process:", callInProgress);
}

function sendICEcandidate(data) {
    //send only if we have caller, else no need to
    console.log("Send ICE candidate");
    // socket.emit("ICEcandidate", data)
    callSocket.send(JSON.stringify({
        type: 'ICEcandidate',
        data
    }));

}

// webrtc parts for 
// If WebRTC cannot establish a connection with the above methods, 
// TURN servers can be used as a fallback, 
// relaying data between endpoints

let pcConfig = {
    "iceServers":
        [
            {
                urls: ["stun:stun1.1.google.com:19302", "stun:stun2.1.google.com:19302"]
            }
        ]
};

// Set up audio and video regardless of what devices are present.
let sdpConstraints = {
    offerToReceiveAudio: true,
    offerToReceiveVideo: false
};

async function beReady() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true,
            video: false
        })
        localStream = stream;
        localVideo.srcObject = stream;
        await createConnectionAndAddStream()
        return true

    } catch (error) {
        console.log("error >>>", error)
        return false
    }

}

function createConnectionAndAddStream() {
    createPeerConnection();
    peerConnection.addStream(localStream);
    return true;
}

function processCall(userName) {
    console.log("processCall >>>", userName, peerConnection)
    peerConnection.createOffer((sessionDescription) => {
        peerConnection.setLocalDescription(sessionDescription);
        sendCall({
            name: userName,
            rtcMessage: sessionDescription
        })
    }, (error) => {
        console.log("Error");
    });
}

function processAccept() {

    peerConnection.setRemoteDescription(new RTCSessionDescription(remoteRTCMessage));
    peerConnection.createAnswer((sessionDescription) => {
        peerConnection.setLocalDescription(sessionDescription);

        answerCall({
            caller: otherUser,
            rtcMessage: sessionDescription
        })

    }, (error) => {
        console.log("Error");
    })
}

/////////////////////////////////////////////////////////

function createPeerConnection() {
    try {
        peerConnection = new RTCPeerConnection(pcConfig);
        peerConnection.onicecandidate = handleIceCandidate;
        peerConnection.onaddstream = handleRemoteStreamAdded;
        peerConnection.onremovestream = handleRemoteStreamRemoved;
        console.log('Created RTCPeerConnnection');
        return;
    } catch (e) {
        console.log('Failed to create PeerConnection, exception: ' + e.message);
        alert('Cannot create RTCPeerConnection object.');
        return;
    }
}

function handleIceCandidate(event) {
    // console.log('icecandidate event: ', event);
    if (event.candidate) {
        console.log("Local ICE candidate");
        // console.log(event.candidate.candidate);

        sendICEcandidate({
            user: otherUser,
            rtcMessage: {
                label: event.candidate.sdpMLineIndex,
                id: event.candidate.sdpMid,
                candidate: event.candidate.candidate
            }
        })

    } else {
        console.log('End of candidates.');
    }
}

function handleRemoteStreamAdded(event) {
    console.log('Remote stream added.');
    remoteStream = event.stream;
    remoteVideo.srcObject = remoteStream;
}

function handleRemoteStreamRemoved(event) {
    console.log('Remote stream removed. Event: ', event);
    remoteVideo.srcObject = null;
    localVideo.srcObject = null;
}


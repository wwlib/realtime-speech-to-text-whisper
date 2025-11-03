document.addEventListener("DOMContentLoaded", function() {
    const status = document.getElementById("status");
    const transcriptionDisplay = document.getElementById("transcription-display");
    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");
    const clearBtn = document.getElementById("clearBtn");
    const clientCount = document.getElementById("clientCount");
    const timestamp = document.getElementById("timestamp");

    const socketUrl = `ws://${window.location.host}`;
    let socket;
    let reconnectInterval;
    let isFirstConnection = true;

    function connect() {
        socket = new WebSocket(socketUrl);

        socket.onopen = function(event) {
            console.log("WebSocket connection established.");
            updateStatus("connected", "Connected to transcription service");
            
            if (isFirstConnection) {
                removePlaceholder();
                isFirstConnection = false;
            }
            
            // Update timestamp
            timestamp.textContent = `Connected: ${new Date().toLocaleTimeString()}`;
            
            // Clear any reconnect interval
            if (reconnectInterval) {
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }
            
            // Request initial status
            socket.send(JSON.stringify({ type: 'status' }));
        };

        socket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleMessage(data);
            } catch (error) {
                console.error("Failed to parse WebSocket message:", error);
            }
        };

        socket.onclose = function(event) {
            console.log("WebSocket connection closed. Reconnecting in 2 seconds...");
            updateStatus("disconnected", "Connection lost. Reconnecting...");
            
            // Disable buttons when disconnected
            startBtn.disabled = true;
            stopBtn.disabled = true;
            
            // Attempt to reconnect
            if (!reconnectInterval) {
                reconnectInterval = setInterval(() => {
                    console.log("Attempting to reconnect...");
                    connect();
                }, 2000);
            }
        };

        socket.onerror = function(error) {
            console.error("WebSocket error:", error);
            updateStatus("error", "Connection error");
        };
    }

    function handleMessage(data) {
        switch (data.type) {
            case 'transcription':
                addTranscription(data.text, data.timestamp);
                break;
            case 'status':
                if (data.status) {
                    updateStatus(data.status, data.message);
                    updateButtons(data.status);
                }
                if (data.clients !== undefined) {
                    clientCount.textContent = `Clients: ${data.clients}`;
                }
                break;
            default:
                console.log("Unknown message type:", data.type);
        }
    }

    function updateStatus(statusType, message) {
        status.textContent = message || statusType;
        status.className = `status-box ${statusType}`;
    }

    function updateButtons(serviceStatus) {
        switch (serviceStatus) {
            case 'stopped':
                startBtn.disabled = false;
                stopBtn.disabled = true;
                break;
            case 'running':
            case 'listening':
            case 'recording':
            case 'transcribing':
                startBtn.disabled = true;
                stopBtn.disabled = false;
                break;
            default:
                // Keep current state for unknown statuses
                break;
        }
    }

    function addTranscription(text, timestamp) {
        removePlaceholder();
        
        const p = document.createElement("p");
        
        // Add timestamp if provided
        if (timestamp) {
            const timeSpan = document.createElement("div");
            timeSpan.className = "timestamp";
            timeSpan.textContent = new Date(timestamp).toLocaleTimeString();
            p.appendChild(timeSpan);
        }
        
        // Add transcription text
        const textNode = document.createTextNode(text);
        p.appendChild(textNode);
        
        transcriptionDisplay.appendChild(p);
        
        // Auto-scroll to the bottom
        transcriptionDisplay.scrollTop = transcriptionDisplay.scrollHeight;
    }

    function removePlaceholder() {
        const placeholder = transcriptionDisplay.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }
    }

    function clearTranscriptions() {
        transcriptionDisplay.innerHTML = '<p class="placeholder">Transcribed text will appear here...</p>';
    }

    // Button event handlers
    startBtn.addEventListener('click', function() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'start' }));
        }
    });

    stopBtn.addEventListener('click', function() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'stop' }));
        }
    });

    clearBtn.addEventListener('click', function() {
        clearTranscriptions();
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey || event.metaKey) {
            switch (event.key) {
                case 's':
                    event.preventDefault();
                    if (!startBtn.disabled) {
                        startBtn.click();
                    }
                    break;
                case 'x':
                    event.preventDefault();
                    if (!stopBtn.disabled) {
                        stopBtn.click();
                    }
                    break;
                case 'k':
                    event.preventDefault();
                    clearBtn.click();
                    break;
            }
        }
    });

    // Initialize connection
    connect();

    // Update client count periodically
    setInterval(() => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'status' }));
        }
    }, 10000); // Every 10 seconds
});

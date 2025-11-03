document.addEventListener("DOMContentLoaded", function() {
    const status = document.getElementById("status");
    const transcriptionDisplay = document.getElementById("transcription-display");

    const socketUrl = `ws://${window.location.host}/ws`;
    let socket;

    function connect() {
        socket = new WebSocket(socketUrl);

        socket.onopen = function(event) {
            console.log("WebSocket connection established.");
            status.textContent = "Connected to transcription service.";
            status.className = "status-box connected";
        };

        socket.onmessage = function(event) {
            let message;
            try {
                // Try to parse as JSON first
                const data = JSON.parse(event.data);
                if (data.type === 'transcription') {
                    message = data.text;
                } else {
                    // If it's JSON but not a transcription type, ignore it
                    return;
                }
            } catch (e) {
                // If JSON parsing fails, treat as plain text (for backward compatibility)
                message = event.data;
            }
            
            // Append the new transcription text to the display
            const p = document.createElement("p");
            p.textContent = message;
            transcriptionDisplay.appendChild(p);
            // Auto-scroll to the bottom
            transcriptionDisplay.scrollTop = transcriptionDisplay.scrollHeight;
        };

        socket.onclose = function(event) {
            console.log("WebSocket connection closed. Reconnecting in 2 seconds...");
            status.textContent = "Connection lost. Reconnecting...";
            status.className = "status-box disconnected";
            setTimeout(connect, 2000); // Try to reconnect after 2 seconds
        };

        socket.onerror = function(error) {
            console.error("WebSocket error:", error);
            status.textContent = "Connection error.";
            status.className = "status-box disconnected";
        };
    }

    connect();
});

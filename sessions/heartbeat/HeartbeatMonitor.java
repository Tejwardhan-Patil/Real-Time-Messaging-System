package sessions.heartbeat;

import java.io.IOException;
import java.net.Socket;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.ConcurrentHashMap;

/**
 * HeartbeatMonitor is responsible for monitoring the connection status
 * of clients in a real-time messaging system by sending periodic heartbeat
 * pings and checking for responses. If a client does not respond within
 * a specific timeout period, the connection is marked as failed.
 */
public class HeartbeatMonitor {

    // Time interval between heartbeats in milliseconds
    private static final long HEARTBEAT_INTERVAL = 5000;

    // Maximum allowed time (ms) for a client to respond to a heartbeat
    private static final long TIMEOUT_THRESHOLD = 10000;

    // Map to track the status of each client connection
    private ConcurrentHashMap<String, ClientSession> clientSessions;

    // Timer for scheduling heartbeat checks
    private Timer timer;

    // Constructor
    public HeartbeatMonitor() {
        clientSessions = new ConcurrentHashMap<>();
        timer = new Timer(true); // Run as a daemon thread
    }

    /**
     * Adds a new client session to the HeartbeatMonitor.
     *
     * @param sessionId unique ID for the client session
     * @param socket client's socket connection
     */
    public void addClientSession(String sessionId, Socket socket) {
        ClientSession session = new ClientSession(sessionId, socket);
        clientSessions.put(sessionId, session);
    }

    /**
     * Removes a client session from the HeartbeatMonitor.
     *
     * @param sessionId unique ID for the client session
     */
    public void removeClientSession(String sessionId) {
        clientSessions.remove(sessionId);
    }

    /**
     * Starts the periodic heartbeat check for all client sessions.
     */
    public void startMonitoring() {
        timer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                for (ClientSession session : clientSessions.values()) {
                    session.sendHeartbeat();
                    session.checkTimeout();
                }
            }
        }, 0, HEARTBEAT_INTERVAL);
    }

    /**
     * Stops the HeartbeatMonitor and cancels all scheduled tasks.
     */
    public void stopMonitoring() {
        timer.cancel();
        clientSessions.clear();
    }

    /**
     * Represents a client session that is monitored by the HeartbeatMonitor.
     */
    private class ClientSession {
        private String sessionId;
        private Socket socket;
        private long lastHeartbeatSent;
        private long lastHeartbeatResponse;

        // Constructor
        public ClientSession(String sessionId, Socket socket) {
            this.sessionId = sessionId;
            this.socket = socket;
            this.lastHeartbeatSent = 0;
            this.lastHeartbeatResponse = System.currentTimeMillis();
        }

        /**
         * Sends a heartbeat message to the client.
         */
        public void sendHeartbeat() {
            try {
                if (socket != null && !socket.isClosed()) {
                    socket.getOutputStream().write("PING".getBytes());
                    lastHeartbeatSent = System.currentTimeMillis();
                    System.out.println("Heartbeat sent to client: " + sessionId);
                }
            } catch (IOException e) {
                System.err.println("Failed to send heartbeat to client: " + sessionId);
                removeClientSession(sessionId);
            }
        }

        /**
         * Handles the response from the client.
         */
        public void receiveHeartbeatResponse() {
            long currentTime = System.currentTimeMillis();
            long roundTripTime = currentTime - lastHeartbeatSent;
            lastHeartbeatResponse = currentTime;
            System.out.println("Heartbeat response received from client: " + sessionId + 
                               " (Round-trip time: " + roundTripTime + " ms)");
        }

        /**
         * Checks if the client has responded to the heartbeat within the allowed time.
         */
        public void checkTimeout() {
            long currentTime = System.currentTimeMillis();
            if (currentTime - lastHeartbeatResponse > TIMEOUT_THRESHOLD) {
                System.err.println("Client timed out: " + sessionId);
                removeClientSession(sessionId);
                closeConnection();
            } else {
                receiveHeartbeatResponse();
            }
        }

        /**
         * Closes the client socket and cleans up resources.
         */
        private void closeConnection() {
            try {
                if (socket != null && !socket.isClosed()) {
                    socket.close();
                    System.out.println("Connection closed for client: " + sessionId);
                }
            } catch (IOException e) {
                System.err.println("Failed to close connection for client: " + sessionId);
            }
        }
    }
}
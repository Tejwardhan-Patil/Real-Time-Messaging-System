package scalability.load_balancer;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.logging.Level;
import java.util.logging.Logger;

public class NginxLB {

    private static final String NGINX_CONFIG_PATH = "/nginx/nginx.conf";
    private static final Logger logger = Logger.getLogger(NginxLB.class.getName());

    public static void main(String[] args) {
        try {
            configureNginxLoadBalancer();
            reloadNginx();
            while (true) {
                monitorAndAutoScale();
                Thread.sleep(30000); // Check every 30 seconds
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Failed to configure or reload Nginx", e);
        }
    }

    public static void configureNginxLoadBalancer() throws IOException {
        StringBuilder nginxConfig = new StringBuilder();

        nginxConfig.append("worker_processes 4;\n")
                .append("events {\n")
                .append("    worker_connections 1024;\n")
                .append("}\n")
                .append("http {\n")
                .append("    upstream websocket_servers {\n")
                .append("        server websocket1.website.com:8080;\n")
                .append("        server websocket2.website.com:8080;\n")
                .append("        server websocket3.website.com:8080;\n")
                .append("    }\n")
                .append("    server {\n")
                .append("        listen 80;\n")
                .append("        location / {\n")
                .append("            proxy_pass http://websocket_servers;\n")
                .append("            proxy_http_version 1.1;\n")
                .append("            proxy_set_header Upgrade $http_upgrade;\n")
                .append("            proxy_set_header Connection \"upgrade\";\n")
                .append("            proxy_set_header Host $host;\n")
                .append("            proxy_cache_bypass $http_upgrade;\n")
                .append("        }\n")
                .append("    }\n")
                .append("}\n");

        writeConfigToFile(nginxConfig.toString(), NGINX_CONFIG_PATH);
    }

    private static void writeConfigToFile(String content, String path) throws IOException {
        java.nio.file.Files.write(java.nio.file.Paths.get(path), content.getBytes());
        logger.log(Level.INFO, "Nginx config written to: " + path);
    }

    public static void reloadNginx() throws IOException {
        ProcessBuilder processBuilder = new ProcessBuilder();
        processBuilder.command("nginx", "-s", "reload");
        Process process = processBuilder.start();

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                logger.log(Level.INFO, line);
            }
        }
    }

    public static String getNginxStatus() throws IOException {
        URL url = new URL("http://localhost/nginx_status");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");

        int responseCode = connection.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            StringBuilder response = new StringBuilder();
            try (BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()))) {
                String inputLine;
                while ((inputLine = in.readLine()) != null) {
                    response.append(inputLine);
                }
            }
            return response.toString();
        } else {
            return "Failed to get Nginx status. Response code: " + responseCode;
        }
    }

    public static void scaleUp(int additionalServers) {
        StringBuilder configUpdate = new StringBuilder();
        for (int i = 0; i < additionalServers; i++) {
            configUpdate.append("server websocket")
                    .append(i + 4)
                    .append(".website.com:8080;\n");
        }

        try {
            appendToNginxConfig(configUpdate.toString());
            reloadNginx();
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error scaling up Nginx servers", e);
        }
    }

    public static void appendToNginxConfig(String content) throws IOException {
        java.nio.file.Files.write(java.nio.file.Paths.get(NGINX_CONFIG_PATH), content.getBytes(), java.nio.file.StandardOpenOption.APPEND);
        logger.log(Level.INFO, "Appended content to Nginx config");
    }

    public static void monitorAndAutoScale() {
        double cpuLoad = getCpuLoad();
        int activeConnections = getActiveConnections();

        if (cpuLoad > 0.75 || activeConnections > 1000) {
            logger.log(Level.INFO, "CPU load high or too many active connections, scaling up Nginx servers...");
            scaleUp(2);  // Adding 2 more servers to the load balancer
        } else if (cpuLoad < 0.25 && activeConnections < 500) {
            logger.log(Level.INFO, "CPU load low and few active connections, scaling down Nginx servers...");
            scaleDown(1);  // Reducing by 1 server
        }
    }

    public static double getCpuLoad() {
        return Math.random(); // Simulating the CPU load
    }

    public static int getActiveConnections() {
        // Simulate the active connection count
        return (int) (Math.random() * 2000);
    }

    public static void scaleDown(int removeServers) {
        try {
            for (int i = 0; i < removeServers; i++) {
                removeServerFromNginxConfig("websocket" + (i + 4) + ".website.com");
            }
            reloadNginx();
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error scaling down Nginx servers", e);
        }
    }

    public static void removeServerFromNginxConfig(String serverAddress) throws IOException {
        java.nio.file.Path path = java.nio.file.Paths.get(NGINX_CONFIG_PATH);
        String configContent = new String(java.nio.file.Files.readAllBytes(path));
        configContent = configContent.replaceAll("server " + serverAddress + ".*?;", "");
        java.nio.file.Files.write(path, configContent.getBytes());
        logger.log(Level.INFO, "Removed server " + serverAddress + " from Nginx config");
    }

    public static void simulateHttpTraffic() {
        try {
            for (int i = 0; i < 10; i++) {
                HttpURLConnection connection = (HttpURLConnection) new URL("http://localhost").openConnection();
                connection.setRequestMethod("GET");
                int responseCode = connection.getResponseCode();
                if (responseCode == HttpURLConnection.HTTP_OK) {
                    logger.log(Level.INFO, "HTTP request successful, response code: " + responseCode);
                } else {
                    logger.log(Level.WARNING, "HTTP request failed, response code: " + responseCode);
                }
            }
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error simulating HTTP traffic", e);
        }
    }
    
    public static void simulateWebSocketTraffic() {
        // Simulating traffic for WebSocket connections
        logger.log(Level.INFO, "Simulating WebSocket traffic...");
        for (int i = 0; i < 10; i++) {
            new Thread(() -> {
                try {
                    HttpURLConnection connection = (HttpURLConnection) new URL("http://localhost").openConnection();
                    connection.setRequestMethod("GET");
                    connection.setRequestProperty("Connection", "Upgrade");
                    connection.setRequestProperty("Upgrade", "websocket");
                    connection.setRequestProperty("Host", "localhost");

                    int responseCode = connection.getResponseCode();
                    if (responseCode == HttpURLConnection.HTTP_OK) {
                        logger.log(Level.INFO, "WebSocket request successful, response code: " + responseCode);
                    } else {
                        logger.log(Level.WARNING, "WebSocket request failed, response code: " + responseCode);
                    }
                } catch (IOException e) {
                    logger.log(Level.SEVERE, "Error simulating WebSocket traffic", e);
                }
            }).start();
        }
    }
}
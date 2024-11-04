package deployment.ansible;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.List;
import java.util.ArrayList;
import java.util.Properties;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public class ServerConfig {
    private String ansiblePlaybookPath;
    private String inventoryFilePath;
    private String serverGroup;
    private String configFilePath;
    private Properties configProperties;

    // Constructor
    public ServerConfig(String ansiblePlaybookPath, String inventoryFilePath, String serverGroup, String configFilePath) {
        this.ansiblePlaybookPath = ansiblePlaybookPath;
        this.inventoryFilePath = inventoryFilePath;
        this.serverGroup = serverGroup;
        this.configFilePath = configFilePath;
        this.configProperties = new Properties();
        loadConfig();
    }

    // Load configuration properties from a file
    private void loadConfig() {
        try (FileInputStream fis = new FileInputStream(configFilePath)) {
            configProperties.load(fis);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // Run Ansible playbook for server configuration
    public void runAnsiblePlaybook() {
        try {
            List<String> command = new ArrayList<>();
            command.add("ansible-playbook");
            command.add(ansiblePlaybookPath);
            command.add("-i");
            command.add(inventoryFilePath);
            command.add("--limit");
            command.add(serverGroup);

            ProcessBuilder processBuilder = new ProcessBuilder(command);
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    System.out.println(line);
                }
            }

            int exitCode = process.waitFor();
            if (exitCode == 0) {
                System.out.println("Ansible playbook executed successfully.");
            } else {
                System.err.println("Ansible playbook execution failed with exit code " + exitCode);
            }

        } catch (IOException | InterruptedException e) {
            e.printStackTrace();
        }
    }

    // Validate server configurations
    public void validateConfig() {
        System.out.println("Validating server configurations...");

        if (configProperties.isEmpty()) {
            System.err.println("Configuration properties are empty.");
            return;
        }

        for (String key : configProperties.stringPropertyNames()) {
            String value = configProperties.getProperty(key);
            if (value == null || value.isEmpty()) {
                System.err.println("Configuration key " + key + " has no value.");
            } else {
                System.out.println("Configuration key " + key + " is valid.");
            }
        }
    }

    // Check server status using Ansible ad-hoc commands
    public void checkServerStatus() {
        try {
            List<String> command = new ArrayList<>();
            command.add("ansible");
            command.add(serverGroup);
            command.add("-i");
            command.add(inventoryFilePath);
            command.add("-m");
            command.add("ping");

            ProcessBuilder processBuilder = new ProcessBuilder(command);
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    System.out.println(line);
                }
            }

            int exitCode = process.waitFor();
            if (exitCode == 0) {
                System.out.println("Server status check successful.");
            } else {
                System.err.println("Server status check failed with exit code " + exitCode);
            }

        } catch (IOException | InterruptedException e) {
            e.printStackTrace();
        }
    }

    // Deploy configurations to server
    public void deployConfigurations() {
        System.out.println("Deploying configurations to server...");
        runAnsiblePlaybook();
    }

    // Retrieve configuration value by key
    public String getConfigValue(String key) {
        return configProperties.getProperty(key);
    }

    // Update configuration property
    public void updateConfig(String key, String value) {
        configProperties.setProperty(key, value);
        saveConfig();
    }

    // Save updated configuration properties to file
    private void saveConfig() {
        try (FileOutputStream fos = new FileOutputStream(configFilePath)) {
            configProperties.store(fos, "Updated server configurations");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // Main method for running server configuration
    public static void main(String[] args) {
        if (args.length != 4) {
            System.err.println("Usage: ServerConfig <ansiblePlaybookPath> <inventoryFilePath> <serverGroup> <configFilePath>");
            return;
        }

        String ansiblePlaybookPath = args[0];
        String inventoryFilePath = args[1];
        String serverGroup = args[2];
        String configFilePath = args[3];

        ServerConfig serverConfig = new ServerConfig(ansiblePlaybookPath, inventoryFilePath, serverGroup, configFilePath);

        // Validate configuration
        serverConfig.validateConfig();

        // Deploy configurations
        serverConfig.deployConfigurations();

        // Check server status
        serverConfig.checkServerStatus();
    }
}
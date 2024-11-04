package security.encryption;

import javax.net.ssl.*;
import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.util.logging.Logger;

public class TLSSetup {

    private static final Logger logger = Logger.getLogger(TLSSetup.class.getName());
    private static final String KEYSTORE_TYPE = "JKS";
    private static final String PROTOCOL = "TLSv1.3";
    private static final String DEFAULT_ALGORITHM = "SunX509";
    private static final String TRUST_MANAGER_ALGORITHM = "PKIX";

    private SSLContext sslContext;

    public TLSSetup() {
        try {
            this.sslContext = SSLContext.getInstance(PROTOCOL);
            KeyManagerFactory keyManagerFactory = createKeyManagerFactory();
            TrustManager[] trustManagers = createCustomTrustManagers();

            sslContext.init(keyManagerFactory.getKeyManagers(), trustManagers, null);
            logger.info("TLS setup initialized successfully.");
        } catch (Exception e) {
            logger.severe("Failed to initialize TLS setup: " + e.getMessage());
        }
    }

    private KeyManagerFactory createKeyManagerFactory() throws Exception {
        KeyStore keyStore = KeyStore.getInstance(KEYSTORE_TYPE);
        FileInputStream keyStoreStream = new FileInputStream("keystore.jks");
        keyStore.load(keyStoreStream, "keystorePassword".toCharArray());
        keyStoreStream.close();

        KeyManagerFactory keyManagerFactory = KeyManagerFactory.getInstance(DEFAULT_ALGORITHM);
        keyManagerFactory.init(keyStore, "keyPassword".toCharArray());
        return keyManagerFactory;
    }

    private TrustManager[] createCustomTrustManagers() throws Exception {
        return new TrustManager[]{new CustomTrustManager()};
    }

    public SSLServerSocketFactory createSSLServerSocketFactory() {
        return sslContext.getServerSocketFactory();
    }

    public SSLSocketFactory createSSLSocketFactory() {
        return sslContext.getSocketFactory();
    }

    public void configureSocket(SSLSocket socket) {
        try {
            socket.setEnabledProtocols(new String[]{PROTOCOL});
            socket.setUseClientMode(false);
            logger.info("TLS Socket configured successfully.");
        } catch (Exception e) {
            logger.severe("Error configuring SSL Socket: " + e.getMessage());
        }
    }

    public void configureServerSocket(SSLServerSocket serverSocket) {
        try {
            serverSocket.setEnabledProtocols(new String[]{PROTOCOL});
            logger.info("SSL Server Socket configured with TLSv1.3.");
        } catch (Exception e) {
            logger.severe("Failed to configure SSL Server Socket: " + e.getMessage());
        }
    }

    public void startTLSServer(int port) {
        try (SSLServerSocket serverSocket = (SSLServerSocket) createSSLServerSocketFactory().createServerSocket(port)) {
            configureServerSocket(serverSocket);

            while (true) {
                SSLSocket socket = (SSLSocket) serverSocket.accept();
                configureSocket(socket);

                // Handle communication in a separate thread
                new Thread(new ClientHandler(socket)).start();
            }
        } catch (Exception e) {
            logger.severe("Failed to start TLS server: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        TLSSetup tlsSetup = new TLSSetup();
        tlsSetup.startTLSServer(8443);
    }

    // ClientHandler to manage SSL connections with clients
    private static class ClientHandler implements Runnable {
        private final SSLSocket sslSocket;

        public ClientHandler(SSLSocket sslSocket) {
            this.sslSocket = sslSocket;
        }

        @Override
        public void run() {
            try {
                // Implement secure communication here
                logger.info("Connected to client: " + sslSocket.getInetAddress());
                sslSocket.getInputStream().read(); // Reading client's data

                sslSocket.getOutputStream().write("Hello Secure World".getBytes());
                sslSocket.getOutputStream().flush();
                sslSocket.close();
            } catch (Exception e) {
                logger.severe("Failed to handle client communication: " + e.getMessage());
            }
        }
    }
    
    // Custom Trust Manager for additional certificate validation logic
    private static class CustomTrustManager implements X509TrustManager {

        private final X509TrustManager defaultTrustManager;

        public CustomTrustManager() throws Exception {
            TrustManagerFactory tmf = TrustManagerFactory.getInstance(TRUST_MANAGER_ALGORITHM);
            tmf.init((KeyStore) null);
            this.defaultTrustManager = (X509TrustManager) tmf.getTrustManagers()[0];
        }

        @Override
        public void checkClientTrusted(X509Certificate[] chain, String authType) throws CertificateException {
            try {
                defaultTrustManager.checkClientTrusted(chain, authType);
            } catch (CertificateException e) {
                logger.warning("Custom client certificate validation failed.");
                throw e;
            }
        }

        @Override
        public void checkServerTrusted(X509Certificate[] chain, String authType) throws CertificateException {
            try {
                defaultTrustManager.checkServerTrusted(chain, authType);
            } catch (CertificateException e) {
                logger.warning("Custom server certificate validation failed.");
                throw e;
            }
        }

        @Override
        public X509Certificate[] getAcceptedIssuers() {
            return defaultTrustManager.getAcceptedIssuers();
        }
    }
}
package auth.oauth2;

import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class GoogleOAuth {

    private static final String CLIENT_ID = "client_id";
    private static final String CLIENT_SECRET = "client_secret";
    private static final String REDIRECT_URI = "https://website.com/oauth2callback";
    private static final String AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth";
    private static final String TOKEN_URL = "https://oauth2.googleapis.com/token";
    private static final String USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo";
    private static final String GRANT_TYPE = "authorization_code";

    // Redirect to Google OAuth Consent Screen
    public void redirectToGoogle(HttpServletResponse response) throws IOException {
        String url = AUTHORIZATION_URL + "?client_id=" + CLIENT_ID +
                     "&redirect_uri=" + REDIRECT_URI +
                     "&response_type=code&scope=openid email profile";
        response.sendRedirect(url);
    }

    // Exchange authorization code for tokens
    public JsonObject exchangeCodeForTokens(String authCode) throws IOException {
        URL url = new URL(TOKEN_URL);
        Map<String, String> params = new HashMap<>();
        params.put("code", authCode);
        params.put("client_id", CLIENT_ID);
        params.put("client_secret", CLIENT_SECRET);
        params.put("redirect_uri", REDIRECT_URI);
        params.put("grant_type", GRANT_TYPE);
        
        String response = sendPostRequest(url, params);
        JsonObject jsonResponse = JsonParser.parseString(response).getAsJsonObject();
        return jsonResponse;
    }

    // Retrieve user information using access token
    public JsonObject getUserInfo(String accessToken) throws IOException {
        URL url = new URL(USER_INFO_URL + "?access_token=" + accessToken);
        String response = sendGetRequest(url);
        JsonObject jsonResponse = JsonParser.parseString(response).getAsJsonObject();
        return jsonResponse;
    }

    // Helper: Sending POST Request
    private String sendPostRequest(URL url, Map<String, String> params) throws IOException {
        StringBuilder postData = new StringBuilder();
        for (Map.Entry<String, String> param : params.entrySet()) {
            if (postData.length() != 0) postData.append('&');
            postData.append(param.getKey());
            postData.append('=');
            postData.append(param.getValue());
        }
        byte[] postDataBytes = postData.toString().getBytes("UTF-8");

        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        conn.setRequestProperty("Content-Length", String.valueOf(postDataBytes.length));
        conn.setDoOutput(true);
        conn.getOutputStream().write(postDataBytes);

        return getResponse(conn);
    }

    // Helper: Sending GET Request
    private String sendGetRequest(URL url) throws IOException {
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        return getResponse(conn);
    }

    // Helper: Get response from the connection
    private String getResponse(HttpURLConnection conn) throws IOException {
        try (Scanner scanner = new Scanner(new InputStreamReader(conn.getInputStream()))) {
            StringBuilder response = new StringBuilder();
            while (scanner.hasNextLine()) {
                response.append(scanner.nextLine());
            }
            return response.toString();
        }
    }

    // Handle the OAuth callback request
    public void handleOAuthCallback(HttpServletRequest request, HttpServletResponse response) throws IOException {
        String authCode = request.getParameter("code");
        if (authCode != null) {
            JsonObject tokens = exchangeCodeForTokens(authCode);
            String accessToken = tokens.get("access_token").getAsString();
            JsonObject userInfo = getUserInfo(accessToken);
            
            // Further handling like saving user details or redirecting to dashboard
            response.getWriter().write("User Info: " + userInfo.toString());
        } else {
            response.getWriter().write("Authorization code not provided.");
        }
    }
}
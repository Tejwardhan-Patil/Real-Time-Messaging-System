package notifications.push_notifications;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class FCMService {

    private static final String FCM_URL = "https://fcm.googleapis.com/fcm/send";
    private static final String FCM_SERVER_KEY = "FCM_SERVER_KEY";

    private final RestTemplate restTemplate;

    public FCMService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    // Sends a notification to a single device using the device token
    public void sendNotificationToDevice(String targetToken, String title, String message) throws InterruptedException, ExecutionException {
        HttpHeaders headers = createHeaders();
        String payload = constructPayloadForDevice(targetToken, title, message);
        HttpEntity<String> entity = new HttpEntity<>(payload, headers);

        CompletableFuture<String> pushNotification = sendFcmMessage(entity);
        pushNotification.get();
    }

    // Sends a notification to a topic
    public void sendNotificationToTopic(String topic, String title, String message) throws InterruptedException, ExecutionException {
        HttpHeaders headers = createHeaders();
        String payload = constructPayloadForTopic(topic, title, message);
        HttpEntity<String> entity = new HttpEntity<>(payload, headers);

        CompletableFuture<String> pushNotification = sendFcmMessage(entity);
        pushNotification.get();
    }

    // Sends a notification to multiple devices
    public void sendNotificationToMultipleDevices(List<String> targetTokens, String title, String message) throws InterruptedException, ExecutionException {
        HttpHeaders headers = createHeaders();
        String payload = constructPayloadForMultipleDevices(targetTokens, title, message);
        HttpEntity<String> entity = new HttpEntity<>(payload, headers);

        CompletableFuture<String> pushNotification = sendFcmMessage(entity);
        pushNotification.get();
    }

    // Create headers for FCM HTTP request
    private HttpHeaders createHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "key=" + FCM_SERVER_KEY);
        headers.set("Content-Type", "application/json");
        return headers;
    }

    // Construct payload for sending notification to a single device
    private String constructPayloadForDevice(String targetToken, String title, String message) throws JsonProcessingException {
        FcmMessage fcmMessage = new FcmMessage();
        fcmMessage.setTo(targetToken);
        fcmMessage.setNotification(new Notification(title, message));
        return convertObjectToJson(fcmMessage);
    }

    // Construct payload for sending notification to a topic
    private String constructPayloadForTopic(String topic, String title, String message) throws JsonProcessingException {
        FcmMessage fcmMessage = new FcmMessage();
        fcmMessage.setTo("/topics/" + topic);
        fcmMessage.setNotification(new Notification(title, message));
        return convertObjectToJson(fcmMessage);
    }

    // Construct payload for sending notification to multiple devices
    private String constructPayloadForMultipleDevices(List<String> targetTokens, String title, String message) throws JsonProcessingException {
        FcmMessage fcmMessage = new FcmMessage();
        fcmMessage.setRegistration_ids(targetTokens);
        fcmMessage.setNotification(new Notification(title, message));
        return convertObjectToJson(fcmMessage);
    }

    // Send FCM message asynchronously using RestTemplate
    private CompletableFuture<String> sendFcmMessage(HttpEntity<String> entity) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                ResponseEntity<String> response = restTemplate.exchange(FCM_URL, HttpMethod.POST, entity, String.class);
                if (response.getStatusCode() == HttpStatus.OK) {
                    return response.getBody();
                } else {
                    throw new RuntimeException("Failed to send notification: " + response.getStatusCode());
                }
            } catch (HttpClientErrorException e) {
                throw new RuntimeException("Error while sending notification", e);
            }
        });
    }

    // Convert object to JSON string
    private String convertObjectToJson(Object object) throws JsonProcessingException {
        ObjectMapper objectMapper = new ObjectMapper();
        return objectMapper.writeValueAsString(object);
    }

    // Inner class for notification
    public static class Notification {
        private String title;
        private String body;

        public Notification() {
        }

        public Notification(String title, String body) {
            this.title = title;
            this.body = body;
        }

        public String getTitle() {
            return title;
        }

        public void setTitle(String title) {
            this.title = title;
        }

        public String getBody() {
            return body;
        }

        public void setBody(String body) {
            this.body = body;
        }
    }

    // Inner class for FCM message payload
    public static class FcmMessage {
        private String to;
        private List<String> registration_ids;
        private Notification notification;
        private Map<String, Object> data;

        public FcmMessage() {
        }

        public String getTo() {
            return to;
        }

        public void setTo(String to) {
            this.to = to;
        }

        public List<String> getRegistration_ids() {
            return registration_ids;
        }

        public void setRegistration_ids(List<String> registration_ids) {
            this.registration_ids = registration_ids;
        }

        public Notification getNotification() {
            return notification;
        }

        public void setNotification(Notification notification) {
            this.notification = notification;
        }

        public Map<String, Object> getData() {
            return data;
        }

        public void setData(Map<String, Object> data) {
            this.data = data;
        }
    }
}
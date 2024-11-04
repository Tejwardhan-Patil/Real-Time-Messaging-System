package tests.performance_tests;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class LoadTest {

    private static final String TARGET_URL = "http://website.com/api/v1/messages";
    private static final int NUM_USERS = 1000;  // Number of concurrent users
    private static final int MESSAGES_PER_USER = 50;  // Messages sent by each user
    private static final int THREAD_POOL_SIZE = 50;  // Number of threads for simulating users

    private static HttpClient httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();

    public static void main(String[] args) {
        System.out.println("Starting Load Test...");

        ScheduledExecutorService executorService = Executors.newScheduledThreadPool(THREAD_POOL_SIZE);

        List<CompletableFuture<Void>> futures = new ArrayList<>();

        for (int i = 0; i < NUM_USERS; i++) {
            int userId = i;
            futures.add(CompletableFuture.runAsync(() -> sendMessagesForUser(userId), executorService));
        }

        // Wait for all tasks to complete
        CompletableFuture<Void> allFutures = CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
        try {
            allFutures.get();
        } catch (InterruptedException | ExecutionException e) {
            e.printStackTrace();
        } finally {
            executorService.shutdown();
            try {
                if (!executorService.awaitTermination(60, TimeUnit.SECONDS)) {
                    executorService.shutdownNow();
                }
            } catch (InterruptedException e) {
                executorService.shutdownNow();
            }
        }

        System.out.println("Load Test Completed.");
    }

    private static void sendMessagesForUser(int userId) {
        for (int i = 0; i < MESSAGES_PER_USER; i++) {
            sendSingleMessage(userId, i);
            try {
                // Simulating real user typing delay between messages
                Thread.sleep(100);  
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    private static void sendSingleMessage(int userId, int messageId) {
        String requestBody = String.format("{\"userId\": %d, \"messageId\": %d, \"content\": \"This is message %d from user %d\"}", userId, messageId, messageId, userId);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(TARGET_URL))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                .build();

        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            System.out.printf("User %d: Sent message %d, Response: %d %s\n", userId, messageId, response.statusCode(), response.body());
        } catch (Exception e) {
            System.err.printf("User %d: Failed to send message %d\n", userId, messageId);
            e.printStackTrace();
        }
    }
}
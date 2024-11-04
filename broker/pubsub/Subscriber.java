package broker.pubsub;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

// Subscriber class for the Pub/Sub system
public class Subscriber {
    private String subscriberId;
    private Set<String> subscribedTopics;
    private BlockingQueue<String> messageQueue;

    // Map to track all subscribers based on topics
    private static Map<String, Set<Subscriber>> topicSubscribers = new HashMap<>();

    public Subscriber(String subscriberId) {
        this.subscriberId = subscriberId;
        this.subscribedTopics = new HashSet<>();
        this.messageQueue = new LinkedBlockingQueue<>();
    }

    // Subscribe to a topic
    public synchronized void subscribe(String topic) {
        subscribedTopics.add(topic);
        topicSubscribers.computeIfAbsent(topic, k -> new HashSet<>()).add(this);
        System.out.println(subscriberId + " subscribed to topic: " + topic);
    }

    // Unsubscribe from a topic
    public synchronized void unsubscribe(String topic) {
        if (subscribedTopics.contains(topic)) {
            subscribedTopics.remove(topic);
            Set<Subscriber> subscribers = topicSubscribers.get(topic);
            if (subscribers != null) {
                subscribers.remove(this);
                if (subscribers.isEmpty()) {
                    topicSubscribers.remove(topic);
                }
            }
            System.out.println(subscriberId + " unsubscribed from topic: " + topic);
        } else {
            System.out.println(subscriberId + " is not subscribed to topic: " + topic);
        }
    }

    // Receive a message from the broker
    public void receiveMessage(String message) {
        try {
            messageQueue.put(message);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.err.println("Interrupted while receiving message");
        }
    }

    // Method to poll the next message in the subscriber's queue
    public String getNextMessage() {
        return messageQueue.poll();
    }

    // Static method for publishing a message to a specific topic
    public static void publishMessage(String topic, String message) {
        Set<Subscriber> subscribers = topicSubscribers.get(topic);
        if (subscribers != null && !subscribers.isEmpty()) {
            for (Subscriber subscriber : subscribers) {
                subscriber.receiveMessage(message);
            }
            System.out.println("Message published to topic: " + topic);
        } else {
            System.out.println("No subscribers for topic: " + topic);
        }
    }

    // Get the subscriber's ID
    public String getSubscriberId() {
        return subscriberId;
    }

    // Check if subscriber is subscribed to a particular topic
    public boolean isSubscribedTo(String topic) {
        return subscribedTopics.contains(topic);
    }

    // Utility method to display all subscribers for a given topic
    public static void displaySubscribers(String topic) {
        Set<Subscriber> subscribers = topicSubscribers.get(topic);
        if (subscribers != null) {
            System.out.println("Subscribers for topic " + topic + ":");
            for (Subscriber subscriber : subscribers) {
                System.out.println(subscriber.getSubscriberId());
            }
        } else {
            System.out.println("No subscribers for topic: " + topic);
        }
    }

    // Main method for testing the pub/sub system
    public static void main(String[] args) {
        Subscriber subscriber1 = new Subscriber("Subscriber1");
        Subscriber subscriber2 = new Subscriber("Subscriber2");

        subscriber1.subscribe("Sports");
        subscriber2.subscribe("Technology");
        subscriber1.subscribe("Technology");

        publishMessage("Sports", "Breaking news in sports!");
        publishMessage("Technology", "Latest tech updates!");

        String message1 = subscriber1.getNextMessage();
        String message2 = subscriber2.getNextMessage();

        System.out.println(subscriber1.getSubscriberId() + " received: " + message1);
        System.out.println(subscriber2.getSubscriberId() + " received: " + message2);

        subscriber1.unsubscribe("Sports");
        publishMessage("Sports", "More sports news!");

        displaySubscribers("Technology");
    }
}
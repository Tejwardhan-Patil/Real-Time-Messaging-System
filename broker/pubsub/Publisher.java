package broker.pubsub;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Publisher class responsible for publishing messages to topics.
 */
public class Publisher {
    
    // Data structure to store topics and their subscribers
    private Map<String, List<Subscriber>> topics;

    // Constructor to initialize the Publisher
    public Publisher() {
        topics = new HashMap<>();
    }

    /**
     * Creates a new topic if it doesn't exist.
     * 
     * @param topic The name of the topic to be created.
     */
    public void createTopic(String topic) {
        if (!topics.containsKey(topic)) {
            topics.put(topic, new ArrayList<>());
            System.out.println("Topic created: " + topic);
        } else {
            System.out.println("Topic already exists: " + topic);
        }
    }

    /**
     * Publishes a message to a given topic.
     * 
     * @param topic   The topic where the message will be published.
     * @param message The message to be published.
     */
    public void publishMessage(String topic, String message) {
        if (topics.containsKey(topic)) {
            List<Subscriber> subscribers = topics.get(topic);
            for (Subscriber subscriber : subscribers) {
                subscriber.receiveMessage(topic, message);
            }
            System.out.println("Message published to topic: " + topic + " | Message: " + message);
        } else {
            System.out.println("Topic does not exist: " + topic);
        }
    }

    /**
     * Subscribes a subscriber to a specific topic.
     * 
     * @param topic      The topic to which the subscriber will be subscribed.
     * @param subscriber The subscriber object.
     */
    public void subscribe(String topic, Subscriber subscriber) {
        if (topics.containsKey(topic)) {
            topics.get(topic).add(subscriber);
            System.out.println("Subscriber added to topic: " + topic);
        } else {
            System.out.println("Topic does not exist: " + topic);
        }
    }

    /**
     * Unsubscribes a subscriber from a specific topic.
     * 
     * @param topic      The topic to which the subscriber will be unsubscribed.
     * @param subscriber The subscriber object.
     */
    public void unsubscribe(String topic, Subscriber subscriber) {
        if (topics.containsKey(topic)) {
            topics.get(topic).remove(subscriber);
            System.out.println("Subscriber removed from topic: " + topic);
        } else {
            System.out.println("Topic does not exist: " + topic);
        }
    }

    public static void main(String[] args) {
        Publisher publisher = new Publisher();
        
        // Create a few topics
        publisher.createTopic("news");
        publisher.createTopic("sports");
        publisher.createTopic("weather");

        // Create subscribers
        Subscriber subscriber1 = new Subscriber("Person1");
        Subscriber subscriber2 = new Subscriber("Person2");
        Subscriber subscriber3 = new Subscriber("Person3");

        // Subscribe to topics
        publisher.subscribe("news", subscriber1);
        publisher.subscribe("sports", subscriber2);
        publisher.subscribe("weather", subscriber3);
        publisher.subscribe("news", subscriber3);

        // Publish messages
        publisher.publishMessage("news", "Breaking news: Major event happening.");
        publisher.publishMessage("sports", "Sports update: Team A won the game.");
        publisher.publishMessage("weather", "Weather alert: Heavy rainfall expected.");

        // Unsubscribe a subscriber
        publisher.unsubscribe("news", subscriber1);

        // Publish message after unsubscribe
        publisher.publishMessage("news", "Update: More details on the event.");
    }
}

/**
 * Subscriber class representing a subscriber that receives messages.
 */
class Subscriber {
    
    private String name;

    // Constructor to create a subscriber with a name
    public Subscriber(String name) {
        this.name = name;
    }

    /**
     * Receives and processes a message from a topic.
     * 
     * @param topic   The topic from which the message is received.
     * @param message The message received.
     */
    public void receiveMessage(String topic, String message) {
        System.out.println("Subscriber " + name + " received message from topic " + topic + ": " + message);
    }

    // Get the name of the subscriber
    public String getName() {
        return name;
    }
}
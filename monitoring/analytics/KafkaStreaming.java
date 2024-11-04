package analytics;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.errors.WakeupException;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.kstream.KStream;
import org.apache.kafka.streams.kstream.KTable;
import org.apache.kafka.streams.kstream.Materialized;
import org.apache.kafka.streams.kstream.Consumed;
import org.apache.kafka.streams.kstream.Printed;
import org.apache.kafka.streams.kstream.Serialized;
import org.apache.kafka.streams.kstream.Grouped;
import org.apache.kafka.streams.kstream.Aggregator;
import java.util.Properties;
import java.time.Duration;
import java.util.Collections;

public class KafkaStreaming {

    private static KafkaConsumer<String, String> consumer;

    public static void main(String[] args) {
        // Configuring Kafka Consumer
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "user-activity-group");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");

        // Kafka consumer to consume activity stream
        consumer = new KafkaConsumer<>(props);

        // Subscribe to topic
        consumer.subscribe(Collections.singletonList("user-activity"));

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("Shutting down...");
            consumer.wakeup();
        }));

        try {
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
                for (ConsumerRecord<String, String> record : records) {
                    System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
                }
            }
        } catch (WakeupException e) {
            // Ignored because shutting down
        } finally {
            consumer.close();
            System.out.println("Consumer closed");
        }

        // Kafka Streams Analytics
        startKafkaStreams();
    }

    private static void startKafkaStreams() {
        // Configuring Kafka Streams
        Properties streamProps = new Properties();
        streamProps.put(StreamsConfig.APPLICATION_ID_CONFIG, "analytics-stream-app");
        streamProps.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        streamProps.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, org.apache.kafka.common.serialization.Serdes.String().getClass().getName());
        streamProps.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, org.apache.kafka.common.serialization.Serdes.String().getClass().getName());

        StreamsBuilder builder = new StreamsBuilder();
        
        // Creating a KStream for user activity topic
        KStream<String, String> userActivityStream = builder.stream("user-activity", Consumed.with(org.apache.kafka.common.serialization.Serdes.String(), org.apache.kafka.common.serialization.Serdes.String()));
        
        // Group and aggregate activities by user ID
        KTable<String, Long> activityCount = userActivityStream
            .groupByKey(Grouped.with(Serialized.with(org.apache.kafka.common.serialization.Serdes.String(), org.apache.kafka.common.serialization.Serdes.String())))
            .count(Materialized.as("activity-store"));
        
        // Printing the results to the console for monitoring purposes
        activityCount.toStream().print(Printed.<String, Long>toSysOut().withLabel("User Activity Count"));

        // Building and starting the Kafka Streams application
        KafkaStreams streams = new KafkaStreams(builder.build(), streamProps);
        streams.start();

        // Shutdown hook to gracefully stop the streams application
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            streams.close();
            System.out.println("Streams closed");
        }));
    }
}
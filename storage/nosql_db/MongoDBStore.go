package storage

import (
	"context"
	"fmt"
	"log"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// MongoDBStore defines a struct for MongoDB storage
type MongoDBStore struct {
	client     *mongo.Client
	database   *mongo.Database
	collection *mongo.Collection
}

// NewMongoDBStore creates a new MongoDBStore instance
func NewMongoDBStore(uri, dbName, collectionName string) (*MongoDBStore, error) {
	clientOptions := options.Client().ApplyURI(uri)
	client, err := mongo.Connect(context.TODO(), clientOptions)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to MongoDB: %v", err)
	}

	database := client.Database(dbName)
	collection := database.Collection(collectionName)

	return &MongoDBStore{
		client:     client,
		database:   database,
		collection: collection,
	}, nil
}

// Disconnect closes the MongoDB connection
func (store *MongoDBStore) Disconnect() error {
	return store.client.Disconnect(context.TODO())
}

// Message represents the structure of a message document
type Message struct {
	ID        primitive.ObjectID `bson:"_id,omitempty"`
	UserID    string             `bson:"userId"`
	Content   string             `bson:"content"`
	Timestamp time.Time          `bson:"timestamp"`
}

// SaveMessage stores a new message in MongoDB
func (store *MongoDBStore) SaveMessage(userID, content string) (*Message, error) {
	message := &Message{
		ID:        primitive.NewObjectID(),
		UserID:    userID,
		Content:   content,
		Timestamp: time.Now(),
	}

	_, err := store.collection.InsertOne(context.TODO(), message)
	if err != nil {
		return nil, fmt.Errorf("failed to insert message: %v", err)
	}

	return message, nil
}

// GetMessage retrieves a message by its ID from MongoDB
func (store *MongoDBStore) GetMessage(id string) (*Message, error) {
	objectID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return nil, fmt.Errorf("invalid message ID format: %v", err)
	}

	var message Message
	err = store.collection.FindOne(context.TODO(), bson.M{"_id": objectID}).Decode(&message)
	if err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, fmt.Errorf("message not found")
		}
		return nil, fmt.Errorf("failed to retrieve message: %v", err)
	}

	return &message, nil
}

// GetMessagesByUserID retrieves all messages by a specific user
func (store *MongoDBStore) GetMessagesByUserID(userID string) ([]*Message, error) {
	filter := bson.M{"userId": userID}
	cursor, err := store.collection.Find(context.TODO(), filter)
	if err != nil {
		return nil, fmt.Errorf("failed to retrieve messages: %v", err)
	}
	defer cursor.Close(context.TODO())

	var messages []*Message
	for cursor.Next(context.TODO()) {
		var message Message
		if err := cursor.Decode(&message); err != nil {
			return nil, fmt.Errorf("failed to decode message: %v", err)
		}
		messages = append(messages, &message)
	}

	if err := cursor.Err(); err != nil {
		return nil, fmt.Errorf("cursor error: %v", err)
	}

	return messages, nil
}

// DeleteMessage removes a message by its ID from MongoDB
func (store *MongoDBStore) DeleteMessage(id string) error {
	objectID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return fmt.Errorf("invalid message ID format: %v", err)
	}

	_, err = store.collection.DeleteOne(context.TODO(), bson.M{"_id": objectID})
	if err != nil {
		return fmt.Errorf("failed to delete message: %v", err)
	}

	return nil
}

// UpdateMessageContent updates the content of a message by its ID
func (store *MongoDBStore) UpdateMessageContent(id, newContent string) (*Message, error) {
	objectID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return nil, fmt.Errorf("invalid message ID format: %v", err)
	}

	update := bson.M{"$set": bson.M{"content": newContent, "timestamp": time.Now()}}
	result := store.collection.FindOneAndUpdate(context.TODO(), bson.M{"_id": objectID}, update, options.FindOneAndUpdate().ReturnDocument(options.After))
	var updatedMessage Message
	err = result.Decode(&updatedMessage)
	if err != nil {
		return nil, fmt.Errorf("failed to update message: %v", err)
	}

	return &updatedMessage, nil
}

// CountMessagesByUserID returns the count of messages by a specific user
func (store *MongoDBStore) CountMessagesByUserID(userID string) (int64, error) {
	count, err := store.collection.CountDocuments(context.TODO(), bson.M{"userId": userID})
	if err != nil {
		return 0, fmt.Errorf("failed to count messages: %v", err)
	}

	return count, nil
}

// GetRecentMessages retrieves the most recent messages from MongoDB
func (store *MongoDBStore) GetRecentMessages(limit int64) ([]*Message, error) {
	findOptions := options.Find()
	findOptions.SetSort(bson.D{"timestamp", -1})
	findOptions.SetLimit(limit)

	cursor, err := store.collection.Find(context.TODO(), bson.D{}, findOptions)
	if err != nil {
		return nil, fmt.Errorf("failed to retrieve recent messages: %v", err)
	}
	defer cursor.Close(context.TODO())

	var messages []*Message
	for cursor.Next(context.TODO()) {
		var message Message
		if err := cursor.Decode(&message); err != nil {
			return nil, fmt.Errorf("failed to decode message: %v", err)
		}
		messages = append(messages, &message)
	}

	if err := cursor.Err(); err != nil {
		return nil, fmt.Errorf("cursor error: %v", err)
	}

	return messages, nil
}

// CreateIndexes creates necessary indexes for the collection
func (store *MongoDBStore) CreateIndexes() error {
	indexes := []mongo.IndexModel{
		{
			Keys:    bson.D{"userId", 1},
			Options: options.Index().SetBackground(true),
		},
		{
			Keys:    bson.D{"timestamp", -1},
			Options: options.Index().SetBackground(true),
		},
	}

	_, err := store.collection.Indexes().CreateMany(context.TODO(), indexes)
	if err != nil {
		return fmt.Errorf("failed to create indexes: %v", err)
	}

	return nil
}

// DropCollection drops the entire message collection
func (store *MongoDBStore) DropCollection() error {
	err := store.collection.Drop(context.TODO())
	if err != nil {
		return fmt.Errorf("failed to drop collection: %v", err)
	}

	return nil
}

// HealthCheck checks the connectivity and availability of MongoDB
func (store *MongoDBStore) HealthCheck() error {
	err := store.client.Ping(context.TODO(), nil)
	if err != nil {
		return fmt.Errorf("MongoDB health check failed: %v", err)
	}

	return nil
}

func main() {
	// Usage
	store, err := NewMongoDBStore("mongodb://localhost:27017", "messaging", "messages")
	if err != nil {
		log.Fatalf("Error initializing MongoDBStore: %v", err)
	}
	defer store.Disconnect()

	// Perform health check
	if err := store.HealthCheck(); err != nil {
		log.Fatalf("MongoDB health check failed: %v", err)
	}

	// Create indexes
	if err := store.CreateIndexes(); err != nil {
		log.Fatalf("Error creating indexes: %v", err)
	}
}

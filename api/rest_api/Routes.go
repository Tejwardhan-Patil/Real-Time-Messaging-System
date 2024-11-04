package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/gorilla/mux"
)

// Message represents a message structure
type Message struct {
	ID        string `json:"id"`
	Content   string `json:"content"`
	Sender    string `json:"sender"`
	Receiver  string `json:"receiver"`
	Timestamp string `json:"timestamp"`
}

// In-memory store for messages
var messages []Message

// Get all messages
func GetMessages(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(messages)
}

// Get a single message by ID
func GetMessage(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	for _, item := range messages {
		if item.ID == params["id"] {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(item)
			return
		}
	}
	http.Error(w, "Message not found", http.StatusNotFound)
}

// Create a new message
func CreateMessage(w http.ResponseWriter, r *http.Request) {
	var message Message
	_ = json.NewDecoder(r.Body).Decode(&message)
	message.ID = fmt.Sprintf("%d", len(messages)+1) // ID generation
	messages = append(messages, message)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(message)
}

// Update an existing message by ID
func UpdateMessage(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	for i, item := range messages {
		if item.ID == params["id"] {
			_ = json.NewDecoder(r.Body).Decode(&messages[i])
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(messages[i])
			return
		}
	}
	http.Error(w, "Message not found", http.StatusNotFound)
}

// Delete a message by ID
func DeleteMessage(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	for i, item := range messages {
		if item.ID == params["id"] {
			messages = append(messages[:i], messages[i+1:]...)
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(messages)
			return
		}
	}
	http.Error(w, "Message not found", http.StatusNotFound)
}

// User session structure
type UserSession struct {
	UserID    string `json:"user_id"`
	SessionID string `json:"session_id"`
	Active    bool   `json:"active"`
}

// In-memory store for user sessions
var userSessions []UserSession

// Create a new user session
func CreateSession(w http.ResponseWriter, r *http.Request) {
	var session UserSession
	_ = json.NewDecoder(r.Body).Decode(&session)
	session.SessionID = fmt.Sprintf("session-%d", len(userSessions)+1) // Simple SessionID generation
	session.Active = true
	userSessions = append(userSessions, session)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(session)
}

// Terminate an existing session by ID
func TerminateSession(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	for i, item := range userSessions {
		if item.SessionID == params["id"] {
			userSessions[i].Active = false
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(userSessions[i])
			return
		}
	}
	http.Error(w, "Session not found", http.StatusNotFound)
}

// Get user session details by ID
func GetSession(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	for _, item := range userSessions {
		if item.SessionID == params["id"] {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(item)
			return
		}
	}
	http.Error(w, "Session not found", http.StatusNotFound)
}

// Track user presence
type Presence struct {
	UserID string `json:"user_id"`
	Online bool   `json:"online"`
}

// In-memory store for user presence
var userPresence []Presence

// Update user presence status
func UpdatePresence(w http.ResponseWriter, r *http.Request) {
	var presence Presence
	_ = json.NewDecoder(r.Body).Decode(&presence)
	for i, item := range userPresence {
		if item.UserID == presence.UserID {
			userPresence[i].Online = presence.Online
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(userPresence[i])
			return
		}
	}
	// If user doesn't exist, create a new presence entry
	userPresence = append(userPresence, presence)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(presence)
}

// Get user presence by ID
func GetPresence(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	for _, item := range userPresence {
		if item.UserID == params["id"] {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(item)
			return
		}
	}
	http.Error(w, "User not found", http.StatusNotFound)
}

// Define routes for the API
func initializeRoutes() *mux.Router {
	router := mux.NewRouter()

	// Message routes
	router.HandleFunc("/messages", GetMessages).Methods("GET")
	router.HandleFunc("/messages/{id}", GetMessage).Methods("GET")
	router.HandleFunc("/messages", CreateMessage).Methods("POST")
	router.HandleFunc("/messages/{id}", UpdateMessage).Methods("PUT")
	router.HandleFunc("/messages/{id}", DeleteMessage).Methods("DELETE")

	// Session routes
	router.HandleFunc("/sessions", CreateSession).Methods("POST")
	router.HandleFunc("/sessions/{id}", GetSession).Methods("GET")
	router.HandleFunc("/sessions/{id}", TerminateSession).Methods("DELETE")

	// Presence routes
	router.HandleFunc("/presence", UpdatePresence).Methods("PUT")
	router.HandleFunc("/presence/{id}", GetPresence).Methods("GET")

	return router
}

func main() {
	router := initializeRoutes()
	log.Fatal(http.ListenAndServe(":8000", router))
}

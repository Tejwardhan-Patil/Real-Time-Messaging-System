package sessions

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

// UserPresence represents the online/offline status of a user
type UserPresence struct {
	UserID   string
	IsOnline bool
	LastSeen time.Time
}

// PresenceService manages user presence and broadcasts updates
type PresenceService struct {
	users         map[string]*UserPresence
	connections   map[*websocket.Conn]string
	lock          sync.RWMutex
	broadcastChan chan *UserPresence
	upgrader      websocket.Upgrader
}

// NewPresenceService creates a new PresenceService instance
func NewPresenceService() *PresenceService {
	return &PresenceService{
		users:         make(map[string]*UserPresence),
		connections:   make(map[*websocket.Conn]string),
		broadcastChan: make(chan *UserPresence),
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true
			},
		},
	}
}

// HandleWebSocket handles WebSocket connections for presence tracking
func (ps *PresenceService) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := ps.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("Error upgrading connection: %v", err)
		return
	}
	defer conn.Close()

	userID := r.URL.Query().Get("userID")
	if userID == "" {
		log.Println("Invalid user ID")
		return
	}

	ps.addConnection(conn, userID)
	defer ps.removeConnection(conn)

	ps.setUserPresence(userID, true)
	ps.listenForMessages(conn)
}

// addConnection adds a WebSocket connection and associates it with a user ID
func (ps *PresenceService) addConnection(conn *websocket.Conn, userID string) {
	ps.lock.Lock()
	defer ps.lock.Unlock()

	ps.connections[conn] = userID
	log.Printf("User %s connected", userID)
}

// removeConnection removes a WebSocket connection and marks the user as offline
func (ps *PresenceService) removeConnection(conn *websocket.Conn) {
	ps.lock.Lock()
	defer ps.lock.Unlock()

	userID, exists := ps.connections[conn]
	if exists {
		delete(ps.connections, conn)
		ps.setUserPresence(userID, false)
		log.Printf("User %s disconnected", userID)
	}
}

// setUserPresence sets the online/offline status of a user and broadcasts the update
func (ps *PresenceService) setUserPresence(userID string, isOnline bool) {
	ps.lock.Lock()
	defer ps.lock.Unlock()

	userPresence, exists := ps.users[userID]
	if !exists {
		userPresence = &UserPresence{UserID: userID}
		ps.users[userID] = userPresence
	}
	userPresence.IsOnline = isOnline
	userPresence.LastSeen = time.Now()

	ps.broadcastChan <- userPresence
}

// listenForMessages listens for incoming WebSocket messages
func (ps *PresenceService) listenForMessages(conn *websocket.Conn) {
	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			log.Printf("Read error: %v", err)
			return
		}
		log.Printf("Received message: %s", message)
	}
}

// BroadcastPresenceChanges listens for presence changes and broadcasts them to all connections
func (ps *PresenceService) BroadcastPresenceChanges() {
	for presenceUpdate := range ps.broadcastChan {
		ps.lock.RLock()
		for conn := range ps.connections {
			if err := conn.WriteJSON(presenceUpdate); err != nil {
				log.Printf("Write error: %v", err)
				conn.Close()
			}
		}
		ps.lock.RUnlock()
	}
}

// StartPresenceService starts the presence tracking and broadcasting
func (ps *PresenceService) StartPresenceService() {
	go ps.BroadcastPresenceChanges()
}

// GetUserPresence returns the presence information for a user
func (ps *PresenceService) GetUserPresence(userID string) *UserPresence {
	ps.lock.RLock()
	defer ps.lock.RUnlock()

	return ps.users[userID]
}

// GetAllUserPresence returns the presence information for all users
func (ps *PresenceService) GetAllUserPresence() []*UserPresence {
	ps.lock.RLock()
	defer ps.lock.RUnlock()

	presences := []*UserPresence{}
	for _, presence := range ps.users {
		presences = append(presences, presence)
	}
	return presences
}

// CleanUpInactiveUsers removes users who have been offline for too long
func (ps *PresenceService) CleanUpInactiveUsers(maxIdleTime time.Duration) {
	for {
		time.Sleep(time.Minute)

		ps.lock.Lock()
		for userID, presence := range ps.users {
			if !presence.IsOnline && time.Since(presence.LastSeen) > maxIdleTime {
				delete(ps.users, userID)
				log.Printf("Cleaned up inactive user %s", userID)
			}
		}
		ps.lock.Unlock()
	}
}

// RunService runs the complete presence service
func RunService() {
	ps := NewPresenceService()
	go ps.StartPresenceService()
	go ps.CleanUpInactiveUsers(30 * time.Minute)

	http.HandleFunc("/presence", ps.HandleWebSocket)
	log.Fatal(http.ListenAndServe(":8080", nil))
}

// StatusResponse represents the response format for status
type StatusResponse struct {
	UserID   string `json:"userID"`
	Online   bool   `json:"online"`
	LastSeen string `json:"lastSeen"`
}

// HandleStatus checks the status of a specific user
func (ps *PresenceService) HandleStatus(w http.ResponseWriter, r *http.Request) {
	userID := r.URL.Query().Get("userID")
	if userID == "" {
		http.Error(w, "Missing userID parameter", http.StatusBadRequest)
		return
	}

	userPresence := ps.GetUserPresence(userID)
	if userPresence == nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	response := StatusResponse{
		UserID:   userPresence.UserID,
		Online:   userPresence.IsOnline,
		LastSeen: userPresence.LastSeen.Format(time.RFC3339),
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

package e2e_tests

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strings"
	"testing"
	"time"
	"websocket"

	"github.com/stretchr/testify/assert"
)

type E2ETestSuite struct {
	serverAddress string
	client1       *websocket.Client
	client2       *websocket.Client
	authToken     string
}

func TestMain(m *testing.M) {
	// Setup before tests
	suite := &E2ETestSuite{}
	suite.SetupSuite()

	// Run tests
	code := m.Run()

	// Teardown after tests
	suite.TeardownSuite()

	os.Exit(code)
}

func (suite *E2ETestSuite) SetupSuite() {
	suite.serverAddress = "http://localhost:8080"
	suite.authToken = suite.authenticateUser("person1", "password123")
	suite.client1 = suite.connectWebSocket(suite.authToken)
	suite.client2 = suite.connectWebSocket(suite.authenticateUser("person2", "password123"))
}

func (suite *E2ETestSuite) TeardownSuite() {
	suite.client1.Close()
	suite.client2.Close()
}

func (suite *E2ETestSuite) authenticateUser(username, password string) string {
	resp, err := http.Post(suite.serverAddress+"/auth/login", "application/json",
		strings.NewReader(fmt.Sprintf(`{"username": "%s", "password": "%s"}`, username, password)))
	if err != nil {
		panic("Failed to authenticate user")
	}

	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic("Failed to read response body")
	}

	var authResponse map[string]string
	err = json.Unmarshal(body, &authResponse)
	if err != nil {
		panic("Failed to unmarshal authentication response")
	}

	return authResponse["token"]
}

func (suite *E2ETestSuite) connectWebSocket(token string) *websocket.Client {
	dialer := websocket.Dialer{
		HandshakeTimeout: 5 * time.Second,
	}

	headers := http.Header{}
	headers.Set("Authorization", "Bearer "+token)

	conn, _, err := dialer.Dial(suite.serverAddress+"/ws", headers)
	if err != nil {
		panic("Failed to establish WebSocket connection")
	}

	return conn
}

func TestMessageDelivery(t *testing.T) {
	suite := &E2ETestSuite{}
	suite.SetupSuite()
	defer suite.TeardownSuite()

	message := "Hello from Person1"

	// Send message from client1 to client2
	err := suite.client1.WriteMessage(websocket.TextMessage, []byte(message))
	assert.NoError(t, err, "Sending message failed")

	// Receive message on client2
	_, receivedMessage, err := suite.client2.ReadMessage()
	assert.NoError(t, err, "Receiving message failed")
	assert.Equal(t, message, string(receivedMessage), "Messages do not match")
}

func TestSessionManagement(t *testing.T) {
	suite := &E2ETestSuite{}
	suite.SetupSuite()
	defer suite.TeardownSuite()

	sessionURL := suite.serverAddress + "/sessions"

	resp, err := http.Get(sessionURL)
	assert.NoError(t, err, "Failed to retrieve sessions")

	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	assert.NoError(t, err, "Failed to read response body")

	var sessions []map[string]interface{}
	err = json.Unmarshal(body, &sessions)
	assert.NoError(t, err, "Failed to unmarshal sessions data")

	assert.Greater(t, len(sessions), 0, "No active sessions found")
}

func TestUserPresence(t *testing.T) {
	suite := &E2ETestSuite{}
	suite.SetupSuite()
	defer suite.TeardownSuite()

	presenceURL := suite.serverAddress + "/presence"

	// Simulate presence update from client1
	resp, err := http.Post(presenceURL+"/update", "application/json",
		strings.NewReader(`{"userId": "person1", "status": "online"}`))
	assert.NoError(t, err, "Failed to update presence status")

	// Fetch presence status
	resp, err = http.Get(presenceURL + "/person1")
	assert.NoError(t, err, "Failed to fetch presence status")

	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	assert.NoError(t, err, "Failed to read response body")

	var presence map[string]string
	err = json.Unmarshal(body, &presence)
	assert.NoError(t, err, "Failed to unmarshal presence status")

	assert.Equal(t, "online", presence["status"], "Presence status mismatch")
}

func TestNotificationDelivery(t *testing.T) {
	suite := &E2ETestSuite{}
	suite.SetupSuite()
	defer suite.TeardownSuite()

	notificationURL := suite.serverAddress + "/notifications"

	// Send notification from client1
	resp, err := http.Post(notificationURL, "application/json",
		strings.NewReader(`{"from": "person1", "to": "person2", "message": "New message notification"}`))
	assert.NoError(t, err, "Failed to send notification")

	defer resp.Body.Close()

	// Verify that client2 receives notification
	_, notification, err := suite.client2.ReadMessage()
	assert.NoError(t, err, "Failed to receive notification")
	assert.Contains(t, string(notification), "New message notification", "Notification message mismatch")
}

func TestMessageEncryption(t *testing.T) {
	suite := &E2ETestSuite{}
	suite.SetupSuite()
	defer suite.TeardownSuite()

	message := "Sensitive Data"

	// Send encrypted message from client1 to client2
	encryptedMessage := encryptMessage(message, suite.client1)
	err := suite.client1.WriteMessage(websocket.TextMessage, encryptedMessage)
	assert.NoError(t, err, "Sending encrypted message failed")

	// Receive encrypted message on client2
	_, receivedMessage, err := suite.client2.ReadMessage()
	assert.NoError(t, err, "Receiving encrypted message failed")

	// Decrypt message
	decryptedMessage := decryptMessage(receivedMessage, suite.client2)
	assert.Equal(t, message, decryptedMessage, "Decrypted message does not match original")
}

func encryptMessage(message string, client *websocket.Client) []byte {
	// Simulate encryption logic here
	return []byte("ENCRYPTED_" + message)
}

func decryptMessage(message []byte, client *websocket.Client) string {
	// Simulate decryption logic here
	return strings.TrimPrefix(string(message), "ENCRYPTED_")
}

func TestScalability(t *testing.T) {
	suite := &E2ETestSuite{}
	suite.SetupSuite()
	defer suite.TeardownSuite()

	// Simulate load by sending multiple messages
	for i := 0; i < 1000; i++ {
		err := suite.client1.WriteMessage(websocket.TextMessage, []byte(fmt.Sprintf("Message %d", i)))
		assert.NoError(t, err, "Sending message failed")
	}

	// Verify messages were received
	for i := 0; i < 1000; i++ {
		_, receivedMessage, err := suite.client2.ReadMessage()
		assert.NoError(t, err, "Receiving message failed")
		assert.Contains(t, string(receivedMessage), fmt.Sprintf("Message %d", i), "Message content mismatch")
	}
}

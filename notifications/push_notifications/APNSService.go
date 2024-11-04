package notifications

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"
)

// APNSConfig holds configuration for the APNS service
type APNSConfig struct {
	APNSHost     string
	APNSPort     string
	KeyFilePath  string
	CertFilePath string
	Topic        string
}

// APNSService struct for sending push notifications to iOS devices
type APNSService struct {
	httpClient *http.Client
	config     APNSConfig
}

// NewAPNSService initializes the APNSService with the necessary configuration
func NewAPNSService(config APNSConfig) (*APNSService, error) {
	// Load the APNS certificate and key
	cert, err := tls.LoadX509KeyPair(config.CertFilePath, config.KeyFilePath)
	if err != nil {
		return nil, fmt.Errorf("unable to load APNS certificates: %v", err)
	}

	// Create TLS configuration
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		MinVersion:   tls.VersionTLS12,
	}

	transport := &http.Transport{
		TLSClientConfig: tlsConfig,
	}

	return &APNSService{
		httpClient: &http.Client{Transport: transport},
		config:     config,
	}, nil
}

// APNSPayload struct for crafting the notification payload
type APNSPayload struct {
	Aps Aps `json:"aps"`
}

// Aps struct holds the alert message and badge details
type Aps struct {
	Alert Alert  `json:"alert"`
	Badge int    `json:"badge"`
	Sound string `json:"sound,omitempty"`
}

// Alert struct for defining the title and body of the notification
type Alert struct {
	Title string `json:"title,omitempty"`
	Body  string `json:"body,omitempty"`
}

// APNSHeaders contains required headers for the APNS request
type APNSHeaders struct {
	ApnsID        string
	Expiration    int64
	Priority      int
	Topic         string
	Authorization string
}

// SendNotification sends a push notification to an iOS device
func (s *APNSService) SendNotification(deviceToken string, payload APNSPayload, headers APNSHeaders) error {
	// Construct URL for the APNS server
	url := fmt.Sprintf("https://%s/%s", s.config.APNSHost, deviceToken)

	// Marshal the payload to JSON
	payloadData, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal payload: %v", err)
	}

	// Create new HTTP request
	req, err := http.NewRequest("POST", url, bytes.NewReader(payloadData))
	if err != nil {
		return fmt.Errorf("failed to create HTTP request: %v", err)
	}

	// Set headers for APNS
	req.Header.Set("apns-topic", s.config.Topic)
	req.Header.Set("apns-priority", fmt.Sprintf("%d", headers.Priority))
	req.Header.Set("authorization", fmt.Sprintf("bearer %s", headers.Authorization))

	// Set expiration if provided
	if headers.Expiration > 0 {
		req.Header.Set("apns-expiration", fmt.Sprintf("%d", headers.Expiration))
	}

	// Execute the request
	resp, err := s.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send APNS notification: %v", err)
	}
	defer resp.Body.Close()

	// Read response body
	respBody, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read APNS response: %v", err)
	}

	// Check for errors in the response
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("error sending APNS notification: %s", respBody)
	}

	log.Printf("Notification sent successfully: %s", respBody)
	return nil
}

// GeneratePayload creates a notification payload
func GeneratePayload(title, body string, badge int, sound string) APNSPayload {
	return APNSPayload{
		Aps: Aps{
			Alert: Alert{
				Title: title,
				Body:  body,
			},
			Badge: badge,
			Sound: sound,
		},
	}
}

// APNSAuthToken is used to retrieve the bearer token for APNS requests
func (s *APNSService) APNSAuthToken() (string, error) {
	return "apns-jwt-token", nil
}

// RetryPolicy defines how the APNS service retries failed requests
type RetryPolicy struct {
	MaxRetries  int
	BackoffTime time.Duration
}

// RetryNotification sends the notification with retry logic
func (s *APNSService) RetryNotification(deviceToken string, payload APNSPayload, headers APNSHeaders, retryPolicy RetryPolicy) error {
	var lastError error
	for attempts := 0; attempts < retryPolicy.MaxRetries; attempts++ {
		lastError = s.SendNotification(deviceToken, payload, headers)
		if lastError == nil {
			return nil
		}
		log.Printf("Retry %d/%d failed: %v", attempts+1, retryPolicy.MaxRetries, lastError)
		time.Sleep(retryPolicy.BackoffTime)
	}
	return lastError
}

// CreateAndSendNotification creates a payload and sends the notification
func (s *APNSService) CreateAndSendNotification(deviceToken, title, body string, badge int, sound string) error {
	// Generate APNS payload
	payload := GeneratePayload(title, body, badge, sound)

	// Get APNS auth token
	authToken, err := s.APNSAuthToken()
	if err != nil {
		return fmt.Errorf("failed to retrieve APNS auth token: %v", err)
	}

	// Create headers for APNS request
	headers := APNSHeaders{
		Priority:      10, // Immediate priority
		Topic:         s.config.Topic,
		Authorization: authToken,
	}

	// Send notification
	return s.SendNotification(deviceToken, payload, headers)
}

// Test function to simulate sending a notification
func main() {
	config := APNSConfig{
		APNSHost:     "api.push.apple.com/3/device",
		APNSPort:     "443",
		CertFilePath: "/cert.pem",
		KeyFilePath:  "/key.pem",
		Topic:        "com.website.app",
	}

	apnsService, err := NewAPNSService(config)
	if err != nil {
		log.Fatalf("Failed to initialize APNS service: %v", err)
	}

	deviceToken := "device-token"
	title := "Notification Title"
	body := "This is the notification body"
	badge := 1
	sound := "default"

	err = apnsService.CreateAndSendNotification(deviceToken, title, body, badge, sound)
	if err != nil {
		log.Fatalf("Failed to send notification: %v", err)
	}

	log.Println("Notification sent successfully")
}

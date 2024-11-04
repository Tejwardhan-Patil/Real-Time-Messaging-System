package email_notifications

import (
	"fmt"
	"log"
	"net/smtp"
	"os"
	"strconv"
	"time"
)

// EmailClient represents the interface for sending emails
type EmailClient interface {
	SendEmail(to, subject, body string) error
}

// SMTPEngine is a struct that implements EmailClient using SMTP
type SMTPEngine struct {
	Host     string
	Port     int
	Username string
	Password string
	From     string
}

// NewSMTPEngine initializes a new SMTPEngine instance
func NewSMTPEngine(host string, port int, username, password, from string) *SMTPEngine {
	return &SMTPEngine{
		Host:     host,
		Port:     port,
		Username: username,
		Password: password,
		From:     from,
	}
}

// SendEmail sends an email via SMTP
func (e *SMTPEngine) SendEmail(to, subject, body string) error {
	addr := fmt.Sprintf("%s:%d", e.Host, e.Port)
	auth := smtp.PlainAuth("", e.Username, e.Password, e.Host)

	msg := fmt.Sprintf("From: %s\nTo: %s\nSubject: %s\n\n%s", e.From, to, subject, body)
	err := smtp.SendMail(addr, auth, e.From, []string{to}, []byte(msg))
	if err != nil {
		return fmt.Errorf("failed to send email: %v", err)
	}
	log.Printf("Email successfully sent to %s", to)
	return nil
}

// EmailNotificationService provides functionalities to send email notifications
type EmailNotificationService struct {
	EmailClient EmailClient
	DefaultFrom string
}

// NewEmailNotificationService initializes an EmailNotificationService
func NewEmailNotificationService(client EmailClient, defaultFrom string) *EmailNotificationService {
	return &EmailNotificationService{
		EmailClient: client,
		DefaultFrom: defaultFrom,
	}
}

// SendNotification sends an email notification with subject and body
func (service *EmailNotificationService) SendNotification(to, subject, body string) error {
	log.Printf("Sending email notification to %s...", to)
	err := service.EmailClient.SendEmail(to, subject, body)
	if err != nil {
		return fmt.Errorf("error sending notification: %v", err)
	}
	return nil
}

// Retry mechanism for failed emails
func (service *EmailNotificationService) SendNotificationWithRetry(to, subject, body string, retries int) error {
	var err error
	for i := 0; i < retries; i++ {
		err = service.SendNotification(to, subject, body)
		if err == nil {
			return nil
		}
		log.Printf("Retrying to send email to %s... Attempt %d", to, i+1)
		time.Sleep(2 * time.Second)
	}
	return fmt.Errorf("failed to send email after %d attempts: %v", retries, err)
}

// SendMassEmail sends emails to multiple recipients
func (service *EmailNotificationService) SendMassEmail(recipients []string, subject, body string) {
	for _, recipient := range recipients {
		err := service.SendNotification(recipient, subject, body)
		if err != nil {
			log.Printf("Failed to send email to %s: %v", recipient, err)
		}
	}
}

// Load SMTP configurations from environment variables
func LoadSMTPConfig() (*SMTPEngine, error) {
	host := os.Getenv("SMTP_HOST")
	portStr := os.Getenv("SMTP_PORT") // Get the port as a string
	username := os.Getenv("SMTP_USERNAME")
	password := os.Getenv("SMTP_PASSWORD")
	from := os.Getenv("SMTP_FROM")

	if host == "" || portStr == "" || username == "" || password == "" || from == "" {
		return nil, fmt.Errorf("missing required SMTP configuration")
	}

	// Convert port to integer
	port, err := strconv.Atoi(portStr)
	if err != nil {
		return nil, fmt.Errorf("invalid port: %v", err)
	}

	return NewSMTPEngine(host, port, username, password, from), nil
}

// LogEmailService is a EmailClient implementation that logs emails instead of sending them
type LogEmailService struct{}

// SendEmail simply logs the email data
func (e *LogEmailService) SendEmail(to, subject, body string) error {
	log.Printf("LogEmailService: Sending email to: %s, subject: %s, body: %s", to, subject, body)
	return nil
}

// EmailScheduler schedules emails for delayed sending
type EmailScheduler struct {
	service *EmailNotificationService
	delay   time.Duration
}

// NewEmailScheduler initializes a new email scheduler
func NewEmailScheduler(service *EmailNotificationService, delay time.Duration) *EmailScheduler {
	return &EmailScheduler{
		service: service,
		delay:   delay,
	}
}

// ScheduleEmail schedules an email to be sent after a delay
func (s *EmailScheduler) ScheduleEmail(to, subject, body string) {
	go func() {
		time.Sleep(s.delay)
		err := s.service.SendNotification(to, subject, body)
		if err != nil {
			log.Printf("Failed to send scheduled email to %s: %v", to, err)
		} else {
			log.Printf("Scheduled email sent to %s", to)
		}
	}()
}

// Error handling for email sending failures
type EmailErrorHandler struct {
	service  *EmailNotificationService
	fallback EmailClient
}

// NewEmailErrorHandler initializes an EmailErrorHandler
func NewEmailErrorHandler(service *EmailNotificationService, fallback EmailClient) *EmailErrorHandler {
	return &EmailErrorHandler{
		service:  service,
		fallback: fallback,
	}
}

// HandleError attempts to send email through fallback in case of failure
func (handler *EmailErrorHandler) HandleError(to, subject, body string) {
	err := handler.service.SendNotification(to, subject, body)
	if err != nil {
		log.Printf("Primary email service failed, using fallback: %v", err)
		handler.fallback.SendEmail(to, subject, body)
	}
}

// EmailLogger is used to log sent emails to a file
type EmailLogger struct {
	logFile string
}

// NewEmailLogger initializes a new EmailLogger
func NewEmailLogger(logFile string) *EmailLogger {
	return &EmailLogger{logFile: logFile}
}

// LogEmail logs the details of the sent email
func (l *EmailLogger) LogEmail(to, subject, body string) error {
	f, err := os.OpenFile(l.logFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("failed to open log file: %v", err)
	}
	defer f.Close()

	logMessage := fmt.Sprintf("To: %s, Subject: %s, Body: %s, Timestamp: %s\n", to, subject, body, time.Now().Format(time.RFC3339))
	if _, err = f.WriteString(logMessage); err != nil {
		return fmt.Errorf("failed to write to log file: %v", err)
	}
	return nil
}

// EmailWebhookService handles incoming email webhook events (from SendGrid, SES)
type EmailWebhookService struct{}

// HandleWebhook processes webhook events
func (e *EmailWebhookService) HandleWebhook(payload string) {
	log.Printf("Received email webhook payload: %s", payload)
	// Process webhook data (bounces, opens, clicks, etc)
}

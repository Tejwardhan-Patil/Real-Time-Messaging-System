package security

import (
	"log"
	"net"
	"net/http"
	"sync"
	"time"
)

// Rate limiting and IP tracking
const (
	requestsPerMinute = 60
	blockDuration     = 10 * time.Minute
	ddosThreshold     = 1000 // Threshold of requests to trigger DDoS detection
)

// IPRecord keeps track of requests made by an IP address
type IPRecord struct {
	Requests       int
	FirstRequestAt time.Time
	BlockExpiresAt time.Time
}

// IPTracker manages IP addresses and their request rates
type IPTracker struct {
	sync.RWMutex
	records map[string]*IPRecord
}

func NewIPTracker() *IPTracker {
	return &IPTracker{
		records: make(map[string]*IPRecord),
	}
}

// CleanUpExpiredBlocks removes blocked IPs whose block duration has expired
func (tracker *IPTracker) CleanUpExpiredBlocks() {
	tracker.Lock()
	defer tracker.Unlock()

	now := time.Now()
	for ip, record := range tracker.records {
		if now.After(record.BlockExpiresAt) {
			delete(tracker.records, ip)
		}
	}
}

// RecordRequest updates the request count for a given IP address
func (tracker *IPTracker) RecordRequest(ip string) {
	tracker.Lock()
	defer tracker.Unlock()

	now := time.Now()
	record, exists := tracker.records[ip]

	if !exists {
		tracker.records[ip] = &IPRecord{
			Requests:       1,
			FirstRequestAt: now,
		}
		return
	}

	// If block is active, do nothing
	if now.Before(record.BlockExpiresAt) {
		return
	}

	// Reset requests if more than 1 minute has passed
	if now.Sub(record.FirstRequestAt) > time.Minute {
		record.Requests = 0
		record.FirstRequestAt = now
	}

	// Increment the request count
	record.Requests++
}

// IsBlocked checks if the IP is currently blocked
func (tracker *IPTracker) IsBlocked(ip string) bool {
	tracker.RLock()
	defer tracker.RUnlock()

	record, exists := tracker.records[ip]
	if !exists {
		return false
	}

	// Check if the block is still active
	return time.Now().Before(record.BlockExpiresAt)
}

// BlockIP blocks the given IP for a duration
func (tracker *IPTracker) BlockIP(ip string) {
	tracker.Lock()
	defer tracker.Unlock()

	record, exists := tracker.records[ip]
	if exists {
		record.BlockExpiresAt = time.Now().Add(blockDuration)
	}
}

// Middleware to enforce rate limits and detect DDoS attacks
func RateLimitMiddleware(tracker *IPTracker) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ip, _, err := net.SplitHostPort(r.RemoteAddr)
			if err != nil {
				log.Printf("Error parsing IP address: %v", err)
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
				return
			}

			// Check if the IP is blocked
			if tracker.IsBlocked(ip) {
				http.Error(w, "Too Many Requests", http.StatusTooManyRequests)
				return
			}

			// Record the request
			tracker.RecordRequest(ip)

			// Check if the IP exceeded the rate limit
			record := tracker.records[ip]
			if record.Requests > requestsPerMinute {
				tracker.BlockIP(ip)
				log.Printf("IP %s blocked due to rate limiting", ip)
				http.Error(w, "Too Many Requests", http.StatusTooManyRequests)
				return
			}

			// Continue with the next handler
			next.ServeHTTP(w, r)
		})
	}
}

// DDoSProtection struct to manage multiple security features
type DDoSProtection struct {
	tracker   *IPTracker
	ddosCount map[string]int
	mu        sync.Mutex
}

// NewDDoSProtection creates a new DDoSProtection instance
func NewDDoSProtection() *DDoSProtection {
	return &DDoSProtection{
		tracker:   NewIPTracker(),
		ddosCount: make(map[string]int),
	}
}

// CheckDDoS detects potential DDoS attacks based on traffic volume
func (d *DDoSProtection) CheckDDoS(ip string) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	d.ddosCount[ip]++
	if d.ddosCount[ip] > ddosThreshold {
		log.Printf("Potential DDoS attack detected from IP: %s", ip)
		return true
	}

	return false
}

// BlockSuspiciousIP blocks IPs showing signs of a DDoS attack
func (d *DDoSProtection) BlockSuspiciousIP(ip string) {
	d.tracker.BlockIP(ip)
}

// Middleware to protect against DDoS attacks
func DDoSMiddleware(ddos *DDoSProtection) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ip, _, err := net.SplitHostPort(r.RemoteAddr)
			if err != nil {
				log.Printf("Error parsing IP address: %v", err)
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
				return
			}

			// Check for potential DDoS
			if ddos.CheckDDoS(ip) {
				ddos.BlockSuspiciousIP(ip)
				http.Error(w, "DDoS Detected", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

func main() {
	ddosProtection := NewDDoSProtection()

	mux := http.NewServeMux()

	// Apply rate limiting middleware
	mux.Handle("/", RateLimitMiddleware(ddosProtection.tracker)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("Welcome to the secure server!"))
	})))

	// Apply DDoS protection middleware
	mux.Handle("/secure", DDoSMiddleware(ddosProtection)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("You have accessed a secure route!"))
	})))

	server := &http.Server{
		Addr:    ":8080",
		Handler: mux,
	}

	log.Println("Starting server on :8080")
	if err := server.ListenAndServe(); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

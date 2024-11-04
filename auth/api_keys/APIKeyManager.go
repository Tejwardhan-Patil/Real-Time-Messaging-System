package api_keys

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"sync"
	"time"
)

// APIKeyManager manages API keys, their generation, validation, and expiration.
type APIKeyManager struct {
	keys          map[string]*APIKey
	expiry        time.Duration
	mutex         sync.RWMutex
	cleanupTicker *time.Ticker
	stopCleanup   chan struct{}
}

// APIKey struct stores the key details.
type APIKey struct {
	Key       string
	CreatedAt time.Time
	ExpiresAt time.Time
	Active    bool
}

// NewAPIKeyManager initializes a new APIKeyManager with an expiry duration and a cleanup interval.
func NewAPIKeyManager(expiryDuration time.Duration, cleanupInterval time.Duration) *APIKeyManager {
	manager := &APIKeyManager{
		keys:          make(map[string]*APIKey),
		expiry:        expiryDuration,
		cleanupTicker: time.NewTicker(cleanupInterval),
		stopCleanup:   make(chan struct{}),
	}

	go manager.cleanupExpiredKeys()

	return manager
}

// GenerateKey generates a new API key, stores it in the manager and returns it.
func (m *APIKeyManager) GenerateKey() (string, error) {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	key, err := generateRandomKey()
	if err != nil {
		return "", err
	}

	now := time.Now()
	apiKey := &APIKey{
		Key:       key,
		CreatedAt: now,
		ExpiresAt: now.Add(m.expiry),
		Active:    true,
	}

	m.keys[apiKey.Key] = apiKey

	return apiKey.Key, nil
}

// ValidateKey checks if the provided key is valid and active.
func (m *APIKeyManager) ValidateKey(key string) (bool, error) {
	m.mutex.RLock()
	defer m.mutex.RUnlock()

	apiKey, exists := m.keys[key]
	if !exists {
		return false, errors.New("API key not found")
	}

	if !apiKey.Active {
		return false, errors.New("API key is inactive")
	}

	if apiKey.ExpiresAt.Before(time.Now()) {
		return false, errors.New("API key has expired")
	}

	return true, nil
}

// RevokeKey deactivates the provided API key, making it invalid for future use.
func (m *APIKeyManager) RevokeKey(key string) error {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	apiKey, exists := m.keys[key]
	if !exists {
		return errors.New("API key not found")
	}

	apiKey.Active = false

	return nil
}

// ListKeys lists all active API keys in the system.
func (m *APIKeyManager) ListKeys() []string {
	m.mutex.RLock()
	defer m.mutex.RUnlock()

	var keys []string
	for k, apiKey := range m.keys {
		if apiKey.Active && apiKey.ExpiresAt.After(time.Now()) {
			keys = append(keys, k)
		}
	}
	return keys
}

// CleanupExpiredKeys removes expired keys from the manager.
func (m *APIKeyManager) cleanupExpiredKeys() {
	for {
		select {
		case <-m.cleanupTicker.C:
			m.mutex.Lock()
			for key, apiKey := range m.keys {
				if apiKey.ExpiresAt.Before(time.Now()) {
					delete(m.keys, key)
				}
			}
			m.mutex.Unlock()
		case <-m.stopCleanup:
			return
		}
	}
}

// StopCleanup stops the cleanup routine.
func (m *APIKeyManager) StopCleanup() {
	close(m.stopCleanup)
	m.cleanupTicker.Stop()
}

// generateRandomKey creates a random, secure key for API key generation.
func generateRandomKey() (string, error) {
	bytes := make([]byte, 32)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", err
	}

	hash := sha256.Sum256(bytes)
	return hex.EncodeToString(hash[:]), nil
}

// Shutdown handles cleanup when the application is shutting down.
func (m *APIKeyManager) Shutdown() {
	m.StopCleanup()
	m.mutex.Lock()
	defer m.mutex.Unlock()
	for k := range m.keys {
		delete(m.keys, k)
	}
}

// RotateKey rotates an existing key by revoking the old one and generating a new one.
func (m *APIKeyManager) RotateKey(oldKey string) (string, error) {
	err := m.RevokeKey(oldKey)
	if err != nil {
		return "", err
	}
	return m.GenerateKey()
}

// UpdateKeyExpiry updates the expiration time of an existing API key.
func (m *APIKeyManager) UpdateKeyExpiry(key string, newExpiry time.Duration) error {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	apiKey, exists := m.keys[key]
	if !exists {
		return errors.New("API key not found")
	}

	if !apiKey.Active {
		return errors.New("API key is inactive")
	}

	apiKey.ExpiresAt = time.Now().Add(newExpiry)

	return nil
}

// ExtendKeyExpiry extends the expiration time of an active API key by a given duration.
func (m *APIKeyManager) ExtendKeyExpiry(key string, extension time.Duration) error {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	apiKey, exists := m.keys[key]
	if !exists {
		return errors.New("API key not found")
	}

	if !apiKey.Active {
		return errors.New("API key is inactive")
	}

	apiKey.ExpiresAt = apiKey.ExpiresAt.Add(extension)

	return nil
}

// KeyDetails provides detailed information about a specific API key.
func (m *APIKeyManager) KeyDetails(key string) (*APIKey, error) {
	m.mutex.RLock()
	defer m.mutex.RUnlock()

	apiKey, exists := m.keys[key]
	if !exists {
		return nil, errors.New("API key not found")
	}

	return apiKey, nil
}

// PurgeInactiveKeys deletes all inactive keys from the manager.
func (m *APIKeyManager) PurgeInactiveKeys() {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	for key, apiKey := range m.keys {
		if !apiKey.Active {
			delete(m.keys, key)
		}
	}
}

// KeyCount returns the total number of API keys managed.
func (m *APIKeyManager) KeyCount() int {
	m.mutex.RLock()
	defer m.mutex.RUnlock()

	return len(m.keys)
}

// ActiveKeyCount returns the count of currently active API keys.
func (m *APIKeyManager) ActiveKeyCount() int {
	m.mutex.RLock()
	defer m.mutex.RUnlock()

	count := 0
	for _, apiKey := range m.keys {
		if apiKey.Active && apiKey.ExpiresAt.After(time.Now()) {
			count++
		}
	}
	return count
}

package routing

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

// Message defines the structure for the message that is routed
type Message struct {
	ID        string
	Sender    string
	Receiver  string
	Channel   string
	Payload   string
	Timestamp time.Time
	Priority  int
}

// Router handles message routing logic
type Router struct {
	Channels map[string][]string // channel name -> list of subscribers
	Users    map[string][]string // user name -> list of channels they're subscribed to
	Mutex    sync.RWMutex
}

// NewRouter creates a new router instance
func NewRouter() *Router {
	return &Router{
		Channels: make(map[string][]string),
		Users:    make(map[string][]string),
	}
}

// Subscribe adds a user to a channel
func (r *Router) Subscribe(user, channel string) error {
	r.Mutex.Lock()
	defer r.Mutex.Unlock()

	// Add user to channel's subscriber list
	if _, exists := r.Channels[channel]; !exists {
		r.Channels[channel] = []string{}
	}
	r.Channels[channel] = append(r.Channels[channel], user)

	// Add channel to user's subscription list
	if _, exists := r.Users[user]; !exists {
		r.Users[user] = []string{}
	}
	r.Users[user] = append(r.Users[user], channel)

	fmt.Printf("User %s subscribed to channel %s\n", user, channel)
	return nil
}

// Unsubscribe removes a user from a channel
func (r *Router) Unsubscribe(user, channel string) error {
	r.Mutex.Lock()
	defer r.Mutex.Unlock()

	// Remove user from channel
	if subs, exists := r.Channels[channel]; exists {
		for i, u := range subs {
			if u == user {
				r.Channels[channel] = append(subs[:i], subs[i+1:]...)
				break
			}
		}
	} else {
		return errors.New("channel does not exist")
	}

	// Remove channel from user's subscription list
	if subs, exists := r.Users[user]; exists {
		for i, c := range subs {
			if c == channel {
				r.Users[user] = append(subs[:i], subs[i+1:]...)
				break
			}
		}
	} else {
		return errors.New("user does not exist")
	}

	fmt.Printf("User %s unsubscribed from channel %s\n", user, channel)
	return nil
}

// RouteMessage routes a message to the correct channel or user
func (r *Router) RouteMessage(msg Message) error {
	r.Mutex.RLock()
	defer r.Mutex.RUnlock()

	if len(msg.Channel) > 0 {
		// If the message has a channel, route it to all users subscribed to the channel
		if subscribers, exists := r.Channels[msg.Channel]; exists {
			fmt.Printf("Routing message to channel %s: %s\n", msg.Channel, msg.Payload)
			for _, subscriber := range subscribers {
				fmt.Printf("Delivered message to user %s\n", subscriber)
			}
		} else {
			return errors.New("channel does not exist")
		}
	} else if len(msg.Receiver) > 0 {
		// If the message has a specific receiver, route it to the user
		if _, exists := r.Users[msg.Receiver]; exists {
			fmt.Printf("Routing message to user %s: %s\n", msg.Receiver, msg.Payload)
		} else {
			return errors.New("user does not exist")
		}
	} else {
		return errors.New("message must have a channel or a receiver")
	}

	return nil
}

// GetSubscriptions retrieves all channels a user is subscribed to
func (r *Router) GetSubscriptions(user string) ([]string, error) {
	r.Mutex.RLock()
	defer r.Mutex.RUnlock()

	if channels, exists := r.Users[user]; exists {
		return channels, nil
	}
	return nil, errors.New("user not found")
}

// GetSubscribers retrieves all users subscribed to a channel
func (r *Router) GetSubscribers(channel string) ([]string, error) {
	r.Mutex.RLock()
	defer r.Mutex.RUnlock()

	if subscribers, exists := r.Channels[channel]; exists {
		return subscribers, nil
	}
	return nil, errors.New("channel not found")
}

// UnsubscribeAll removes all channel subscriptions for a user
func (r *Router) UnsubscribeAll(user string) error {
	r.Mutex.Lock()
	defer r.Mutex.Unlock()

	if channels, exists := r.Users[user]; exists {
		for _, channel := range channels {
			if subs, exists := r.Channels[channel]; exists {
				for i, u := range subs {
					if u == user {
						r.Channels[channel] = append(subs[:i], subs[i+1:]...)
						break
					}
				}
			}
		}
		delete(r.Users, user)
		fmt.Printf("Unsubscribed user %s from all channels\n", user)
		return nil
	}
	return errors.New("user not found")
}

// AddChannel creates a new channel
func (r *Router) AddChannel(channel string) error {
	r.Mutex.Lock()
	defer r.Mutex.Unlock()

	if _, exists := r.Channels[channel]; exists {
		return errors.New("channel already exists")
	}
	r.Channels[channel] = []string{}
	fmt.Printf("Channel %s created\n", channel)
	return nil
}

// RemoveChannel deletes a channel and unsubscribes all users
func (r *Router) RemoveChannel(channel string) error {
	r.Mutex.Lock()
	defer r.Mutex.Unlock()

	if _, exists := r.Channels[channel]; exists {
		for _, user := range r.Channels[channel] {
			if subs, exists := r.Users[user]; exists {
				for i, ch := range subs {
					if ch == channel {
						r.Users[user] = append(subs[:i], subs[i+1:]...)
						break
					}
				}
			}
		}
		delete(r.Channels, channel)
		fmt.Printf("Channel %s removed\n", channel)
		return nil
	}
	return errors.New("channel not found")
}

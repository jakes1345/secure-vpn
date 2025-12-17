package mesh

import (
	"fmt"
	"net"
	"sync"
	"time"
)

// Route represents a path through the mesh network
type Route struct {
	Hops    []*Hop
	Latency time.Duration
	Score   float64 // Trust + performance score
}

// Hop represents one node in a route
type Hop struct {
	NodeID  [20]byte
	Addr    *net.UDPAddr
	Encrypted bool // Traffic is encrypted, node can't see it
}

// MeshRouter handles routing through the mesh network
type MeshRouter struct {
	routes map[string]*Route // destination -> route
	nodes  map[[20]byte]*Node
	mu     sync.RWMutex
}

// Node represents a node in the mesh
type Node struct {
	ID         [20]byte
	Addr       *net.UDPAddr
	Reputation int
	Latency    time.Duration
	LastSeen   time.Time
	IsActive   bool
}

// NewMeshRouter creates a new mesh router
func NewMeshRouter() *MeshRouter {
	return &MeshRouter{
		routes: make(map[string]*Route),
		nodes:  make(map[[20]byte]*Node),
	}
}

// FindRoute finds the best route to a destination
func (mr *MeshRouter) FindRoute(destIP string) (*Route, error) {
	mr.mu.RLock()
	defer mr.mu.RUnlock()

	// Check if we have a cached route
	if route, exists := mr.routes[destIP]; exists {
		// Verify route is still valid
		if mr.isRouteValid(route) {
			return route, nil
		}
		// Route invalid, remove it
		delete(mr.routes, destIP)
	}

	// Find best route using Dijkstra's algorithm (simplified)
	route := mr.findBestRoute(destIP)
	if route == nil {
		return nil, fmt.Errorf("no route found to %s", destIP)
	}

	// Cache the route
	mr.routes[destIP] = route

	return route, nil
}

// findBestRoute finds the best route using shortest path
func (mr *MeshRouter) findBestRoute(destIP string) *Route {
	// Simplified routing - in production would use proper graph algorithms
	// For now, find route with:
	// 1. Highest reputation
	// 2. Lowest latency
	// 3. Fewest hops

	var bestRoute *Route
	bestScore := 0.0

	// Try direct connection first
	for _, node := range mr.nodes {
		if !node.IsActive {
			continue
		}

		// Calculate score
		score := float64(node.Reputation) / (float64(node.Latency.Milliseconds()) + 1)
		
		if score > bestScore {
			bestScore = score
			bestRoute = &Route{
				Hops: []*Hop{
					{
						NodeID:    node.ID,
						Addr:      node.Addr,
						Encrypted: true, // All traffic encrypted
					},
				},
				Latency: node.Latency,
				Score:   score,
			}
		}
	}

	return bestRoute
}

// isRouteValid checks if a route is still valid
func (mr *MeshRouter) isRouteValid(route *Route) bool {
	for _, hop := range route.Hops {
		mr.mu.RLock()
		node, exists := mr.nodes[hop.NodeID]
		mr.mu.RUnlock()

		if !exists || !node.IsActive {
			return false
		}

		// Check if node is still responsive
		if time.Since(node.LastSeen) > 5*time.Minute {
			return false
		}
	}

	return true
}

// AddNode adds a node to the mesh
func (mr *MeshRouter) AddNode(node *Node) {
	mr.mu.Lock()
	defer mr.mu.Unlock()
	mr.nodes[node.ID] = node
}

// RemoveNode removes a node
func (mr *MeshRouter) RemoveNode(nodeID [20]byte) {
	mr.mu.Lock()
	defer mr.mu.Unlock()
	delete(mr.nodes, nodeID)

	// Remove routes using this node
	for dest, route := range mr.routes {
		for _, hop := range route.Hops {
			if hop.NodeID == nodeID {
				delete(mr.routes, dest)
				break
			}
		}
	}
}

// UpdateNode updates node information
func (mr *MeshRouter) UpdateNode(nodeID [20]byte, latency time.Duration, reputation int) {
	mr.mu.Lock()
	defer mr.mu.Unlock()

	if node, exists := mr.nodes[nodeID]; exists {
		node.Latency = latency
		node.Reputation = reputation
		node.LastSeen = time.Now()
	}
}


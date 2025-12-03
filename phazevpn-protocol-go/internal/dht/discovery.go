package dht

import (
	"context"
	"crypto/rand"
	"encoding/binary"
	"fmt"
	"net"
	"sync"
	"time"

	"github.com/anacrolix/dht/v2"
	"github.com/anacrolix/dht/v2/krpc"
)

// Node represents a peer in the DHT network
type Node struct {
	ID       [20]byte
	Addr     *net.UDPAddr
	LastSeen time.Time
	Reputation int // Trust score
}

// DHTDiscovery handles peer discovery via DHT
type DHTDiscovery struct {
	dhtServer *dht.Server
	nodes     map[string]*Node
	mu        sync.RWMutex
	ctx       context.Context
	cancel    context.CancelFunc
}

// NewDHTDiscovery creates a new DHT discovery instance
func NewDHTDiscovery(port int) (*DHTDiscovery, error) {
	ctx, cancel := context.WithCancel(context.Background())

	// Generate random node ID
	var nodeID [20]byte
	rand.Read(nodeID[:])

	// Create DHT server
	s, err := dht.NewServer(&dht.ServerConfig{
		Conn:          nil, // Will create UDP conn
		StartingNodes: dht.GlobalBootstrapAddrs,
		NodeId:        nodeID,
	})
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to create DHT server: %w", err)
	}

	// Start DHT server
	if err := s.Start(); err != nil {
		cancel()
		return nil, fmt.Errorf("failed to start DHT server: %w", err)
	}

	return &DHTDiscovery{
		dhtServer: s,
		nodes:     make(map[string]*Node),
		ctx:       ctx,
		cancel:    cancel,
	}, nil
}

// DiscoverPeers discovers other VPN nodes in the network
func (d *DHTDiscovery) DiscoverPeers(targetID [20]byte) ([]*Node, error) {
	// Search for peers with similar ID (VPN nodes)
	results := d.dhtServer.GetPeers(krpc.NodeInfo{
		Addr: net.UDPAddr{},
		Id:   targetID,
	})

	var peers []*Node
	for result := range results {
		if result.Err != nil {
			continue
		}

		for _, addr := range result.Peers {
			node := &Node{
				ID:       result.NodeInfo.Id,
				Addr:     addr,
				LastSeen: time.Now(),
			}
			peers = append(peers, node)
		}
	}

	return peers, nil
}

// Announce announces this node to the DHT
func (d *DHTDiscovery) Announce(infoHash [20]byte, port int) error {
	// Announce this node's presence
	_, err := d.dhtServer.Announce(infoHash, port, true)
	return err
}

// GetNodes returns all known nodes
func (d *DHTDiscovery) GetNodes() []*Node {
	d.mu.RLock()
	defer d.mu.RUnlock()

	nodes := make([]*Node, 0, len(d.nodes))
	for _, node := range d.nodes {
		nodes = append(nodes, node)
	}
	return nodes
}

// AddNode adds a node to the network
func (d *DHTDiscovery) AddNode(node *Node) {
	d.mu.Lock()
	defer d.mu.Unlock()

	key := fmt.Sprintf("%x-%s", node.ID, node.Addr.String())
	d.nodes[key] = node
}

// RemoveNode removes a node
func (d *DHTDiscovery) RemoveNode(nodeID [20]byte) {
	d.mu.Lock()
	defer d.mu.Unlock()

	for key, node := range d.nodes {
		if node.ID == nodeID {
			delete(d.nodes, key)
			break
		}
	}
}

// Close closes the DHT discovery
func (d *DHTDiscovery) Close() {
	d.cancel()
	if d.dhtServer != nil {
		d.dhtServer.Close()
	}
}


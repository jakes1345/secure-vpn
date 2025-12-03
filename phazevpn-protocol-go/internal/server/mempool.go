package server

import (
	"sync"
)

// MemoryPool manages reusable buffers to reduce allocations
type MemoryPool struct {
	buffers sync.Pool
}

var globalPool = &MemoryPool{
	buffers: sync.Pool{
		New: func() interface{} {
			// Pre-allocate 1500 byte buffers (typical MTU)
			return make([]byte, 1500)
		},
	},
}

// GetBuffer gets a buffer from the pool
func (p *MemoryPool) GetBuffer() []byte {
	return globalPool.buffers.Get().([]byte)
}

// PutBuffer returns a buffer to the pool
func (p *MemoryPool) PutBuffer(buf []byte) {
	// Only return buffers of expected size
	if cap(buf) >= 1500 {
		globalPool.buffers.Put(buf[:1500])
	}
}

// GetLargeBuffer gets a larger buffer (for jumbo frames)
func (p *MemoryPool) GetLargeBuffer() []byte {
	return make([]byte, 9000) // Jumbo frame size
}


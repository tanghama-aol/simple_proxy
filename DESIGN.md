# Simple Proxy - Design Document

## 1. Overview
Simple Proxy is a local proxy server that provides flexible routing capabilities based on IP patterns. It allows users to configure routing rules through a web interface, similar to Switchy Omega.

## 2. System Architecture

### 2.1 Core Components
1. **Proxy Server**
   - Local HTTP/HTTPS proxy server
   - Handles incoming connections
   - Routes traffic based on configured rules

2. **Configuration Manager**
   - Manages proxy rules and settings
   - Handles configuration persistence
   - Provides configuration API

3. **Web Interface**
   - Simple HTML/JS interface
   - Rule management UI
   - Real-time configuration updates

### 2.2 Key Features
- Local proxy server (HTTP/HTTPS)
- Multiple proxy modes:
  - Direct connection
  - Through proxy server
- Rule-based routing using IP suffix regex
- Web-based configuration interface
- Configuration persistence
- Real-time rule updates

## 3. Technical Specifications

### 3.1 Core Server
- Python-based implementation
- Async IO for better performance
- Support for HTTP/HTTPS protocols

### 3.2 Configuration Format
```json
{
    "default_mode": "direct",  // "direct" or "proxy"
    "proxy_settings": {
        "default_proxy": {
            "host": "proxy.example.com",
            "port": 8080,
            "type": "http"  // http/socks5
        }
    },
    "rules": [
        {
            "pattern": "192\\.168\\.*",
            "action": "direct"
        },
        {
            "pattern": "10\\..*",
            "proxy": "default_proxy"
        }
    ]
}
```

### 3.3 Web Interface
- Simple and responsive design
- Real-time rule management
- Configuration import/export
- Rule testing functionality

## 4. Implementation Plan

### 4.1 Phase 1: Core Proxy Server
- Set up basic HTTP/HTTPS proxy server
- Implement direct connection handling
- Add proxy connection support
- Basic configuration loading

### 4.2 Phase 2: Rule Engine
- Implement regex pattern matching
- Add rule evaluation logic
- Create configuration manager
- Add rule persistence

### 4.3 Phase 3: Web Interface
- Create basic HTML/JS interface
- Implement configuration API
- Add real-time rule updates
- Include rule testing functionality

## 5. Security Considerations
- Local-only access to web interface
- Configuration validation
- Proper error handling
- Secure proxy connection handling

## 6. Testing Strategy
- Unit tests for core components
- Integration tests for proxy functionality
- Rule pattern testing
- Web interface testing
- Performance testing

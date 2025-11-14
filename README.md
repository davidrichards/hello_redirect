# Hello HelloRedirect

A proof-of-concept demonstrating secure token-based redirection between a gateway service and runtime containers using JWS + JWE-style nested encryption.

[Demo Video](https://youtube.com/live/Db2MKtGcfyc)

This is a self-documenting tool. Do things. Be grounded. Ask questions. Validate answers. Have fun.


## Architecture

- **Gateway Service** (`gateway_app.py`) - Receives user requests, allocates runtime, creates encrypted tokens, and redirects users
- **Runtime Service** (`runtime_app.py`) - Validates and decrypts tokens, displays user information
- **Security Module** (`security.py`) - Handles JWT signing and Fernet encryption for nested token security
- **Allocator** - Routes users to appropriate runtime instances (supports both static and dynamic allocation)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Make (optional, but recommended)

### Setup and Run

1. **Build and start services:**
   ```bash
   make dev-setup
   ```
   
   Or manually:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

2. **Test the complete flow:**
   ```bash
   make test-e2e
   ```

3. **Access the services:**
   - Gateway: http://localhost:8000/
   - Runtime: http://localhost:8001/health

### Testing the Flow

1. **Visit the gateway:** http://localhost:8000/
   - The gateway will inspect your request headers and cookies
   - It creates an encrypted token with user information
   - It redirects you to the runtime with the token

2. **The runtime receives you:**
   - Validates and decrypts the token
   - Displays your user ID and features
   - Shows that the token was securely processed

## Development

### Available Make Commands

- `make help` - Show all available commands
- `make dev-setup` - Build and start development environment
- `make docker-build` - Build Docker images
- `make docker-up` - Start services
- `make docker-down` - Stop services
- `make docker-logs` - View service logs
- `make test-e2e` - Run end-to-end tests
- `make dev-reset` - Complete reset (clean, build, start)

### Manual Testing

You can test different user scenarios by setting cookies:

```bash
# Basic user
curl -H "User-Agent: test-browser" http://localhost:8000/

# Advanced user with cookies
curl -H "User-Agent: test-browser" \\
     -H "Cookie: rbt_session=test123; rbt_advanced=true" \\
     http://localhost:8000/
```

### Architecture Details

#### Token Security
- **JWT (JWS)**: Claims are signed to prevent tampering
- **Fernet (JWE-style)**: The entire JWT is then encrypted for confidentiality
- **Nested Security**: Provides both integrity and confidentiality

#### Allocation Strategies
- **Simple Allocator**: Routes all users to a single runtime (Docker Compose default)
- **Docker Allocator**: Dynamically creates per-user containers (set `USE_DOCKER_ALLOCATOR=true`)

#### Configuration
Environment variables:
- `JWT_SIGNING_SECRET`: Secret for JWT signing
- `FERNET_KEY`: Key for Fernet encryption
- `USE_DOCKER_ALLOCATOR`: Enable dynamic container allocation
- `RUNTIME_HOST`: Runtime service hostname
- `RUNTIME_PORT`: Runtime service port

## Security Features

1. **Token Expiration**: Tokens expire after 5 minutes
2. **Nested Encryption**: Claims are signed then encrypted
3. **Secure Headers**: All security-related data is in encrypted tokens
4. **Isolated Runtimes**: Each user can have their own container (with Docker allocator)

## Production Considerations

- Set strong secrets for `JWT_SIGNING_SECRET` and `FERNET_KEY`
- Use HTTPS in production
- Implement proper session management
- Add rate limiting and abuse protection
- Consider using a proper secret management system
- Implement container lifecycle management for dynamic allocation
- Add monitoring and logging

## File Structure

```
.
├── gateway_app.py          # Gateway service
├── runtime_app.py          # Runtime service  
├── security.py            # JWT/encryption utilities
├── docker_allocator.py    # Dynamic container allocation
├── simple_allocator.py    # Static runtime allocation
├── runtime_registry.py    # Runtime state management
├── Dockerfile.gateway     # Gateway container
├── Dockerfile.runtime     # Runtime container
├── docker-compose.yml     # Service orchestration
├── test_e2e.py           # End-to-end testing
├── Makefile              # Development commands
└── requirements.txt      # Python dependencies
```

## Extending the POC

1. **Add Authentication**: Integrate with OAuth, SAML, or other auth providers
2. **Enhanced Features**: Implement more sophisticated feature detection
3. **Load Balancing**: Add runtime load balancing and health checks  
4. **Persistent State**: Add database for user sessions and runtime state
5. **Monitoring**: Add metrics, logging, and observability
6. **Security**: Implement CSP, CORS, and other security headers

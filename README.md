# AIOServer
Trio Server and Client

## Server
Combines: Connection, Server, and 3rd party Services handling all in one trio nursery

## Client
Two options here: either TUI (Text User Interface) or Client

### Background
All connections will operate over asyncio TCP connections

All threads will have their own asyncio event loop

All services must be awaitable

## Security
Connections will automatically implement RSA and AES authentication based on whether the Client connection is unauthorized, or registered (respectively)

All new connections will connect to the server using the server public RSA key

Upon RSA key exchange, all communication will be transferred to AES encryption

## Communication
All communication between client and server will be through AIOMessage Google protobuf messages

All services must define their own google protobuf message
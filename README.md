# Concurrent Python Socket Server

A lightweight, non-blocking Python socket server that uses `select.poll()` to handle multiple client connections simultaneously. The server implements a custom state-based communication protocol to receive binary-packed data, execute algorithmic operations, and return the computed results to the client.

## Features

* **Asynchronous I/O:** Uses `select.poll()` and non-blocking sockets to manage multiple client states concurrently without threads.
* **Custom State Machine:** Tracks each client's communication phase (`WAITING_OP_ID`, `WAITING_HEADER`, `WAITING_PAYLOAD`) to handle fragmented data transmission cleanly.
* **Binary Data Packing:** Utilizes Python's `struct` module to pack and unpack data payloads (handling floats, integers, and unsigned shorts) securely over the network.
* **Connection Throttling:** Automatically caps the maximum number of handled connections to 5 before cleanly shutting down.

## Supported Operations

Clients can request three specific operations by sending the corresponding Operation ID:

1. **Find Maximum (`op_id = 1`):** Accepts a list of integers (between -100 and 100) and returns the maximum value as a signed byte.
2. **Merge Sort (`op_id = 2`):** Accepts a list of floats (between 0 and 200) and returns the fully sorted array.
3. **List Intersection (`op_id = 3`):** Accepts two lists of integers (values up to 60,000) and returns an array of their common elements.

## Communication Protocol

Clients must communicate with the server using the following strict 3-phase protocol:

1. **Phase 1 (Operation ID):** Client sends the desired operation ID (`1`, `2`, or `3`) as a UTF-8 encoded string. Server replies with a status code (`0` for success) packed as an unsigned short (`!H`).
2. **Phase 2 (Header):** Client sends a 6-byte header containing the data lengths. The server calculates the expected payload size and necessary byte padding.
3. **Phase 3 (Payload):** Client sends the actual array data based on the chosen operation. The server validates the data bounds, executes the algorithm, and returns a binary-packed response.

## Prerequisites

* Python 3.6+
* No external dependencies required (uses built-in `socket`, `select`, and `struct` modules).

## Usage

1. Clone the repository.
2. Run the server script:
   ```bash
   python server.py

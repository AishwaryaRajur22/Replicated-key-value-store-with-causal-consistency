# Replicated key-value store with causal consistency 

This project is a **replicated, fault-tolerant, and causally consistent key-value store**. It is designed to ensure data availability and consistency in distributed systems through replication and causal metadata tracking.

## Features

- **Replication and Fault Tolerance:** Data is replicated across multiple instances (replicas), ensuring availability even if one replica goes down.
- **Causal Consistency:** Each replica communicates state changes (like additions or deletions of keys) while respecting causal order to maintain consistency.
- **Dynamic Cluster Management:** The system can dynamically add or remove replicas in the cluster, adapting to changes without compromising data consistency.
- **RESTful API Support:** Endpoints support standard CRUD operations (Create, Read, Update, Delete) with causal metadata to ensure consistency across requests.

## API Endpoints

1. **View Operations** (`/view`)
   - **PUT:** Add a new replica to the view.
   - **GET:** Retrieve the current view of replicas.
   - **DELETE:** Remove a replica from the view.

2. **Key-Value Operations** (`/kvs`)
   - **PUT:** Add or update key-value pairs with causal dependency tracking.
   - **GET:** Retrieve values based on key.
   - **DELETE:** Remove key-value pairs.

## Causal Consistency Mechanism

The project uses causal metadata to track dependencies and ensures each replica applies operations in the correct causal order. Metadata is propagated through requests, allowing clients to see a consistent view of the store.

## Running the Project

1. **Build the Docker Image:**
   ```bash
   docker build -t dashboard-img .
2. **Create Docker Network:**
   ```bash
   docker network create --subnet=10.10.0.0/16 asg3net
3. **Run Instances:**
   ```bash
   docker run --rm -p 8082:8090 --net=asg3net --ip=10.10.0.2 -e SOCKET_ADDRESS=10.10.0.2:8090 -e VIEW=10.10.0.2:8090,10.10.0.3:8090,10.10.0.4:8090 dashboard-img
   docker run --rm -p 8083:8090 --net=asg3net --ip=10.10.0.3 -e SOCKET_ADDRESS=10.10.0.3:8090 -e VIEW=10.10.0.2:8090,10.10.0.3:8090,10.10.0.4:8090 dashboard-img
   docker run --rm -p 8084:8090 --net=asg3net --ip=10.10.0.4 -e SOCKET_ADDRESS=10.10.0.4:8090 -e VIEW=10.10.0.2:8090,10.10.0.3:8090,10.10.0.4:8090 dashboard-img
   
## Testing

You can run `test_assignment3.py` to validate the project’s functionality. The script tests for causal consistency and correctness of API responses.

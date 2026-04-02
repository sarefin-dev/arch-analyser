# Architecture analysis report

**Input:** `baggage reconciliation system, 10k bags/hour, event-sourced, Kafka, Oracle, IATA Type B messaging, BSM/BPM messages`  
**Generated:** 2026-04-03 03:35  
**Pipeline:** P1 context > P2 decompose > P3 patterns > P4 risks > P5 synthesis

---

## System summary

Baggage Reconciliation System processing IATA Type B messaging (BSM/BPM) using event-sourced architecture with Kafka message broker and Oracle database for materialized views. Designed for 10k bags/hour throughput with event sourcing as the architectural foundation, employing CQRS pattern for separating write (event stream) and read (Oracle projections) concerns. System uses stateless service layer consuming from Kafka partitions with parallel reconciliation workers for horizontal scaling.

---

## Counts

| | |
|---|---|
| Components | 21 |
| Patterns | 24 |
| Risks (total) | 38 |
| P1-BLOCKING | 15 |
| P2-HIGH | 15 |
| P3-MEDIUM | 8 |
| CROSS-BRANCH | 0 |

---

## Components

| Component | Responsibility | State | Source |
|---|---|---|---|
| Kafka Message Broker | Durably store and distribute baggage event streams (BSM/BPM messages) to consumers with ordering and replay guarantees. | STATEFUL | SPECIFIED |
| Oracle Database | Persist reconciled baggage state, transaction records, and queryable baggage history. | STATEFUL | SPECIFIED |
| Event Store | Store immutable sequence of all baggage events as the source of truth for event-sourced architecture. | STATEFUL | INFERRED |
| Read Model Cache | Cache materialized views of baggage state to reduce database query load and improve read performance. | STATEFUL | INFERRED |
| Schema Registry | Manage and version schemas for IATA Type B message formats and internal event structures. | STATEFUL | INFERRED |
| Distributed Tracing System | Capture and correlate request flows across services for end-to-end baggage event processing visibility. | STATEFUL | INFERRED |
| IATA Type B Message Parser Service | Parse and validate incoming BSM/BPM messages according to IATA Type B specifications. | STATELESS | INFERRED |
| Event Ingestion Service | Receive baggage events from external systems and publish to Kafka topics with appropriate routing. | STATELESS | INFERRED |
| Baggage Reconciliation Engine | Process baggage events from Kafka, apply reconciliation business logic, and identify discrepancies. | STATELESS | INFERRED |
| Event Projection Service | Consume events from Kafka and materialize read models into Oracle database for querying. | STATELESS | INFERRED |
| State Query Service | Provide current baggage state by querying materialized read models from Oracle and cache. | STATELESS | INFERRED |
| Reconciliation Worker Pool | Execute reconciliation tasks in parallel by consuming events from Kafka partitions for throughput scaling. | STATELESS | INFERRED |
| Exception Handler Service | Process reconciliation exceptions, baggage discrepancies, and routing errors requiring intervention. | STATELESS | INFERRED |
| Snapshot Service | Periodically create baggage state snapshots from event stream to optimize event replay performance. | STATELESS | INFERRED |
| Replay Coordinator | Manage event stream replay operations for rebuilding read models or recovering from failures. | STATELESS | INFERRED |
| Dead Letter Queue Processor | Handle failed message processing attempts and implement retry logic with exponential backoff. | STATELESS | INFERRED |
| API Gateway | Route external API requests, enforce rate limiting, and provide unified entry point for baggage queries. | STATELESS | INFERRED |
| Load Balancer | Distribute incoming traffic across service instances to ensure availability and performance. | STATELESS | INFERRED |
| Authentication Service | Verify identity of systems and users accessing baggage reconciliation data and APIs. | STATELESS | INFERRED |
| Authorization Service | Enforce access control policies determining which entities can view or modify baggage information. | STATELESS | INFERRED |
| API Rate Limiter | Throttle request rates per client to protect backend services from overload. | HYBRID | INFERRED |

---

## Patterns

### REQUIRED

| Pattern | Applies to | Rationale |
|---|---|---|
| Kafka Partition Ordering Guarantee | Kafka Message Broker, Baggage Reconciliation Engine, Reconciliation Worker Pool | The Baggage Reconciliation Engine requires ordered processing of BSM/BPM events per bag to prevent reconciliation logic from processing out-of-sequence events that would produce incorrect baggage state. |
| At-Least-Once Delivery | Kafka Message Broker, Event Ingestion Service, Baggage Reconciliation Engine | The Event Ingestion Service requires at-least-once delivery to prevent baggage event loss which would create undetectable gaps in the event stream causing permanent reconciliation failures. |
| Idempotent Consumer | Baggage Reconciliation Engine, Event Projection Service, Reconciliation Worker Pool | The Baggage Reconciliation Engine requires idempotent processing because at-least-once delivery guarantees from Kafka will produce duplicate events that would otherwise corrupt baggage state or double-count reconciliation outcomes. |
| Event Sourcing | Event Store, Baggage Reconciliation Engine, Event Projection Service, Snapshot Service | The Event Store requires immutable event append operations as the specified event-sourced architecture pattern makes the event log the source of truth for all baggage state reconstruction. |
| CQRS (Command Query Responsibility Segregation) | Event Projection Service, State Query Service, Oracle Database, Read Model Cache | The Event Projection Service requires separation of write and read models because event-sourced writes to Kafka and queryable reads from Oracle Database serve fundamentally different access patterns that cannot be efficiently served by a single model. |
| Eventual Consistency | Event Projection Service, Read Model Cache, State Query Service | The Event Projection Service produces eventual consistency between Kafka event stream and Oracle read models because asynchronous projection cannot guarantee immediate consistency without blocking event ingestion throughput. |
| Consumer Group Partitioning | Reconciliation Worker Pool, Kafka Message Broker | The Reconciliation Worker Pool requires Kafka consumer group partitioning to achieve horizontal scaling to meet the 10k bags/hour throughput requirement through parallel processing. |
| Dead Letter Queue | Dead Letter Queue Processor, Kafka Message Broker, Baggage Reconciliation Engine | The Dead Letter Queue Processor requires a dedicated queue for poison messages to prevent repeatedly failing BSM/BPM messages from blocking partition consumption and creating cascading baggage reconciliation delays. |
| Retry with Exponential Backoff | Dead Letter Queue Processor, Event Ingestion Service, Baggage Reconciliation Engine | The Dead Letter Queue Processor requires exponential backoff to prevent retry storms from overwhelming downstream services during transient failures while allowing eventual recovery. |
| Schema Evolution with Compatibility Guarantees | Schema Registry, IATA Type B Message Parser Service, Event Ingestion Service | The Schema Registry requires backward/forward compatibility enforcement to prevent deployment of incompatible IATA Type B message schema changes that would break in-flight event processing across service versions. |
| Snapshot Pattern for Event Replay Optimization | Snapshot Service, Event Store, Replay Coordinator | The Snapshot Service requires periodic state snapshots because replaying unbounded event streams from the Event Store would exceed acceptable recovery time as event volume grows over operational lifetime. |
| Materialized View Pattern | Event Projection Service, Oracle Database, State Query Service | The Event Projection Service requires pre-computed materialized views in Oracle Database because reconstructing baggage state from raw events at query time would violate read performance requirements. |
| Correlation ID Propagation | Distributed Tracing System, IATA Type B Message Parser Service, Baggage Reconciliation Engine, Event Projection Service | The Distributed Tracing System requires correlation IDs threaded through all service calls to trace individual baggage events through asynchronous processing stages for debugging reconciliation failures. |
| Competing Consumers | Reconciliation Worker Pool, Kafka Message Broker | The Reconciliation Worker Pool requires multiple consumers competing for Kafka partition assignments to achieve horizontal scaling necessary for 10k bags/hour throughput target. |
| Message Validation at Entry Point | IATA Type B Message Parser Service, Event Ingestion Service | The IATA Type B Message Parser Service requires strict schema validation before publishing to Kafka to prevent invalid messages from poisoning the event stream and breaking downstream reconciliation logic. |

### RECOMMENDED

| Pattern | Applies to | Rationale |
|---|---|---|
| Circuit Breaker | Baggage Reconciliation Engine, Event Projection Service, State Query Service, Oracle Database | The Baggage Reconciliation Engine should implement circuit breakers to Oracle Database to prevent cascading failures where slow database queries block Kafka consumer threads and cause partition lag buildup. |
| Bulkhead Isolation | Reconciliation Worker Pool, Baggage Reconciliation Engine | The Reconciliation Worker Pool should isolate thread pools per Kafka partition to prevent failures processing one partition from exhausting resources needed for healthy partitions. |
| Cache-Aside Pattern | Read Model Cache, State Query Service, Oracle Database | The State Query Service should implement cache-aside loading to reduce Oracle Database query load for frequently accessed baggage states while maintaining cache consistency with database updates. |
| Request Timeout | State Query Service, API Gateway, Oracle Database | The State Query Service should enforce query timeouts to Oracle Database to prevent slow queries from blocking API Gateway threads and degrading overall system responsiveness. |
| API Rate Limiting (Token Bucket) | API Rate Limiter, API Gateway | The API Rate Limiter should implement token bucket algorithm to protect State Query Service and Oracle Database from query floods that could degrade reconciliation throughput. |
| Load Balancing with Health Checks | Load Balancer, API Gateway, State Query Service | The Load Balancer should actively health-check State Query Service instances to route traffic away from failing nodes and maintain query availability. |
| Backpressure Propagation | Event Ingestion Service, Kafka Message Broker, Baggage Reconciliation Engine | The Event Ingestion Service should signal backpressure to external publishers when Kafka broker cannot accept messages at offered rate to prevent memory exhaustion. |

### OPTIONAL

| Pattern | Applies to | Rationale |
|---|---|---|
| Write-Through Cache | Event Projection Service, Read Model Cache, Oracle Database | The Event Projection Service could write-through to Read Model Cache when updating Oracle Database to reduce cache miss rate but eventual consistency model allows lazy cache population. |
| Transactional Outbox | Event Projection Service, Oracle Database, Kafka Message Broker | The Event Projection Service could use transactional outbox to atomically update Oracle Database and publish derived events to Kafka but current architecture does not specify such dual-write scenarios. |

---

## Risks

### P1 — blocking

**Single Kafka Cluster SPOF** `INFRASTRUCTURE`  
Single Kafka cluster with insufficient replication creates SPOF. Broker disk failure loses events if replication factor < 3. Network partition between brokers causes split-brain if no quorum. ZooKeeper/KRaft metadata service failure halts all broker operations.
> **Mitigation:** Deploy Kafka cluster with replication factor >= 3, minimum 3 brokers across availability zones, enable KRaft quorum or ZooKeeper ensemble (3+ nodes), configure min.insync.replicas >= 2, implement cross-region replication for disaster recovery.

**Single Oracle Instance SPOF** `INFRASTRUCTURE`  
Single Oracle instance without RAC/DataGuard is complete SPOF. Disk array failure loses all reconciled state and read models. Network isolation from services halts all queries and projections. Tablespace exhaustion prevents new reconciliation state writes.
> **Mitigation:** Deploy Oracle RAC for high availability or Oracle DataGuard for standby failover. Implement RAID storage with redundancy. Configure tablespace auto-extend with monitoring and alerting. Establish network redundancy with multiple paths to database.

**Event Store Single Instance SPOF** `INFRASTRUCTURE`  
If Event Store is separate from Kafka: single instance loses all history. Disk failure without RAID/replication loses source of truth. Network partition prevents event appends and replay operations. Storage exhaustion prevents new event ingestion.
> **Mitigation:** If Event Store is separate from Kafka, deploy with replication (e.g., EventStoreDB clustering). Use RAID storage or cloud-native replicated storage. Implement storage monitoring with auto-scaling or alerting. Establish network redundancy.

**Schema Registry Single Instance SPOF** `INFRASTRUCTURE`  
Single Schema Registry instance prevents new schema validation. Disk failure loses schema versions breaking compatibility checks. Network isolation prevents message parser from validating schemas.
> **Mitigation:** Deploy Schema Registry in clustered mode with multiple instances backed by Kafka topic for storage. Enable replication for the underlying Kafka topic. Implement health checks and automatic failover.

**Non-Idempotent Reconciliation Logic Data Corruption** `SOFTWARE`  
Kafka → Reconciliation Engine interaction: non-idempotent reconciliation logic with duplicate events corrupts bag state. At-least-once delivery without deduplication causes duplicate events in stream that would corrupt baggage state or double-count reconciliation outcomes.
> **Mitigation:** Implement idempotent reconciliation logic using event IDs for deduplication. Store processed event IDs in Oracle with bag state. Use database constraints to prevent duplicate processing. Apply idempotency keys to all state mutations.

**Lost Updates from Concurrent Projections** `SOFTWARE`  
Reconciliation Engine → Oracle interaction: concurrent projections updating same bag record without optimistic locking causes lost updates. Race condition where multiple projection workers overwrite each other's state changes.
> **Mitigation:** Implement optimistic locking using version columns in Oracle tables. Use Kafka partition key on bag ID to ensure single consumer processes events for each bag. Apply database-level constraints to detect concurrent modifications.

**Dual-Write Consistency Failure** `SOFTWARE`  
Event Projection Service → Oracle/Kafka interaction: projection service crashes after Oracle commit but before Kafka offset commit causes duplicate projections. Creates inconsistency between processed events and committed offsets.
> **Mitigation:** Store Kafka offsets in Oracle database transactionally with projection data. On startup, read offsets from Oracle and seek to last committed position. Alternatively, use Kafka transactions to atomically commit offsets and ensure idempotent projections handle duplicates.

**Replay Concurrent with Live Processing Data Corruption** `SOFTWARE`  
Replay Coordinator → Kafka interaction: concurrent replay and live consumption processes same events causing duplicate projections. Race condition between replay consumer group and live consumer group both updating same read models.
> **Mitigation:** Use separate read model tables for replay operations. Implement replay mode flag that disables live consumption. Use dedicated consumer groups with different offsets. Coordinate replay with distributed lock to prevent concurrent execution.

**Partition Ordering Violation** `SOFTWARE`  
Event Ingestion → Kafka interaction: concurrent publishes of same bag ID without ordering key goes to different partitions. Violates partition ordering guarantee required for correct reconciliation state.
> **Mitigation:** Configure Kafka producer to use bag ID as partition key for all BSM/BPM messages. Validate partition key is set before publishing. Implement producer-level validation to reject messages without proper routing key.

**Invalid Message Poisoning Event Stream** `SOFTWARE`  
IATA Parser → Event Ingestion interaction: schema registry timeout causes parser to fail-open accepting invalid messages. Invalid BSM/BPM messages poison Kafka stream and break downstream reconciliation logic.
> **Mitigation:** Implement fail-closed validation: reject messages if Schema Registry is unavailable. Cache schemas locally with TTL for resilience. Require strict schema validation before Kafka publish with no bypass mechanisms. Route validation failures to separate dead letter topic.

**Snapshot Inconsistent State Capture** `SOFTWARE`  
Snapshot Service → Event Store interaction: snapshot created while events still being written captures inconsistent state. Snapshot metadata committed but snapshot data write fails causes invalid recovery point.
> **Mitigation:** Implement snapshot creation from stable offset position with no concurrent writes. Use database transactions to atomically write snapshot data and metadata. Validate snapshot integrity before marking as available for replay. Store offset position with snapshot.

**API Gateway Missing Authentication Unauthorized Access** `SECURITY`  
API Gateway external boundary: missing authentication allows anonymous access to bag data. No mutual TLS allows external system to impersonate legitimate baggage system. Missing request signature validation allows message modification in transit.
> **Mitigation:** Implement mutual TLS for all external API connections. Require client certificates for authentication. Implement request signature validation using HMAC or digital signatures. Deploy OAuth 2.0 or API key authentication for all endpoints.

**Event Ingestion Missing Client Validation Fake Event Injection** `SECURITY`  
Event Ingestion Service external boundary: no client certificate validation allows rogue system to inject fake BSM/BPM messages. Missing authorization allows any authenticated client to publish any bag event. No message signature validation allows event modification.
> **Mitigation:** Require mutual TLS with client certificate validation for all event publishers. Implement message-level digital signatures for BSM/BPM events. Apply authorization policies limiting which clients can publish events for specific airlines/airports. Log and audit all event sources.

**Oracle Database Missing Row-Level Encryption Data Tampering** `SECURITY`  
Oracle Database privileged operation: missing row-level encryption allows DBA to modify reconciliation records. Application service accounts shared across services hide true caller identity. Overly permissive grants allow services to read unrelated tables.
> **Mitigation:** Enable Oracle Transparent Data Encryption (TDE) for tablespaces. Implement row-level security policies with VPD (Virtual Private Database). Use separate service accounts per component with principle of least privilege. Enable database audit logging for all data modifications.

**Kafka Missing SASL Authentication Unauthorized Stream Access** `SECURITY`  
Kafka Message Broker privileged operation: no SASL authentication allows unauthorized producer/consumer connection. No TLS encryption allows network eavesdropper to modify events in transit.
> **Mitigation:** Enable Kafka SASL authentication (SASL/SCRAM or SASL/PLAIN with TLS). Configure Kafka ACLs restricting topic access per service account. Enable TLS encryption for all broker connections. Implement topic-level authorization for producers and consumers.

### P2 — high

**Kafka Disk Exhaustion Event Loss** `INFRASTRUCTURE`  
Kafka Message Broker: disk exhaustion from unbounded retention prevents new event writes. Broker rejects producers when disk watermark reached.

**Oracle Archive Log Disk Full Write Halt** `INFRASTRUCTURE`  
Oracle Database: archive log disk full stops all write transactions. Database enters suspended state until archive space available.

**Read Model Cache Cluster Failure Performance Degradation** `INFRASTRUCTURE`  
Read Model Cache cluster failure degrades query performance but not correctness. Memory exhaustion causes evictions impacting read performance. Network partition causes cache inconsistency across nodes.

**Distributed Tracing System SPOF Observability Loss** `INFRASTRUCTURE`  
Single tracing collector creates observability SPOF. Disk failure loses historical trace data for debugging. Storage exhaustion drops traces impacting incident response.

**Kafka Backpressure Blocks Ingestion Threads** `SOFTWARE`  
Event Ingestion → Kafka interaction: Kafka broker slow response blocks ingestion threads exhausting connection pool. Unbounded publishing rate exhausts Kafka broker memory causing backpressure.

**Consumer Rebalance Loses In-Flight Offsets** `SOFTWARE`  
Kafka → Reconciliation Engine interaction: consumer rebalance during processing loses in-flight offset commits causing reprocessing. Slow Oracle query blocks consumer poll loop causing partition reassignment storm.

**Oracle Connection Pool Exhaustion Blocks Workers** `SOFTWARE`  
Reconciliation Engine → Oracle interaction: Oracle connection pool exhaustion from slow queries blocks all reconciliation workers. Creates cascading failure where worker threads wait indefinitely for database connections.

**Cache Update Without Oracle Write Consistency Failure** `SOFTWARE`  
Event Projection Service → Read Model Cache interaction: cache update succeeds but Oracle write fails leaves inconsistent state. Cache serves stale data that diverges from source of truth.

**Oracle Query Timeout Storm Exhausts API Threads** `SOFTWARE`  
State Query Service → Oracle interaction: Oracle slowdown causes query timeout storm exhausting API Gateway threads. Query flood without rate limiting exhausts Oracle connection pool.

**DLQ Processor Retry Storm Thread Exhaustion** `SOFTWARE`  
Dead Letter Queue Processor → Kafka interaction: DLQ processor retry storm on persistent failure exhausts thread pool. Unbounded DLQ growth from persistent parse failures exhausts disk.

**API Rate Limiter Distributed State Inconsistency** `SOFTWARE`  
API Rate Limiter state synchronization: distributed rate limiter nodes have inconsistent token counts allowing burst over limit. Rate limit state reset loses accumulated counts allowing immediate burst.

**State Query Service Missing Audit Trail Compliance Violation** `SECURITY`  
State Query Service privileged operation: missing query audit trail prevents compliance investigation. Over-privileged queries return passenger data not needed by caller.

**API Gateway Missing TLS PII Exposure** `SECURITY`  
API Gateway external boundary: missing TLS exposes bag PII data in transit. Missing audit logging prevents proving which system issued query.

**Event Ingestion Service Missing Event Attribution Repudiation** `SECURITY`  
Event Ingestion Service external boundary: missing event source attribution prevents identifying malicious event publisher. Logging raw BSM messages exposes passenger PII in logs.

**Oracle Missing Schema Change Audit Trail** `SECURITY`  
Oracle Database privileged operation: insufficient audit logging of schema changes and data modifications. Application account has DDL privileges allowing schema modification.

### P3 — medium

**Cache Miss During Projection Write Stale Read** `SOFTWARE`  
State Query Service → Oracle/Cache interaction: cache miss concurrent with projection write returns incomplete state. Reading from cache while projection updates Oracle serves stale data beyond acceptable window.

**Replay Rate Exhausts Oracle Write Capacity** `SOFTWARE`  
Replay Coordinator → Kafka/Event Store interaction: unbounded replay rate exhausts Oracle write capacity. Replay consumer group conflicts with live consumer group causing rebalance cascades.

**Snapshot Read During Heavy Write Degrades Ingestion** `SOFTWARE`  
Snapshot Service → Event Store interaction: snapshot read during heavy write load degrades event ingestion performance. Snapshot storage growth without compaction exhausts disk.

**Schema Registry Cache Invalidation Uses Stale Schema** `SOFTWARE`  
IATA Parser → Schema Registry interaction: schema registry cache invalidation during parse uses stale schema accepting invalid message. Schema validation CPU cost without rate limiting causes parser thread exhaustion.

**Token Revocation Race Allows Revoked Token** `SOFTWARE`  
Authentication Service → API Gateway interaction: token revocation and validation race allows revoked token to pass. Auth service cache and database disagree on token validity.

**Exception Handler Circular Dependency Deadlock** `SOFTWARE`  
Exception Handler → multiple services interaction: exception handler and reconciliation engine both update bag status causing conflict. Circular dependency between exception handler and reconciliation engine on shared resource.

**State Query Service Missing Query Complexity Limits DoS** `SECURITY`  
State Query Service privileged operation: no query complexity limits allow expensive queries exhausting Oracle. Missing field-level authorization exposes restricted bag attributes.

**API Gateway Missing Rate Limiting Query Flood DoS** `SECURITY`  
API Gateway external boundary: no rate limiting at gateway allows query flood. Missing authentication allows anonymous access to bag data.

---

## Unresolved assumptions

Re-run with these specified to sharpen the analysis:

- Latency/SLA requirements
- Compute infrastructure (cloud/on-premise, provider)
- High availability requirements
- Disaster recovery requirements
- Peak vs sustained throughput characteristics

---

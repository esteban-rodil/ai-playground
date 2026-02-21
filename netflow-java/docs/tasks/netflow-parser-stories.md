# NetFlow Parser — Story Breakdown

> Detailed user stories for implementing the NetFlow parser, grouped by milestone.
> Derived from the [Implementation Plan](../plans/netflow-parser-implementation-plan.md).

---

## Table of Contents

- [Milestone 1: Project Scaffolding](#milestone-1-project-scaffolding)
- [Milestone 2: Core Abstractions](#milestone-2-core-abstractions)
- [Milestone 3: NetFlow v5 Parser](#milestone-3-netflow-v5-parser)
- [Milestone 4: NetFlow v9 Parser](#milestone-4-netflow-v9-parser)
- [Milestone 5: CSV Generation](#milestone-5-csv-generation)
- [Milestone 6: Storage Abstraction & Implementations](#milestone-6-storage-abstraction--implementations)

---

## Story Format

Each story follows this structure:

| Field | Description |
|-------|-------------|
| **ID** | Unique identifier (M{milestone}.S{story}) |
| **Title** | Short description of the story |
| **Description** | What needs to be done and why |
| **Acceptance Criteria** | Conditions that must be met for the story to be considered complete |
| **Dependencies** | Stories that must be completed first |
| **Estimated Effort** | T-shirt size (XS, S, M, L, XL) |

---

## Milestone 1: Project Scaffolding

**Goal:** Bootable Spring Boot 4 application with Maven build, Netty UDP listener receiving and logging raw packets.

---

### M1.S1 — Initialize Maven Project

**Description:**
Create the root `pom.xml` with all required dependencies and plugins for the project. This establishes the build foundation that all subsequent milestones depend on.

**Acceptance Criteria:**
- [ ] `pom.xml` exists at `netflow-java/` root with `com.netflow` group ID
- [ ] Java 21 is configured as the source and target version
- [ ] Spring Boot 4.0.x parent POM or BOM is declared
- [ ] Dependencies declared: `spring-boot-starter`, `netty-transport`, `spock-core`, `spock-spring` (2.4-groovy-5.0), `groovy` (5.0.x), `testcontainers` BOM, `apache-commons-csv`
- [ ] Maven compiler plugin targets Java 21
- [ ] GMavenPlus plugin is configured for compiling Groovy test sources
- [ ] `mvn clean compile` succeeds with zero errors
- [ ] `mvn test` runs (even if no tests exist yet) without build failures

**Dependencies:** None
**Estimated Effort:** S

---

### M1.S2 — Create Spring Boot Application Entry Point

**Description:**
Create the `NetflowApplication.java` main class annotated with `@SpringBootApplication`. This is the bootstrap entry point for the entire application.

**Acceptance Criteria:**
- [ ] `NetflowApplication.java` exists at `src/main/java/com/netflow/`
- [ ] Class is annotated with `@SpringBootApplication`
- [ ] Contains a standard `public static void main(String[] args)` method
- [ ] Application starts successfully via `mvn spring-boot:run` (even without listeners)
- [ ] Application context loads without errors

**Dependencies:** M1.S1
**Estimated Effort:** XS

---

### M1.S3 — Create Default Application Configuration

**Description:**
Create the `application.yml` with baseline configuration properties for the UDP listener (port, buffer size). This externalizes settings so they can be overridden per environment.

**Acceptance Criteria:**
- [ ] `application.yml` exists at `src/main/resources/`
- [ ] Contains `netflow.listener.port` defaulting to `2055`
- [ ] Contains `netflow.listener.buffer-size` defaulting to `65535`
- [ ] Contains `netflow.listener.worker-threads` defaulting to `4`
- [ ] Application starts and binds properties correctly

**Dependencies:** M1.S2
**Estimated Effort:** XS

---

### M1.S4 — Configure Netty UDP Server

**Description:**
Create `NettyServerConfig.java` that configures a Netty `Bootstrap` for UDP datagram reception. The server must bind to the configurable port and use `NioDatagramChannel` with a `NioEventLoopGroup`.

**Acceptance Criteria:**
- [ ] `NettyServerConfig.java` exists at `src/main/java/com/netflow/config/`
- [ ] Reads port and worker-threads from `application.yml` via `@ConfigurationProperties` or `@Value`
- [ ] Creates a Netty `Bootstrap` bean configured for UDP (`NioDatagramChannel`)
- [ ] Uses `NioEventLoopGroup` with the configured number of worker threads
- [ ] Wires `UdpPacketListener` as the channel handler
- [ ] Server binds to the configured port on application startup
- [ ] Server shuts down cleanly on application stop (event loop groups are closed)
- [ ] Startup log confirms the bound port: `"NetFlow UDP listener started on port {port}"`

**Dependencies:** M1.S3
**Estimated Effort:** M

---

### M1.S5 — Implement UDP Packet Listener

**Description:**
Create `UdpPacketListener.java` as a Netty `SimpleChannelInboundHandler<DatagramPacket>` that receives raw UDP datagrams, extracts the byte payload and sender address, and logs receipt.

**Acceptance Criteria:**
- [ ] `UdpPacketListener.java` exists at `src/main/java/com/netflow/listener/`
- [ ] Extends `SimpleChannelInboundHandler<DatagramPacket>`
- [ ] Extracts `ByteBuf` content from the datagram and converts to `byte[]`
- [ ] Extracts sender `InetAddress` from the `DatagramPacket`
- [ ] Logs packet size and source address at DEBUG level
- [ ] Forwards `byte[]` and sender `InetAddress` to `PacketDispatcher` (stub/no-op at this milestone)
- [ ] Handles `ByteBuf` lifecycle correctly (no leaks)
- [ ] Properly handles exceptions in `exceptionCaught()` with error logging

**Dependencies:** M1.S4
**Estimated Effort:** M

---

### M1.S6 — Create Logging Configuration

**Description:**
Create `logback-spring.xml` with structured logging configuration appropriate for development and production.

**Acceptance Criteria:**
- [ ] `logback-spring.xml` exists at `src/main/resources/`
- [ ] Console appender configured with timestamp, level, logger, and message
- [ ] `com.netflow` logger set to INFO by default
- [ ] `com.netflow.parser` logger set to DEBUG by default
- [ ] Log output is readable and includes thread names

**Dependencies:** M1.S2
**Estimated Effort:** XS

---

### M1.S7 — Verify End-to-End UDP Reception

**Description:**
Manually or via a simple test verify that the application starts, binds the UDP port, and logs incoming packets. This is the milestone's integration validation gate.

**Acceptance Criteria:**
- [ ] Application starts without errors via `mvn spring-boot:run`
- [ ] Sending a UDP packet to port 2055 (e.g., via `netcat`) produces a log line with packet size and sender IP
- [ ] No memory leaks from `ByteBuf` handling (verified by enabling Netty leak detection in test)
- [ ] Application shuts down gracefully on SIGTERM

**Dependencies:** M1.S5
**Estimated Effort:** S

---

### M1.S8 — Spock Compatibility Gate

**Description:**
Confirm that Spock 2.4 + Spring Boot 4 build and test correctly. Write a trivial Spock specification to validate the toolchain. If compatibility is unstable, document the fallback to JUnit 5 for integration tests.

**Acceptance Criteria:**
- [ ] A sample Spock specification exists at `src/test/groovy/com/netflow/`
- [ ] Specification uses `@SpringBootTest` to load the application context
- [ ] `mvn test` compiles Groovy sources and executes the Spock spec successfully
- [ ] If Spock + Spring Boot 4 is incompatible, a `TESTING_FALLBACK.md` documents the JUnit 5 strategy
- [ ] Decision is recorded and communicated before M2 begins

**Dependencies:** M1.S1, M1.S2
**Estimated Effort:** S

---

## Milestone 2: Core Abstractions

**Goal:** Define the interfaces and shared models that all parser versions and handlers will implement.

---

### M2.S1 — Define NetflowVersion Enum

**Description:**
Create the `NetflowVersion` enum that enumerates all supported NetFlow protocol versions. This is referenced by parsers, models, and handlers throughout the codebase.

**Acceptance Criteria:**
- [ ] `NetflowVersion.java` exists at `src/main/java/com/netflow/parser/`
- [ ] Contains values `V5(5)` and `V9(9)`
- [ ] Each value stores its numeric protocol version
- [ ] Provides a `fromVersionNumber(int)` static lookup method
- [ ] `fromVersionNumber` returns `Optional.empty()` for unknown versions
- [ ] Unit test covers known versions and unknown version handling

**Dependencies:** M1.S1
**Estimated Effort:** XS

---

### M2.S2 — Define FieldType Enum and FieldRegistry

**Description:**
Create the `FieldType` enum mapping known NetFlow/IPFIX field type IDs to names and default byte sizes. Create `FieldRegistry` as a lookup utility that resolves `FieldType` by numeric ID.

**Acceptance Criteria:**
- [ ] `FieldType.java` exists at `src/main/java/com/netflow/field/`
- [ ] Contains entries for all common fields: `IN_BYTES(1,4)`, `IN_PKTS(2,4)`, `PROTOCOL(4,1)`, `TOS(5,1)`, `TCP_FLAGS(6,1)`, `L4_SRC_PORT(7,2)`, `IPV4_SRC_ADDR(8,4)`, `IPV4_DST_ADDR(12,4)`, `L4_DST_PORT(11,2)`, `IPV6_SRC_ADDR(27,16)`, `IPV6_DST_ADDR(28,16)`, `INPUT_SNMP(10,2)`, `OUTPUT_SNMP(14,2)`, `SRC_AS(16,2)`, `DST_AS(17,2)`, `SRC_MASK(9,1)`, `DST_MASK(13,1)`, `NEXT_HOP(15,4)`, and additional types from the research doc
- [ ] Each entry stores type ID and default byte length
- [ ] `FieldRegistry.java` exists at `src/main/java/com/netflow/field/`
- [ ] `FieldRegistry.lookup(int typeId)` returns `Optional<FieldType>`
- [ ] Unknown type IDs return `Optional.empty()` (not an exception)
- [ ] Unit test (`FieldRegistrySpec`) verifies known lookups and unknown ID handling

**Dependencies:** M1.S1
**Estimated Effort:** S

---

### M2.S3 — Define FlowHeader Sealed Interface

**Description:**
Create the `FlowHeader` sealed interface that defines the common contract for NetFlow packet headers across all versions.

**Acceptance Criteria:**
- [ ] `FlowHeader.java` exists at `src/main/java/com/netflow/model/`
- [ ] Declared as `sealed interface` permitting `V5Header` and `V9Header`
- [ ] Exposes methods: `version()`, `count()`, `sysUpTime()`, `unixSecs()`, `sequenceNumber()`
- [ ] All return types use appropriate Java types (`NetflowVersion`, `int`, `long`)

**Dependencies:** M2.S1
**Estimated Effort:** XS

---

### M2.S4 — Define FlowRecord Sealed Interface

**Description:**
Create the `FlowRecord` sealed interface with the `getField(FieldType)` method and convenience default accessors for common fields (source/destination addresses, ports, protocol, bytes, packets). Address accessors must fall back to IPv6 field types when IPv4 fields are absent.

**Acceptance Criteria:**
- [ ] `FlowRecord.java` exists at `src/main/java/com/netflow/model/`
- [ ] Declared as `sealed interface` permitting `V5FlowRecord` and `V9FlowRecord`
- [ ] Exposes `version()` returning `NetflowVersion`
- [ ] Exposes `getField(FieldType)` returning `Optional<Object>`
- [ ] Default methods: `srcAddress()`, `dstAddress()`, `srcPort()`, `dstPort()`, `protocol()`, `bytes()`, `packets()`
- [ ] `srcAddress()` and `dstAddress()` fall back from IPv4 to IPv6 field types via `Optional.or()`
- [ ] Numeric accessors use safe widening: `((Number) v).intValue()` / `((Number) v).longValue()`

**Dependencies:** M2.S1, M2.S2
**Estimated Effort:** S

---

### M2.S5 — Define NetflowParser Interface and ParseResult Record

**Description:**
Create the `NetflowParser` strategy interface and the `ParseResult` record that wraps a parsed header and its list of flow records.

**Acceptance Criteria:**
- [ ] `NetflowParser.java` exists at `src/main/java/com/netflow/parser/`
- [ ] Exposes `version()` returning `NetflowVersion`
- [ ] Exposes `parse(byte[] data, InetAddress exporterAddress)` returning `ParseResult`
- [ ] `ParseResult` is a record containing `FlowHeader header` and `List<FlowRecord> records`
- [ ] `ParseResult` exists alongside or within the parser package

**Dependencies:** M2.S3, M2.S4
**Estimated Effort:** XS

---

### M2.S6 — Implement ParserFactory

**Description:**
Create the Spring-managed `ParserFactory` that resolves the correct `NetflowParser` implementation based on the version number extracted from the packet. Uses constructor injection of all `NetflowParser` beans.

**Acceptance Criteria:**
- [ ] `ParserFactory.java` exists at `src/main/java/com/netflow/parser/`
- [ ] Annotated with `@Component`
- [ ] Constructor injects `List<NetflowParser>` and builds an internal `Map<NetflowVersion, NetflowParser>`
- [ ] `getParser(int versionNumber)` returns `Optional<NetflowParser>`
- [ ] Returns `Optional.empty()` for unsupported version numbers
- [ ] Unit test verifies correct parser resolution for v5, v9, and unknown versions

**Dependencies:** M2.S1, M2.S5
**Estimated Effort:** S

---

### M2.S7 — Define FlowRecordHandler Interface

**Description:**
Create the `FlowRecordHandler` observer interface that all downstream handlers (logging, CSV, etc.) will implement.

**Acceptance Criteria:**
- [ ] `FlowRecordHandler.java` exists at `src/main/java/com/netflow/handler/`
- [ ] Exposes `handle(FlowHeader header, List<FlowRecord> records)`
- [ ] Javadoc clarifies the observer pattern: multiple handlers receive the same records

**Dependencies:** M2.S3, M2.S4
**Estimated Effort:** XS

---

### M2.S8 — Implement PacketDispatcher

**Description:**
Create `PacketDispatcher` that receives raw bytes and the exporter `InetAddress`, reads the version field (first 2 bytes), resolves the parser via `ParserFactory`, and dispatches parsed results to all registered `FlowRecordHandler` instances.

**Acceptance Criteria:**
- [ ] `PacketDispatcher.java` exists at `src/main/java/com/netflow/listener/`
- [ ] Annotated as a Spring `@Component`
- [ ] Validates `data.length >= 2` before reading the version field; sub-2-byte packets are silently dropped with a DEBUG log
- [ ] Reads version from first 2 bytes (big-endian unsigned short)
- [ ] Uses `ParserFactory` to resolve the appropriate parser
- [ ] Logs a WARN for unknown/unsupported version numbers
- [ ] Calls `parser.parse(data, exporterAddress)` and forwards the `ParseResult` to all `FlowRecordHandler` beans
- [ ] Unit test (`PacketDispatcherSpec`) verifies: correct parser selection, unknown version handling, sub-2-byte packet handling

**Dependencies:** M2.S6, M2.S7
**Estimated Effort:** M

---

### M2.S9 — Implement IngestionBuffer

**Description:**
Introduce a bounded packet queue between the UDP receive stage and the parse stage to absorb traffic bursts. The buffer must support configurable capacity and overflow behavior (`drop-oldest` or `drop-newest`).

**Acceptance Criteria:**
- [ ] `IngestionBuffer` class exists at `src/main/java/com/netflow/listener/`
- [ ] Backed by a bounded, thread-safe queue (e.g., `ArrayBlockingQueue` or similar)
- [ ] Capacity is configurable via `application.yml`
- [ ] Overflow policy is configurable: `drop-oldest` or `drop-newest`
- [ ] Exposes queue-depth metric (counter/gauge accessible for logging or future Micrometer integration)
- [ ] Exposes drop counter (incremented each time a packet is discarded due to overflow)
- [ ] Unit test validates queue-full behavior for both overflow policies
- [ ] `UdpPacketListener` enqueues into the buffer; a consumer thread dequeues and forwards to `PacketDispatcher`

**Dependencies:** M2.S8
**Estimated Effort:** M

---

### M2.S10 — Wire UDP Listener to Dispatcher Pipeline

**Description:**
Update `UdpPacketListener` to forward received packets through the `IngestionBuffer` to `PacketDispatcher`, completing the receive-to-dispatch pipeline.

**Acceptance Criteria:**
- [ ] `UdpPacketListener` passes `byte[]` and `InetAddress` to `IngestionBuffer`
- [ ] A consumer thread reads from `IngestionBuffer` and calls `PacketDispatcher.dispatch()`
- [ ] Logging confirms the full path: receive → buffer → dispatch
- [ ] Sending a UDP packet to the running app triggers the dispatcher (verified by log or test)

**Dependencies:** M2.S8, M2.S9
**Estimated Effort:** S

---

## Milestone 3: NetFlow v5 Parser

**Goal:** Fully parse NetFlow v5 packets (24-byte header + N x 48-byte records) and log structured flow data.

---

### M3.S1 — Implement V5Header Record

**Description:**
Create the `V5Header` Java record that maps to the 24-byte NetFlow v5 packet header. It must implement the `FlowHeader` sealed interface.

**Acceptance Criteria:**
- [ ] `V5Header.java` exists at `src/main/java/com/netflow/model/v5/`
- [ ] Declared as a `record` implementing `FlowHeader`
- [ ] Fields: `count`, `sysUpTime`, `unixSecs`, `unixNSecs`, `flowSequence`, `engineType`, `engineId`, `samplingInterval`
- [ ] `version()` returns `NetflowVersion.V5`
- [ ] `sequenceNumber()` delegates to `flowSequence`
- [ ] All numeric fields use unsigned-safe types (`int` for 16-bit, `long` for 32-bit)

**Dependencies:** M2.S3
**Estimated Effort:** S

---

### M3.S2 — Implement V5FlowRecord Record

**Description:**
Create the `V5FlowRecord` Java record that maps to the 48-byte NetFlow v5 flow record. It must implement the `FlowRecord` sealed interface, including the `getField(FieldType)` method that maps fixed fields to the corresponding `FieldType`.

**Acceptance Criteria:**
- [ ] `V5FlowRecord.java` exists at `src/main/java/com/netflow/model/v5/`
- [ ] Declared as a `record` implementing `FlowRecord`
- [ ] Fields: `srcAddr`, `dstAddr`, `nextHop`, `inputInterface`, `outputInterface`, `packets`, `bytes`, `firstSwitched`, `lastSwitched`, `srcPort`, `dstPort`, `tcpFlags`, `protocol`, `tos`, `srcAs`, `dstAs`, `srcMask`, `dstMask`
- [ ] `version()` returns `NetflowVersion.V5`
- [ ] `getField(FieldType)` maps fixed fields to corresponding `FieldType` values (e.g., `FieldType.IPV4_SRC_ADDR` → `srcAddr`)
- [ ] Returns `Optional.empty()` for field types not present in v5 (e.g., IPv6 fields)
- [ ] Unit test verifies `getField()` mappings and `Optional` behavior for missing fields

**Dependencies:** M2.S4
**Estimated Effort:** M

---

### M3.S3 — Implement V5Parser

**Description:**
Create the `V5Parser` that wraps raw `byte[]` in a `ByteBuffer` (big-endian), validates the packet, parses the 24-byte header and N x 48-byte flow records, and returns a `ParseResult`.

**Acceptance Criteria:**
- [ ] `V5Parser.java` exists at `src/main/java/com/netflow/parser/v5/`
- [ ] Registered as a Spring `@Component` implementing `NetflowParser`
- [ ] `version()` returns `NetflowVersion.V5`
- [ ] Uses `ByteBuffer` in big-endian mode for all reads
- [ ] Validates first 2 bytes equal `5`; rejects otherwise
- [ ] Validates packet length matches `24 + (count * 48)`; rejects on mismatch with WARN log
- [ ] Parses header using unsigned operations (`& 0xFFFF`, `& 0xFFFFFFFFL`)
- [ ] Parses each 48-byte flow record; converts 4-byte IP fields to dotted-string via `InetAddress`
- [ ] Returns `ParseResult` with the `V5Header` and `List<V5FlowRecord>`
- [ ] Edge cases handled:
  - `count == 0`: accepts packet, returns empty record list, DEBUG log
  - `count > 30`: rejects as malformed, WARN log
  - Actual length != expected: rejects as malformed, WARN log
  - Truncated record mid-iteration: aborts entire packet (no partial emit), WARN log

**Dependencies:** M3.S1, M3.S2, M2.S5
**Estimated Effort:** L

---

### M3.S4 — Create V5 Binary Test Fixtures

**Description:**
Create binary test fixture files and a `TestPacketBuilder` utility for constructing valid and malformed v5 packets programmatically. These are used by all v5 parser tests.

**Acceptance Criteria:**
- [ ] `TestPacketBuilder.java` (or Groovy equivalent) exists in test sources
- [ ] Can construct valid v5 packets with configurable flow count and field values
- [ ] Can construct malformed packets: truncated, wrong version, count > 30, mismatched length
- [ ] Binary fixtures generated at `src/test/resources/packets/`:
  - `v5-single-flow.bin` — 24-byte header + 1 x 48-byte record (72 bytes)
  - `v5-30-flows.bin` — 24-byte header + 30 x 48-byte records (1464 bytes)
- [ ] Fixtures have known, documented field values for assertion in tests

**Dependencies:** M3.S1, M3.S2
**Estimated Effort:** M

---

### M3.S5 — Write V5Parser Unit Tests

**Description:**
Create comprehensive Spock specifications for the `V5Parser` covering valid parsing, edge cases, and malformed input handling.

**Acceptance Criteria:**
- [ ] `V5ParserSpec.groovy` exists at `src/test/groovy/com/netflow/parser/v5/`
- [ ] Tests cover:
  - Parsing a single-flow v5 packet with all field values verified
  - Parsing a max-flow (30 records) v5 packet
  - `count == 0` returns empty list
  - `count > 30` is rejected
  - Packet length mismatch is rejected
  - Truncated packet (partial record) is rejected
  - Wrong version number is rejected
- [ ] Uses `TestPacketBuilder` and/or binary fixtures
- [ ] All tests pass via `mvn test`

**Dependencies:** M3.S3, M3.S4
**Estimated Effort:** M

---

### M3.S6 — Implement LoggingFlowHandler

**Description:**
Create `LoggingFlowHandler` that logs each parsed flow record with structured fields using the `Optional`-aware convenience accessors from `FlowRecord`.

**Acceptance Criteria:**
- [ ] `LoggingFlowHandler.java` exists at `src/main/java/com/netflow/handler/`
- [ ] Implements `FlowRecordHandler`
- [ ] Registered as a Spring `@Component`
- [ ] Logs each record in structured format: `"Received v{version} flow: src={srcAddr}:{srcPort} dst={dstAddr}:{dstPort} proto={protocol} bytes={bytes} packets={packets}"`
- [ ] Uses `Optional`-aware accessors; missing fields render as `N/A`
- [ ] Log level is INFO for flow records, DEBUG for header summary (count, sequence, exporter)

**Dependencies:** M2.S7, M2.S4
**Estimated Effort:** S

---

### M3.S7 — Wire V5 End-to-End Pipeline

**Description:**
Wire the full v5 pipeline: `UdpPacketListener` → `IngestionBuffer` → `PacketDispatcher` → `ParserFactory` → `V5Parser` → `LoggingFlowHandler`. Validate with an integration test.

**Acceptance Criteria:**
- [ ] Sending a valid v5 UDP packet to the running application produces structured log lines for each flow record
- [ ] `ParserFactory` correctly resolves `V5Parser` for version 5
- [ ] Integration test (`UdpListenerIntegrationSpec`) sends a v5 packet via embedded Netty client and asserts log output or handler invocation
- [ ] Malformed packets produce warning logs but do not crash the application

**Dependencies:** M3.S3, M3.S6, M2.S10
**Estimated Effort:** M

---

## Milestone 4: NetFlow v9 Parser

**Goal:** Parse template-based NetFlow v9 packets with template caching, supporting dynamic record structures.

---

### M4.S1 — Define TemplateKind Enum

**Description:**
Create the `TemplateKind` enum that distinguishes regular flow templates from options templates, enabling the parser to route them correctly.

**Acceptance Criteria:**
- [ ] `TemplateKind.java` exists at `src/main/java/com/netflow/model/v9/`
- [ ] Contains values: `FLOW`, `OPTIONS`

**Dependencies:** M1.S1
**Estimated Effort:** XS

---

### M4.S2 — Implement FieldDefinition Record

**Description:**
Create the `FieldDefinition` record that represents a single field definition within a v9 template (type ID + length), with a convenience method to resolve the `FieldType`.

**Acceptance Criteria:**
- [ ] `FieldDefinition.java` exists at `src/main/java/com/netflow/model/v9/`
- [ ] Declared as `record FieldDefinition(int typeId, int length)`
- [ ] `fieldType()` method returns `Optional<FieldType>` via `FieldRegistry.lookup(typeId)`
- [ ] Unknown type IDs return `Optional.empty()` (not an exception)

**Dependencies:** M2.S2
**Estimated Effort:** XS

---

### M4.S3 — Implement Template Record

**Description:**
Create the `Template` record that holds a parsed v9 template definition, including its field list, kind (FLOW/OPTIONS), and metadata.

**Acceptance Criteria:**
- [ ] `Template.java` exists at `src/main/java/com/netflow/model/v9/`
- [ ] Declared as a record with fields: `templateId`, `sourceId`, `kind` (TemplateKind), `fields` (List<FieldDefinition>), `receivedAt` (Instant)
- [ ] `recordLength()` computes the sum of all field lengths
- [ ] `isOptions()` returns `kind == TemplateKind.OPTIONS`
- [ ] Unit test verifies `recordLength()` computation

**Dependencies:** M4.S1, M4.S2
**Estimated Effort:** S

---

### M4.S4 — Implement TemplateCache

**Description:**
Create a thread-safe `TemplateCache` keyed by composite key `(exporterIp, exporterPort, sourceId, templateId)` with configurable TTL and max-size enforcement via LRU eviction.

**Acceptance Criteria:**
- [ ] `TemplateCache.java` exists at `src/main/java/com/netflow/parser/v9/`
- [ ] `ExporterKey` record defined as `(InetAddress ip, int port, long sourceId)`
- [ ] Thread-safe via `ConcurrentHashMap`
- [ ] `put(ExporterKey key, Template template)` stores a template
- [ ] `get(ExporterKey key, int templateId)` returns `Optional<Template>`; returns empty for expired entries
- [ ] `remove(ExporterKey key, int templateId)` returns `boolean` for zero-field template withdrawals
- [ ] TTL is configurable via `netflow.parser.v9.template-cache-ttl` (default: 30 minutes)
- [ ] Max size is configurable via `netflow.parser.v9.template-cache-max-size` (default: 10,000)
- [ ] When max size is reached, LRU entry is evicted before inserting
- [ ] WARN log when a Data FlowSet references an unknown template
- [ ] DEBUG log when a template is re-learned under a new port for the same `(exporterIp, sourceId, templateId)` tuple
- [ ] Unit test (`TemplateCacheSpec`) covers: put/get, TTL expiration, max-size eviction, thread safety, FLOW vs OPTIONS distinction, removal

**Dependencies:** M4.S3
**Estimated Effort:** L

---

### M4.S5 — Implement V9Header Record

**Description:**
Create the `V9Header` Java record that maps to the 20-byte NetFlow v9 packet header.

**Acceptance Criteria:**
- [ ] `V9Header.java` exists at `src/main/java/com/netflow/model/v9/`
- [ ] Declared as a `record` implementing `FlowHeader`
- [ ] Fields: `count`, `sysUpTime`, `unixSecs`, `sequenceNumber`, `sourceId`
- [ ] `version()` returns `NetflowVersion.V9`
- [ ] All numeric fields use unsigned-safe types

**Dependencies:** M2.S3
**Estimated Effort:** S

---

### M4.S6 — Implement V9FlowRecord Record

**Description:**
Create the `V9FlowRecord` record that holds dynamically decoded key-value field data from template-based v9 data records.

**Acceptance Criteria:**
- [ ] `V9FlowRecord.java` exists at `src/main/java/com/netflow/model/v9/`
- [ ] Declared as a `record` implementing `FlowRecord`
- [ ] Fields: `fields` (Map<FieldType, Object>), `unknownFields` (Map<Integer, byte[]>)
- [ ] `version()` returns `NetflowVersion.V9`
- [ ] `getField(FieldType)` returns `Optional.ofNullable(fields.get(fieldType))`
- [ ] Unknown/vendor field type IDs are stored in `unknownFields` by their numeric ID as raw byte arrays

**Dependencies:** M2.S4, M2.S2
**Estimated Effort:** S

---

### M4.S7 — Implement V9Parser: Header and FlowSet Iteration

**Description:**
Create the `V9Parser` core structure: parse the 20-byte header, then iterate through FlowSets by reading FlowSet ID and length. This story covers the outer parsing loop with all defensive guards.

**Acceptance Criteria:**
- [ ] `V9Parser.java` exists at `src/main/java/com/netflow/parser/v9/`
- [ ] Registered as a Spring `@Component` implementing `NetflowParser`
- [ ] `version()` returns `NetflowVersion.V9`
- [ ] Validates `data.length >= 20` at entry; packets of 2–19 bytes dropped with WARN log
- [ ] Parses 20-byte header into `V9Header`
- [ ] FlowSet iteration loop:
  - Validates `remainingBytes >= 4` before reading each FlowSet header
  - Reads FlowSet ID (2 bytes) and length (2 bytes)
  - Validates `length >= 4` and `length <= remainingBytes`; drops rest of packet on failure with WARN log
  - Handles 32-bit boundary padding at end of FlowSets
- [ ] A `length == 0` FlowSet does not cause an infinite loop (explicitly guarded)

**Dependencies:** M4.S5, M4.S4
**Estimated Effort:** L

---

### M4.S8 — Implement V9Parser: Template FlowSet Parsing (ID=0)

**Description:**
Add template FlowSet parsing to `V9Parser`. When FlowSet ID is 0, parse template definitions and store them in `TemplateCache`. Support zero-field template withdrawal.

**Acceptance Criteria:**
- [ ] FlowSet ID 0 is recognized and routed to template parsing logic
- [ ] Each template record is parsed: template ID (2 bytes), field count (2 bytes), then N x (type ID + length) pairs
- [ ] Per-template bounds check: verifies `4 + fieldCount * 4` fits within remaining FlowSet bytes; skips malformed template with WARN
- [ ] Templates with `fieldCount > 0` are stored in `TemplateCache` with `kind = FLOW`
- [ ] Templates with `fieldCount == 0` trigger cache removal (withdrawal) with INFO log
- [ ] Multiple templates in a single FlowSet are parsed sequentially
- [ ] Exporter address and source ID from header are used for cache key

**Dependencies:** M4.S7, M4.S4
**Estimated Effort:** M

---

### M4.S9 — Implement V9Parser: Options Template FlowSet Parsing (ID=1)

**Description:**
Add options template FlowSet parsing to `V9Parser`. When FlowSet ID is 1, parse scope and option field definitions and store in `TemplateCache` with `kind = OPTIONS`.

**Acceptance Criteria:**
- [ ] FlowSet ID 1 is recognized and routed to options template parsing logic
- [ ] Parses: template ID, scope length, option length, then scope fields + option fields
- [ ] Per-template bounds check: verifies `6 + scopeLength + optionLength` fits within remaining FlowSet bytes
- [ ] Optional validation that `scopeLength` and `optionLength` are each 4-byte aligned
- [ ] Templates with `fieldCount == 0` trigger cache removal (withdrawal) with INFO log
- [ ] Non-empty options templates stored in `TemplateCache` with `kind = OPTIONS`

**Dependencies:** M4.S7, M4.S4
**Estimated Effort:** M

---

### M4.S10 — Implement V9Parser: Data FlowSet Parsing (ID>255)

**Description:**
Add data FlowSet parsing to `V9Parser`. When FlowSet ID > 255, look up the template from cache, decode records, and emit to the handler chain.

**Acceptance Criteria:**
- [ ] FlowSet ID > 255 is recognized and routed to data parsing logic
- [ ] Template lookup by FlowSet ID using `TemplateCache.get()`
- [ ] If template not found: skip FlowSet with WARN log (template not yet received)
- [ ] If template found and `kind == FLOW`: decode N records as `V9FlowRecord` instances
  - Record count computed as `(flowSetLength - 4) / template.recordLength()`
  - Each field decoded based on `FieldDefinition` type and length
  - Known `FieldType` values stored in `fields` map; unknown type IDs stored in `unknownFields` as raw bytes
  - Numeric fields decoded to appropriate Java types based on byte width (1→Byte, 2→Short, 4→Integer, 8→Long)
  - IP address fields (4 bytes and 16 bytes) decoded to string representation
- [ ] If template found and `kind == OPTIONS`: decode as exporter metadata, log at DEBUG, do NOT emit to `FlowRecordHandler` chain
- [ ] Defence-in-depth: `template.recordLength() > 0` check before division to prevent `ArithmeticException`
- [ ] Emit decoded flow records to all `FlowRecordHandler` instances

**Dependencies:** M4.S7, M4.S4, M4.S6
**Estimated Effort:** L

---

### M4.S11 — Create V9 Binary Test Fixtures

**Description:**
Create binary test fixture files and extend `TestPacketBuilder` for constructing valid and malformed v9 packets programmatically.

**Acceptance Criteria:**
- [ ] `TestPacketBuilder` extended with v9 packet construction methods
- [ ] Can construct: template FlowSets, options template FlowSets, data FlowSets, and combined packets
- [ ] Can construct malformed v9 packets: truncated, invalid FlowSet lengths, zero-length FlowSets, missing templates, corrupt field data
- [ ] Binary fixtures generated at `src/test/resources/packets/`:
  - `v9-template.bin` — Header + one Template FlowSet defining common fields
  - `v9-data.bin` — Header + one Data FlowSet referencing the above template
  - `v9-template-and-data.bin` — Header + Template FlowSet + Data FlowSet in same packet
- [ ] Fixture field values are documented for test assertions

**Dependencies:** M4.S5, M4.S3
**Estimated Effort:** M

---

### M4.S12 — Write V9Parser Unit Tests

**Description:**
Create comprehensive Spock specifications for the `V9Parser` covering template parsing, data decoding, caching, edge cases, and malformed input.

**Acceptance Criteria:**
- [ ] `V9ParserSpec.groovy` exists at `src/test/groovy/com/netflow/parser/v9/`
- [ ] Tests cover:
  - Parsing a template FlowSet and verifying it is cached
  - Parsing a data FlowSet with a previously cached template
  - Combined template + data in one packet
  - Options template parsing and OPTIONS kind assignment
  - Options data decoded but NOT emitted to handler chain
  - Missing template produces WARN and skips FlowSet
  - Zero-field template triggers cache removal
  - Packet shorter than 20 bytes is rejected
  - FlowSet with `length < 4` drops rest of packet
  - FlowSet with `length > remainingBytes` drops rest of packet
  - Trailing padding bytes are handled
  - `template.recordLength() == 0` defence-in-depth guard
- [ ] Malformed-packet robustness tests (fuzz-style): invalid lengths, trailing bytes, template/data mismatches
- [ ] All tests pass via `mvn test`

**Dependencies:** M4.S7, M4.S8, M4.S9, M4.S10, M4.S11
**Estimated Effort:** L

---

### M4.S13 — Wire V9 End-to-End Pipeline

**Description:**
Register `V9Parser` as a Spring bean and verify the full v9 pipeline end-to-end: UDP → parse → template caching → data decoding → logging.

**Acceptance Criteria:**
- [ ] `ParserFactory` resolves both `V5Parser` and `V9Parser`
- [ ] Sending a v9 template packet followed by a v9 data packet produces structured log lines for decoded flows
- [ ] Integration test sends v9 packets via embedded Netty client and validates handler invocation
- [ ] Template caching works across multiple packets from the same exporter
- [ ] Data packets arriving before templates produce a warning but do not crash

**Dependencies:** M4.S12, M3.S7
**Estimated Effort:** M

---

## Milestone 5: CSV Generation

**Goal:** Write parsed flow records to CSV files with configurable field selection and file rotation.

---

### M5.S1 — Implement CsvConfig

**Description:**
Create `CsvConfig` as a Spring `@ConfigurationProperties` class that binds the CSV-related settings from `application.yml`: enabled flag, output directory, field list, rotation strategy, and file prefix.

**Acceptance Criteria:**
- [ ] `CsvConfig.java` exists at `src/main/java/com/netflow/csv/`
- [ ] Annotated with `@ConfigurationProperties(prefix = "netflow.csv")`
- [ ] Properties: `enabled` (boolean), `outputDir` (String), `fields` (List<String>), `rotation.strategy` (enum: TIME, SIZE, RECORDS), `rotation.interval` (Duration), `rotation.maxSize` (DataSize), `rotation.maxRecords` (int), `filePrefix` (String)
- [ ] Sensible defaults: enabled=true, outputDir=./output, strategy=TIME, interval=5m, prefix=netflow
- [ ] `application.yml` updated with the full CSV configuration block
- [ ] Properties bind correctly on startup (verified by test or log)

**Dependencies:** M1.S3
**Estimated Effort:** S

---

### M5.S2 — Implement CsvWriter

**Description:**
Create `CsvWriter` that writes flow records to CSV files using Apache Commons CSV. Manages file lifecycle including creation, buffered writing, and rotation based on the configured strategy.

**Acceptance Criteria:**
- [ ] `CsvWriter.java` exists at `src/main/java/com/netflow/csv/`
- [ ] Uses Apache Commons CSV `CSVPrinter` for output
- [ ] Writes the configured fields as the CSV header row on file creation
- [ ] File naming follows pattern: `{prefix}_{yyyyMMdd_HHmmss}.csv`
- [ ] Supports three rotation strategies:
  - **Time-based:** Rotates after the configured interval elapses
  - **Size-based:** Rotates when file size exceeds `maxSize`
  - **Record-count:** Rotates when record count exceeds `maxRecords`
- [ ] On rotation: closes current file, returns the completed file `Path` (for storage upload)
- [ ] Uses buffered I/O to minimize disk writes
- [ ] Creates the output directory if it does not exist
- [ ] Thread-safe (synchronized writes or single-writer guarantee)
- [ ] Unit test (`CsvWriterSpec`) verifies: header row, field mapping, all three rotation triggers, file naming

**Dependencies:** M5.S1
**Estimated Effort:** L

---

### M5.S3 — Implement Timestamp Conversion

**Description:**
Implement the RFC-correct timestamp conversion for `firstSwitched` and `lastSwitched` fields. These are exporter-uptime counters, not Unix timestamps, and must be converted using the header's reference time.

**Acceptance Criteria:**
- [ ] Timestamp conversion logic is implemented (in `CsvFlowHandler` or a shared utility)
- [ ] Formula: `absoluteTimeMs = (unixSecs * 1000 + unixNSecs / 1_000_000) - (sysUpTime - switchedTime)`
- [ ] Uses unsigned modular subtraction for the uptime delta: `Integer.toUnsignedLong(sysUpTime - switchedTime)` to handle 32-bit wrap (~49.7 days)
- [ ] Output formatted as ISO-8601 with millisecond precision: `2026-02-19T14:30:00.123Z`
- [ ] Unit test covers: normal conversion, wrap-around scenario, edge values (0, max unsigned 32-bit)

**Dependencies:** M3.S1
**Estimated Effort:** M

---

### M5.S4 — Implement CsvFlowHandler

**Description:**
Create `CsvFlowHandler` that implements `FlowRecordHandler`, maps `FlowRecord` fields to the configured CSV columns, writes to `CsvWriter`, and triggers storage upload on file rotation.

**Acceptance Criteria:**
- [ ] `CsvFlowHandler.java` exists at `src/main/java/com/netflow/handler/`
- [ ] Implements `FlowRecordHandler`
- [ ] Conditionally registered as a Spring bean only when `netflow.csv.enabled=true`
- [ ] Maps `FlowRecord` convenience accessors and `getField()` to the configured CSV field list
- [ ] Handles missing fields (v9 records may lack some fields) by writing empty string
- [ ] Delegates writing to `CsvWriter`
- [ ] On file rotation, triggers `StorageService.upload()` if storage is enabled (via `Optional` injection)
- [ ] Unit test (`CsvFlowHandlerSpec`) verifies: field mapping for v5 and v9 records, missing field handling, rotation trigger

**Dependencies:** M5.S2, M5.S3, M2.S7
**Estimated Effort:** M

---

### M5.S5 — Update Application Configuration for CSV

**Description:**
Update `application.yml` with the full CSV configuration block and verify all properties bind correctly.

**Acceptance Criteria:**
- [ ] `application.yml` contains the full `netflow.csv` configuration block as specified in the plan
- [ ] All 14 default fields are listed
- [ ] Rotation strategy defaults to `time` with 5-minute interval
- [ ] Application starts without binding errors

**Dependencies:** M5.S1
**Estimated Effort:** XS

---

### M5.S6 — CSV Pipeline Integration Test

**Description:**
Create an integration test that verifies the full CSV pipeline: receive a UDP packet → parse → write to CSV file → verify file contents.

**Acceptance Criteria:**
- [ ] Integration test sends v5 and v9 UDP packets to the running application
- [ ] Verifies CSV file is created in the output directory
- [ ] Verifies CSV header matches configured fields
- [ ] Verifies CSV data rows contain the expected values from the test packets
- [ ] Verifies file rotation occurs when the trigger condition is met
- [ ] Test cleans up generated files after execution

**Dependencies:** M5.S4, M3.S7, M4.S13
**Estimated Effort:** M

---

## Milestone 6: Storage Abstraction & Implementations

**Goal:** Upload completed CSV files to configurable storage backends via a pluggable abstraction.

---

### M6.S1 — Define StorageService Interface and StorageType Enum

**Description:**
Create the `StorageService` strategy interface and the `StorageType` enum that enumerates available storage backends.

**Acceptance Criteria:**
- [ ] `StorageService.java` exists at `src/main/java/com/netflow/storage/`
- [ ] Exposes `type()` returning `StorageType`
- [ ] Exposes `upload(Path localFile, String remotePath)` for file uploads
- [ ] Exposes `healthCheck()` returning `boolean` for connectivity validation
- [ ] `StorageType.java` exists with values: `FTP`, `S3`
- [ ] Javadoc explains the extensibility pattern for adding new backends

**Dependencies:** M1.S1
**Estimated Effort:** XS

---

### M6.S2 — Implement StorageConfig with Conditional Bean Registration

**Description:**
Create `StorageConfig` that conditionally registers the appropriate `StorageService` bean based on configuration. No storage bean should be created when storage is disabled.

**Acceptance Criteria:**
- [ ] `StorageConfig.java` exists at `src/main/java/com/netflow/config/`
- [ ] Each backend bean guarded by BOTH conditions: `netflow.storage.enabled=true` AND `netflow.storage.type={type}`
- [ ] When `enabled=false` (default), no `StorageService` bean is registered
- [ ] `CsvFlowHandler` declares `StorageService` as `@Autowired(required = false)` or `Optional<StorageService>`
- [ ] Application starts cleanly with storage disabled (no missing-bean errors)
- [ ] Application starts cleanly with storage enabled and correct type configured

**Dependencies:** M6.S1, M5.S4
**Estimated Effort:** S

---

### M6.S3 — Update Application Configuration for Storage

**Description:**
Add the full storage configuration block to `application.yml` with FTP and S3 settings.

**Acceptance Criteria:**
- [ ] `application.yml` contains the full `netflow.storage` configuration block
- [ ] Storage disabled by default (`enabled: false`)
- [ ] FTP settings: host, port, username (env var), password (env var), passive-mode
- [ ] S3 settings: bucket, region, prefix
- [ ] `remote-path-prefix` and `delete-after-upload` properties present
- [ ] No secrets are hardcoded (use `${ENV_VAR}` placeholders)

**Dependencies:** M1.S3
**Estimated Effort:** XS

---

### M6.S4 — Implement FtpStorageService

**Description:**
Create `FtpStorageService` using Apache Commons Net `FTPClient`/`FTPSClient` that uploads completed CSV files to an FTP server.

**Acceptance Criteria:**
- [ ] `FtpStorageService.java` exists at `src/main/java/com/netflow/storage/ftp/`
- [ ] Implements `StorageService`
- [ ] `type()` returns `StorageType.FTP`
- [ ] Configurable: host, port, username, password, passive mode
- [ ] Supports passive mode (configurable via `passive-mode` property)
- [ ] `upload()`: connects, authenticates, uploads file, verifies completion reply code
- [ ] `healthCheck()`: attempts connection and authentication, returns true/false
- [ ] Handles connection errors gracefully with logging
- [ ] Manages connection lifecycle (connect/disconnect per upload or pooled)
- [ ] Apache Commons Net dependency added to `pom.xml`

**Dependencies:** M6.S1
**Estimated Effort:** M

---

### M6.S5 — Implement S3StorageService

**Description:**
Create `S3StorageService` using AWS SDK v2 `S3Client` that uploads completed CSV files to an S3 bucket.

**Acceptance Criteria:**
- [ ] `S3StorageService.java` exists at `src/main/java/com/netflow/storage/s3/`
- [ ] Implements `StorageService`
- [ ] `type()` returns `StorageType.S3`
- [ ] Configurable: bucket, region, prefix
- [ ] Uses AWS default credential provider chain (env vars, instance profile, etc.)
- [ ] `upload()`: uploads file to `{prefix}/{remotePath}` in the configured bucket
- [ ] Supports multipart upload for large files
- [ ] `healthCheck()`: performs a headBucket or listObjects call, returns true/false
- [ ] Handles AWS SDK errors gracefully with logging
- [ ] AWS SDK v2 dependency added to `pom.xml`

**Dependencies:** M6.S1
**Estimated Effort:** M

---

### M6.S6 — Implement Async Upload Trigger

**Description:**
Wire the upload trigger in `CsvFlowHandler` so that after each file rotation, the completed CSV file is uploaded asynchronously to the configured storage backend without blocking the parsing pipeline.

**Acceptance Criteria:**
- [ ] `CsvFlowHandler` calls `StorageService.upload()` after each file rotation (when storage is enabled)
- [ ] Upload executes asynchronously via `@Async` or a dedicated `ExecutorService`
- [ ] Parsing pipeline is not blocked during upload
- [ ] Upload failures are logged but do not crash the application
- [ ] Successful upload with `delete-after-upload=true` deletes the local file only after confirmed remote success

**Dependencies:** M6.S2, M5.S4
**Estimated Effort:** M

---

### M6.S7 — Implement Upload Reliability (Retry & Dead-Letter)

**Description:**
Implement retry logic with exponential backoff for failed uploads, and a dead-letter directory for files that exhaust all retries.

**Acceptance Criteria:**
- [ ] Upload retries with exponential backoff (configurable max attempts, default: 3)
- [ ] Backoff intervals: 2s, 4s, 8s (doubling)
- [ ] After all retries exhausted, file is moved to a dead-letter directory (e.g., `./output/dead-letter/`)
- [ ] Dead-letter files retain their original name for manual replay
- [ ] Metrics/logging: upload latency, retry count, permanent failure count
- [ ] Unit test verifies: successful upload on first try, successful upload on retry, dead-letter after exhaustion

**Dependencies:** M6.S6
**Estimated Effort:** M

---

### M6.S8 — Write FTP Storage Integration Test

**Description:**
Create a Spock integration specification for `FtpStorageService` using Testcontainers to spin up a real FTP server.

**Acceptance Criteria:**
- [ ] `FtpStorageServiceSpec.groovy` exists at `src/test/groovy/com/netflow/storage/`
- [ ] Uses Testcontainers to start an FTP server container (e.g., vsftpd or similar)
- [ ] Tests: successful upload, upload verification (file exists on server with correct content), health check, connection failure handling
- [ ] Test cleans up after execution
- [ ] All tests pass via `mvn test`

**Dependencies:** M6.S4
**Estimated Effort:** M

---

### M6.S9 — Write S3 Storage Integration Test

**Description:**
Create a Spock integration specification for `S3StorageService` using Testcontainers with LocalStack to emulate S3.

**Acceptance Criteria:**
- [ ] `S3StorageServiceSpec.groovy` exists at `src/test/groovy/com/netflow/storage/`
- [ ] Uses Testcontainers with LocalStack container for S3 emulation
- [ ] Tests: successful upload, upload verification (object exists in bucket with correct content), health check, bucket-not-found handling
- [ ] Test cleans up after execution
- [ ] All tests pass via `mvn test`

**Dependencies:** M6.S5
**Estimated Effort:** M

---

### M6.S10 — End-to-End Pipeline Integration Test

**Description:**
Create the ultimate integration test: full pipeline from UDP reception through parsing, CSV generation, file rotation, and storage upload.

**Acceptance Criteria:**
- [ ] `CsvPipelineIntegrationSpec.groovy` exists in integration test sources
- [ ] Sends multiple UDP packets (v5 and v9) to trigger CSV generation and rotation
- [ ] Verifies CSV files are created with correct content
- [ ] Verifies rotated files are uploaded to storage (via Testcontainers LocalStack or FTP)
- [ ] Verifies local files are cleaned up after successful upload (when `delete-after-upload=true`)
- [ ] Verifies the application handles the full pipeline without errors or resource leaks
- [ ] All tests pass via `mvn test`

**Dependencies:** M6.S6, M5.S6, M4.S13
**Estimated Effort:** L

---

## Summary

| Milestone | Stories | Estimated Total Effort |
|-----------|---------|----------------------|
| **M1: Project Scaffolding** | 8 stories | 2× XS, 3× S, 2× M, 1× XS |
| **M2: Core Abstractions** | 10 stories | 4× XS, 3× S, 3× M |
| **M3: NetFlow v5 Parser** | 7 stories | 2× S, 3× M, 1× L, 1× S |
| **M4: NetFlow v9 Parser** | 13 stories | 2× XS, 3× S, 3× M, 3× L, 2× M |
| **M5: CSV Generation** | 6 stories | 1× XS, 1× S, 3× M, 1× L |
| **M6: Storage Abstraction & Implementations** | 10 stories | 2× XS, 1× S, 6× M, 1× L |
| **Total** | **54 stories** | |

---

## Story Dependency Graph (Simplified)

```
M1.S1 (Maven)
  ├── M1.S2 (App Entry) → M1.S3 (Config) → M1.S4 (Netty) → M1.S5 (Listener) → M1.S7 (Verify)
  ├── M1.S6 (Logging)
  ├── M1.S8 (Spock Gate)
  │
  ├── M2.S1 (Version Enum)
  │     ├── M2.S2 (FieldType) → M2.S4 (FlowRecord)
  │     ├── M2.S3 (FlowHeader)
  │     │     ├── M2.S5 (Parser Interface) → M2.S6 (ParserFactory)
  │     │     └── M2.S7 (Handler Interface)
  │     └── M2.S8 (Dispatcher) → M2.S9 (Buffer) → M2.S10 (Wire Pipeline)
  │
  ├── M3.S1 (V5Header)─┐
  ├── M3.S2 (V5Record)─┼── M3.S3 (V5Parser) → M3.S5 (V5 Tests)
  ├── M3.S4 (V5 Fixtures)┘
  ├── M3.S6 (LoggingHandler) → M3.S7 (V5 E2E)
  │
  ├── M4.S1 (TemplateKind)─┐
  ├── M4.S2 (FieldDef)─────┼── M4.S3 (Template) → M4.S4 (Cache)
  ├── M4.S5 (V9Header)─────┤
  ├── M4.S6 (V9Record)─────┤
  │                         └── M4.S7 (V9 Outer Loop)
  │                               ├── M4.S8 (Template FlowSet)
  │                               ├── M4.S9 (Options FlowSet)
  │                               └── M4.S10 (Data FlowSet)
  │                                     └── M4.S11 (Fixtures) → M4.S12 (V9 Tests) → M4.S13 (V9 E2E)
  │
  ├── M5.S1 (CsvConfig) → M5.S2 (CsvWriter)─┐
  ├── M5.S3 (Timestamps)─────────────────────┼── M5.S4 (CsvHandler) → M5.S6 (CSV E2E)
  ├── M5.S5 (Config Update)                   │
  │                                            │
  ├── M6.S1 (StorageInterface)                 │
  │     ├── M6.S4 (FTP) → M6.S8 (FTP Test)    │
  │     ├── M6.S5 (S3)  → M6.S9 (S3 Test)     │
  │     └── M6.S2 (StorageConfig) → M6.S6 (Async Upload) → M6.S7 (Retry) → M6.S10 (Full E2E)
  └── M6.S3 (Storage Config YAML)
```

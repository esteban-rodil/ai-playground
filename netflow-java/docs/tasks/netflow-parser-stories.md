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

| Field | Description |
|-------|-------------|
| **ID** | Unique identifier `M{milestone}.S{story}` |
| **Title** | Short description |
| **Acceptance Criteria** | Conditions for completion |
| **Dependencies** | Stories that must be completed first |
| **Effort** | T-shirt size (XS / S / M / L / XL) |

---

## Milestone 1: Project Scaffolding

**Goal:** Bootable Spring Boot 4 application with Maven build, Netty UDP listener receiving and logging raw packets.

---

### M1.S1 — Initialize Maven Project

**Description:**
Create the root `pom.xml` with all required dependencies and plugins. This establishes the build foundation for all subsequent milestones.

**Acceptance Criteria:**
- [ ] `pom.xml` exists at `netflow-java/` root with `com.netflow` group ID
- [ ] Java 21 configured as source and target version
- [ ] Spring Boot 4.0.x parent POM or BOM declared
- [ ] Dependencies: `spring-boot-starter`, `netty-transport`, `spock-core`, `spock-spring` (2.4-groovy-5.0), `groovy` (5.0.x), `testcontainers` BOM, `apache-commons-csv`
- [ ] Maven compiler plugin targets Java 21
- [ ] GMavenPlus plugin configured for compiling Groovy test sources
- [ ] `mvn clean compile` succeeds with zero errors

**Dependencies:** None
**Effort:** S

---

### M1.S2 — Create Spring Boot Application Entry Point

**Description:**
Create `NetflowApplication.java` with `@SpringBootApplication` as the bootstrap entry point.

**Acceptance Criteria:**
- [ ] `NetflowApplication.java` exists at `src/main/java/com/netflow/`
- [ ] Annotated with `@SpringBootApplication`
- [ ] Standard `public static void main(String[] args)` method
- [ ] Application starts via `mvn spring-boot:run` without errors

**Dependencies:** M1.S1
**Effort:** XS

---

### M1.S3 — Create Default Application Configuration

**Description:**
Create `application.yml` with baseline configuration for the UDP listener.

**Acceptance Criteria:**
- [ ] `application.yml` exists at `src/main/resources/`
- [ ] Contains `netflow.listener.port` defaulting to `2055`
- [ ] Contains `netflow.listener.buffer-size` defaulting to `65535`
- [ ] Contains `netflow.listener.worker-threads` defaulting to `4`
- [ ] Properties bind correctly on startup

**Dependencies:** M1.S2
**Effort:** XS

---

### M1.S4 — Configure Netty UDP Server

**Description:**
Create `NettyServerConfig.java` that configures a Netty `Bootstrap` for UDP datagram reception bound to the configurable port.

**Acceptance Criteria:**
- [ ] `NettyServerConfig.java` exists at `src/main/java/com/netflow/config/`
- [ ] Reads port and worker-threads from `application.yml`
- [ ] Creates Netty `Bootstrap` configured for UDP (`NioDatagramChannel`)
- [ ] Uses `NioEventLoopGroup` with configured worker threads
- [ ] Wires `UdpPacketListener` as the channel handler
- [ ] Server binds on startup and shuts down cleanly on stop
- [ ] Log confirms: `"NetFlow UDP listener started on port {port}"`

**Dependencies:** M1.S3
**Effort:** M

---

### M1.S5 — Implement UDP Packet Listener

**Description:**
Create `UdpPacketListener.java` as a Netty `SimpleChannelInboundHandler<DatagramPacket>` that receives raw datagrams, extracts payload and sender address.

**Acceptance Criteria:**
- [ ] `UdpPacketListener.java` exists at `src/main/java/com/netflow/listener/`
- [ ] Extends `SimpleChannelInboundHandler<DatagramPacket>`
- [ ] Extracts `ByteBuf` content and converts to `byte[]`
- [ ] Extracts sender `InetAddress` from the datagram
- [ ] Logs packet size and source address at DEBUG level
- [ ] Forwards `byte[]` and `InetAddress` to `PacketDispatcher` (stub at this milestone)
- [ ] No `ByteBuf` leaks; proper `exceptionCaught()` handling

**Dependencies:** M1.S4
**Effort:** M

---

### M1.S6 — Create Logging Configuration

**Description:**
Create `logback-spring.xml` with structured logging for development and production.

**Acceptance Criteria:**
- [ ] `logback-spring.xml` exists at `src/main/resources/`
- [ ] Console appender with timestamp, level, logger, and message
- [ ] `com.netflow` set to INFO; `com.netflow.parser` set to DEBUG
- [ ] Thread names included in log output

**Dependencies:** M1.S2
**Effort:** XS

---

### M1.S7 — Verify End-to-End UDP Reception

**Description:**
Validate that the application starts, binds the UDP port, and logs incoming packets.

**Acceptance Criteria:**
- [ ] Application starts without errors
- [ ] Sending a UDP packet to port 2055 (e.g., via `netcat`) produces a log line
- [ ] No memory leaks from `ByteBuf` handling
- [ ] Graceful shutdown on SIGTERM

**Dependencies:** M1.S5
**Effort:** S

---

### M1.S8 — Spock Compatibility Gate

**Description:**
Confirm Spock 2.4 + Spring Boot 4 build and test correctly. Write a trivial spec to validate the toolchain. Document fallback to JUnit 5 if incompatible.

**Acceptance Criteria:**
- [ ] Sample Spock spec exists at `src/test/groovy/com/netflow/`
- [ ] Spec uses `@SpringBootTest` to load application context
- [ ] `mvn test` compiles Groovy and executes the spec successfully
- [ ] If incompatible, `TESTING_FALLBACK.md` documents the JUnit 5 strategy
- [ ] Decision recorded before M2 begins

**Dependencies:** M1.S1, M1.S2
**Effort:** S

---

## Milestone 2: Core Abstractions

**Goal:** Define the interfaces and shared models that all parser versions and handlers implement.

---

### M2.S1 — Define NetflowVersion Enum

**Description:**
Create the `NetflowVersion` enum enumerating supported protocol versions.

**Acceptance Criteria:**
- [ ] `NetflowVersion.java` exists at `src/main/java/com/netflow/parser/`
- [ ] Values: `V5(5)`, `V9(9)` — each storing its numeric version
- [ ] `fromVersionNumber(int)` static lookup returns `Optional<NetflowVersion>`
- [ ] Returns `Optional.empty()` for unknown versions
- [ ] Unit test covers known and unknown versions

**Dependencies:** M1.S1
**Effort:** XS

---

### M2.S2 — Define FieldType Enum and FieldRegistry

**Description:**
Create `FieldType` enum mapping known field type IDs to names and default byte sizes. Create `FieldRegistry` as a lookup utility.

**Acceptance Criteria:**
- [ ] `FieldType.java` at `src/main/java/com/netflow/field/` with entries: `IN_BYTES(1,4)`, `IN_PKTS(2,4)`, `PROTOCOL(4,1)`, `TOS(5,1)`, `TCP_FLAGS(6,1)`, `L4_SRC_PORT(7,2)`, `IPV4_SRC_ADDR(8,4)`, `SRC_MASK(9,1)`, `INPUT_SNMP(10,2)`, `L4_DST_PORT(11,2)`, `IPV4_DST_ADDR(12,4)`, `DST_MASK(13,1)`, `OUTPUT_SNMP(14,2)`, `NEXT_HOP(15,4)`, `SRC_AS(16,2)`, `DST_AS(17,2)`, `IPV6_SRC_ADDR(27,16)`, `IPV6_DST_ADDR(28,16)`, and additional types from research doc
- [ ] Each entry stores type ID and default byte length
- [ ] `FieldRegistry.java` at `src/main/java/com/netflow/field/`
- [ ] `FieldRegistry.lookup(int typeId)` returns `Optional<FieldType>`
- [ ] Unknown IDs return `Optional.empty()`
- [ ] Unit test (`FieldRegistrySpec`) verifies lookups

**Dependencies:** M1.S1
**Effort:** S

---

### M2.S3 — Define FlowHeader Sealed Interface

**Description:**
Create the `FlowHeader` sealed interface as the common contract for packet headers.

**Acceptance Criteria:**
- [ ] `FlowHeader.java` at `src/main/java/com/netflow/model/`
- [ ] `sealed interface` permitting `V5Header` and `V9Header`
- [ ] Methods: `version()`, `count()`, `sysUpTime()`, `unixSecs()`, `sequenceNumber()`

**Dependencies:** M2.S1
**Effort:** XS

---

### M2.S4 — Define FlowRecord Sealed Interface

**Description:**
Create the `FlowRecord` sealed interface with `getField(FieldType)` and convenience default accessors. Address accessors must fall back to IPv6 when IPv4 is absent.

**Acceptance Criteria:**
- [ ] `FlowRecord.java` at `src/main/java/com/netflow/model/`
- [ ] `sealed interface` permitting `V5FlowRecord` and `V9FlowRecord`
- [ ] `version()` returns `NetflowVersion`; `getField(FieldType)` returns `Optional<Object>`
- [ ] Default methods: `srcAddress()`, `dstAddress()` (with IPv6 fallback via `Optional.or()`), `srcPort()`, `dstPort()`, `protocol()`, `bytes()`, `packets()`
- [ ] Numeric accessors use safe widening: `((Number) v).intValue()` / `longValue()`

**Dependencies:** M2.S1, M2.S2
**Effort:** S

---

### M2.S5 — Define NetflowParser Interface and ParseResult

**Description:**
Create the `NetflowParser` strategy interface and `ParseResult` record.

**Acceptance Criteria:**
- [ ] `NetflowParser.java` at `src/main/java/com/netflow/parser/`
- [ ] Methods: `version()`, `parse(byte[] data, InetAddress exporterAddress)` returning `ParseResult`
- [ ] `ParseResult` record: `FlowHeader header`, `List<FlowRecord> records`

**Dependencies:** M2.S3, M2.S4
**Effort:** XS

---

### M2.S6 — Implement ParserFactory

**Description:**
Create Spring-managed `ParserFactory` resolving the correct `NetflowParser` by version number.

**Acceptance Criteria:**
- [ ] `ParserFactory.java` at `src/main/java/com/netflow/parser/` annotated `@Component`
- [ ] Constructor injects `List<NetflowParser>`, builds `Map<NetflowVersion, NetflowParser>`
- [ ] `getParser(int versionNumber)` returns `Optional<NetflowParser>`
- [ ] `Optional.empty()` for unsupported versions
- [ ] Unit test verifies v5, v9, and unknown resolution

**Dependencies:** M2.S1, M2.S5
**Effort:** S

---

### M2.S7 — Define FlowRecordHandler Interface

**Description:**
Create the `FlowRecordHandler` observer interface for downstream handlers.

**Acceptance Criteria:**
- [ ] `FlowRecordHandler.java` at `src/main/java/com/netflow/handler/`
- [ ] Method: `handle(FlowHeader header, List<FlowRecord> records)`

**Dependencies:** M2.S3, M2.S4
**Effort:** XS

---

### M2.S8 — Implement PacketDispatcher

**Description:**
Create `PacketDispatcher` that reads the version field, resolves the parser, and dispatches results to all handlers.

**Acceptance Criteria:**
- [ ] `PacketDispatcher.java` at `src/main/java/com/netflow/listener/` as `@Component`
- [ ] Validates `data.length >= 2`; sub-2-byte packets dropped with DEBUG log
- [ ] Reads version from first 2 bytes (big-endian unsigned short)
- [ ] Uses `ParserFactory` to resolve parser; WARN for unknown versions
- [ ] Forwards `ParseResult` to all `FlowRecordHandler` beans
- [ ] Unit test (`PacketDispatcherSpec`): correct selection, unknown version, sub-2-byte packets

**Dependencies:** M2.S6, M2.S7
**Effort:** M

---

### M2.S9 — Implement IngestionBuffer

**Description:**
Bounded packet queue between UDP receive and parse stages with configurable capacity and overflow policy.

**Acceptance Criteria:**
- [ ] `IngestionBuffer` at `src/main/java/com/netflow/listener/`
- [ ] Backed by bounded, thread-safe queue
- [ ] Configurable capacity via `application.yml`
- [ ] Configurable overflow policy: `drop-oldest` or `drop-newest`
- [ ] Exposes queue-depth gauge and drop counter
- [ ] Unit test validates both overflow policies

**Dependencies:** M2.S8
**Effort:** M

---

### M2.S10 — Wire UDP Listener to Dispatcher Pipeline

**Description:**
Connect `UdpPacketListener` → `IngestionBuffer` → `PacketDispatcher` completing the receive-to-dispatch pipeline.

**Acceptance Criteria:**
- [ ] `UdpPacketListener` enqueues into `IngestionBuffer`
- [ ] Consumer thread dequeues and calls `PacketDispatcher.dispatch()`
- [ ] Sending a UDP packet triggers the full path (verified by log or test)

**Dependencies:** M2.S8, M2.S9
**Effort:** S

---

## Milestone 3: NetFlow v5 Parser

**Goal:** Fully parse NetFlow v5 packets (24-byte header + N x 48-byte records) and log structured flow data.

---

### M3.S1 — Implement V5Header Record

**Description:**
Create `V5Header` Java record mapping the 24-byte v5 packet header, implementing `FlowHeader`.

**Acceptance Criteria:**
- [ ] `V5Header.java` at `src/main/java/com/netflow/model/v5/`
- [ ] Record fields: `count`, `sysUpTime`, `unixSecs`, `unixNSecs`, `flowSequence`, `engineType`, `engineId`, `samplingInterval`
- [ ] `version()` returns `NetflowVersion.V5`
- [ ] `sequenceNumber()` delegates to `flowSequence`
- [ ] Unsigned-safe types (`int` for 16-bit, `long` for 32-bit)

**Dependencies:** M2.S3
**Effort:** S

---

### M3.S2 — Implement V5FlowRecord Record

**Description:**
Create `V5FlowRecord` Java record mapping the 48-byte v5 flow record, implementing `FlowRecord` with `getField(FieldType)`.

**Acceptance Criteria:**
- [ ] `V5FlowRecord.java` at `src/main/java/com/netflow/model/v5/`
- [ ] Record fields: `srcAddr`, `dstAddr`, `nextHop`, `inputInterface`, `outputInterface`, `packets`, `bytes`, `firstSwitched`, `lastSwitched`, `srcPort`, `dstPort`, `tcpFlags`, `protocol`, `tos`, `srcAs`, `dstAs`, `srcMask`, `dstMask`
- [ ] `version()` returns `NetflowVersion.V5`
- [ ] `getField(FieldType)` maps fixed fields to `FieldType` (e.g., `IPV4_SRC_ADDR` -> `srcAddr`)
- [ ] `Optional.empty()` for absent field types (e.g., IPv6)
- [ ] Unit test verifies mappings

**Dependencies:** M2.S4
**Effort:** M

---

### M3.S3 — Implement V5Parser

**Description:**
Create `V5Parser` that wraps `byte[]` in a big-endian `ByteBuffer`, validates the packet, and parses header + flow records.

**Acceptance Criteria:**
- [ ] `V5Parser.java` at `src/main/java/com/netflow/parser/v5/` as `@Component`
- [ ] `version()` returns `NetflowVersion.V5`
- [ ] Validates first 2 bytes == `5`
- [ ] Validates packet length == `24 + (count * 48)`; WARN on mismatch
- [ ] Parses header with unsigned operations (`& 0xFFFF`, `& 0xFFFFFFFFL`)
- [ ] Parses each 48-byte record; converts 4-byte IPs via `InetAddress`
- [ ] Returns `ParseResult` with `V5Header` + `List<V5FlowRecord>`
- [ ] Edge cases: `count == 0` -> empty list + DEBUG; `count > 30` -> reject + WARN; length mismatch -> reject + WARN; truncated mid-record -> abort + WARN

**Dependencies:** M3.S1, M3.S2, M2.S5
**Effort:** L

---

### M3.S4 — Create V5 Binary Test Fixtures and TestPacketBuilder

**Description:**
Create binary fixtures and a `TestPacketBuilder` utility for constructing valid and malformed v5 packets.

**Acceptance Criteria:**
- [ ] `TestPacketBuilder` exists in test sources; constructs v5 packets with configurable fields
- [ ] Can construct malformed packets: truncated, wrong version, count > 30, length mismatch
- [ ] Fixtures at `src/test/resources/packets/`: `v5-single-flow.bin` (72 bytes), `v5-30-flows.bin` (1464 bytes)
- [ ] Field values documented for assertion

**Dependencies:** M3.S1, M3.S2
**Effort:** M

---

### M3.S5 — Write V5Parser Unit Tests

**Description:**
Comprehensive Spock specs for `V5Parser` covering valid parsing, edge cases, and malformed input.

**Acceptance Criteria:**
- [ ] `V5ParserSpec.groovy` at `src/test/groovy/com/netflow/parser/v5/`
- [ ] Tests: single-flow parse with field verification, max-flow (30) parse, `count == 0`, `count > 30`, length mismatch, truncated packet, wrong version
- [ ] Uses `TestPacketBuilder` and/or binary fixtures
- [ ] All tests pass via `mvn test`

**Dependencies:** M3.S3, M3.S4
**Effort:** M

---

### M3.S6 — Implement LoggingFlowHandler

**Description:**
Create `LoggingFlowHandler` that logs each flow record with structured fields using `Optional`-aware accessors.

**Acceptance Criteria:**
- [ ] `LoggingFlowHandler.java` at `src/main/java/com/netflow/handler/` as `@Component`
- [ ] Implements `FlowRecordHandler`
- [ ] Logs: `"Received v{version} flow: src={srcAddr}:{srcPort} dst={dstAddr}:{dstPort} proto={protocol} bytes={bytes} packets={packets}"`
- [ ] Missing fields render as `N/A`
- [ ] INFO for records, DEBUG for header summary

**Dependencies:** M2.S7, M2.S4
**Effort:** S

---

### M3.S7 — Wire V5 End-to-End Pipeline

**Description:**
Wire the full v5 pipeline and validate with an integration test.

**Acceptance Criteria:**
- [ ] Valid v5 UDP packet produces structured log lines per flow record
- [ ] `ParserFactory` resolves `V5Parser` for version 5
- [ ] Integration test (`UdpListenerIntegrationSpec`) sends v5 packet via embedded Netty client, asserts handler invocation
- [ ] Malformed packets produce warnings without crashing

**Dependencies:** M3.S3, M3.S6, M2.S10
**Effort:** M

---

## Milestone 4: NetFlow v9 Parser

**Goal:** Parse template-based NetFlow v9 packets with template caching, supporting dynamic record structures.

---

### M4.S1 — Define TemplateKind Enum

**Description:**
Create `TemplateKind` enum distinguishing regular flow templates from options templates.

**Acceptance Criteria:**
- [ ] `TemplateKind.java` at `src/main/java/com/netflow/model/v9/`
- [ ] Values: `FLOW`, `OPTIONS`

**Dependencies:** M1.S1
**Effort:** XS

---

### M4.S2 — Implement FieldDefinition Record

**Description:**
Create `FieldDefinition` record representing a single field in a v9 template (type ID + length).

**Acceptance Criteria:**
- [ ] `FieldDefinition.java` at `src/main/java/com/netflow/model/v9/`
- [ ] `record FieldDefinition(int typeId, int length)`
- [ ] `fieldType()` returns `Optional<FieldType>` via `FieldRegistry.lookup(typeId)`

**Dependencies:** M2.S2
**Effort:** XS

---

### M4.S3 — Implement Template Record

**Description:**
Create `Template` record holding a parsed v9 template definition.

**Acceptance Criteria:**
- [ ] `Template.java` at `src/main/java/com/netflow/model/v9/`
- [ ] Fields: `templateId`, `sourceId`, `kind` (TemplateKind), `fields` (List<FieldDefinition>), `receivedAt` (Instant)
- [ ] `recordLength()` returns sum of field lengths
- [ ] `isOptions()` returns `kind == TemplateKind.OPTIONS`
- [ ] Unit test verifies `recordLength()`

**Dependencies:** M4.S1, M4.S2
**Effort:** S

---

### M4.S4 — Implement TemplateCache

**Description:**
Thread-safe template cache keyed by `(exporterIp, exporterPort, sourceId, templateId)` with TTL and LRU eviction.

**Acceptance Criteria:**
- [ ] `TemplateCache.java` at `src/main/java/com/netflow/parser/v9/`
- [ ] `ExporterKey` record: `(InetAddress ip, int port, long sourceId)`
- [ ] Thread-safe via `ConcurrentHashMap`
- [ ] `put()`, `get()` (returns `Optional<Template>`), `remove()` (returns `boolean`)
- [ ] TTL configurable via `netflow.parser.v9.template-cache-ttl` (default: 30m)
- [ ] Max size via `netflow.parser.v9.template-cache-max-size` (default: 10,000); LRU eviction
- [ ] WARN when Data FlowSet references unknown template
- [ ] DEBUG when template re-learned under new port
- [ ] Unit test (`TemplateCacheSpec`): put/get, TTL expiry, max-size eviction, thread safety, removal

**Dependencies:** M4.S3
**Effort:** L

---

### M4.S5 — Implement V9Header Record

**Description:**
Create `V9Header` Java record mapping the 20-byte v9 packet header.

**Acceptance Criteria:**
- [ ] `V9Header.java` at `src/main/java/com/netflow/model/v9/`
- [ ] Record implementing `FlowHeader`
- [ ] Fields: `count`, `sysUpTime`, `unixSecs`, `sequenceNumber`, `sourceId`
- [ ] `version()` returns `NetflowVersion.V9`

**Dependencies:** M2.S3
**Effort:** S

---

### M4.S6 — Implement V9FlowRecord Record

**Description:**
Create `V9FlowRecord` holding dynamically decoded key-value field data.

**Acceptance Criteria:**
- [ ] `V9FlowRecord.java` at `src/main/java/com/netflow/model/v9/`
- [ ] Record implementing `FlowRecord`
- [ ] Fields: `fields` (Map<FieldType, Object>), `unknownFields` (Map<Integer, byte[]>)
- [ ] `version()` returns `NetflowVersion.V9`
- [ ] `getField(FieldType)` returns `Optional.ofNullable(fields.get(fieldType))`

**Dependencies:** M2.S4, M2.S2
**Effort:** S

---

### M4.S7 — Implement V9Parser: Header and FlowSet Loop

**Description:**
Create `V9Parser` core: parse 20-byte header, iterate FlowSets with all defensive guards.

**Acceptance Criteria:**
- [ ] `V9Parser.java` at `src/main/java/com/netflow/parser/v9/` as `@Component`
- [ ] `version()` returns `NetflowVersion.V9`
- [ ] Validates `data.length >= 20`; 2-19 byte packets dropped with WARN
- [ ] Parses 20-byte header into `V9Header`
- [ ] FlowSet loop validates `remainingBytes >= 4` before each header read
- [ ] Validates `length >= 4` and `length <= remainingBytes`; drops rest of packet on failure
- [ ] `length == 0` cannot cause infinite loop
- [ ] Handles 32-bit boundary padding

**Dependencies:** M4.S5, M4.S4
**Effort:** L

---

### M4.S8 — Implement V9Parser: Template FlowSet Parsing (ID=0)

**Description:**
Parse template definitions from FlowSet ID 0 and store in `TemplateCache`. Support zero-field withdrawal.

**Acceptance Criteria:**
- [ ] FlowSet ID 0 routed to template parsing
- [ ] Parses: template ID, field count, then N x (type ID, length) pairs
- [ ] Bounds check: `4 + fieldCount * 4` fits within remaining FlowSet bytes; WARN on failure
- [ ] `fieldCount > 0`: stored with `kind = FLOW`
- [ ] `fieldCount == 0`: triggers cache removal (withdrawal) with INFO log
- [ ] Multiple templates per FlowSet parsed sequentially

**Dependencies:** M4.S7, M4.S4
**Effort:** M

---

### M4.S9 — Implement V9Parser: Options Template FlowSet Parsing (ID=1)

**Description:**
Parse options template definitions from FlowSet ID 1 and store with `kind = OPTIONS`.

**Acceptance Criteria:**
- [ ] FlowSet ID 1 routed to options template parsing
- [ ] Parses: template ID, scope length, option length, then scope + option fields
- [ ] Bounds check: `6 + scopeLength + optionLength` fits within remaining FlowSet bytes
- [ ] Optional: validates `scopeLength` and `optionLength` are 4-byte aligned
- [ ] Zero-field withdrawal supported (same as regular templates)
- [ ] Stored with `kind = OPTIONS`

**Dependencies:** M4.S7, M4.S4
**Effort:** M

---

### M4.S10 — Implement V9Parser: Data FlowSet Parsing (ID>255)

**Description:**
Decode data FlowSets using cached templates and emit flow records to the handler chain.

**Acceptance Criteria:**
- [ ] FlowSet ID > 255 routed to data parsing
- [ ] Template lookup via `TemplateCache.get()`
- [ ] Template not found: skip with WARN
- [ ] Template `kind == FLOW`: decode N `V9FlowRecord` instances
  - Record count: `(flowSetLength - 4) / template.recordLength()`
  - Fields decoded by type/length (1->Byte, 2->Short, 4->Integer, 8->Long)
  - IP fields (4 and 16 bytes) decoded to strings
  - Known types in `fields` map; unknown in `unknownFields` as raw bytes
- [ ] Template `kind == OPTIONS`: decode as metadata, log DEBUG, do NOT emit to handlers
- [ ] Defence-in-depth: `template.recordLength() > 0` before division
- [ ] Decoded flow records emitted to all `FlowRecordHandler` instances

**Dependencies:** M4.S7, M4.S4, M4.S6
**Effort:** L

---

### M4.S11 — Create V9 Binary Test Fixtures

**Description:**
Create binary fixtures and extend `TestPacketBuilder` for v9 packets.

**Acceptance Criteria:**
- [ ] `TestPacketBuilder` extended with v9 construction methods
- [ ] Supports: template FlowSets, options templates, data FlowSets, combined packets
- [ ] Supports malformed variants: truncated, invalid lengths, zero-length, missing templates
- [ ] Fixtures at `src/test/resources/packets/`: `v9-template.bin`, `v9-data.bin`, `v9-template-and-data.bin`

**Dependencies:** M4.S5, M4.S3
**Effort:** M

---

### M4.S12 — Write V9Parser Unit Tests

**Description:**
Comprehensive Spock specs for `V9Parser` including template caching, data decoding, and malformed input.

**Acceptance Criteria:**
- [ ] `V9ParserSpec.groovy` at `src/test/groovy/com/netflow/parser/v9/`
- [ ] Tests cover: template parse + cache, data decode with cached template, combined template+data packet, options template with OPTIONS kind, options data NOT emitted to handlers, missing template WARN, zero-field withdrawal, packet < 20 bytes rejected, FlowSet `length < 4` drops packet, FlowSet `length > remaining` drops packet, padding bytes, `recordLength() == 0` guard
- [ ] Malformed-packet robustness tests (fuzz-style inputs)
- [ ] All tests pass via `mvn test`

**Dependencies:** M4.S7, M4.S8, M4.S9, M4.S10, M4.S11
**Effort:** L

---

### M4.S13 — Wire V9 End-to-End Pipeline

**Description:**
Register `V9Parser` and verify the full v9 pipeline end-to-end.

**Acceptance Criteria:**
- [ ] `ParserFactory` resolves both v5 and v9
- [ ] Template packet followed by data packet produces structured log lines
- [ ] Integration test sends v9 packets via embedded Netty client
- [ ] Template caching works across multiple packets
- [ ] Data before template produces warning without crash

**Dependencies:** M4.S12, M3.S7
**Effort:** M

---

## Milestone 5: CSV Generation

**Goal:** Write parsed flow records to CSV files with configurable field selection and file rotation.

---

### M5.S1 — Implement CsvConfig

**Description:**
Create `CsvConfig` as `@ConfigurationProperties` binding CSV settings from `application.yml`.

**Acceptance Criteria:**
- [ ] `CsvConfig.java` at `src/main/java/com/netflow/csv/`
- [ ] Properties: `enabled`, `outputDir`, `fields` (List<String>), `rotation.strategy` (TIME/SIZE/RECORDS), `rotation.interval`, `rotation.maxSize`, `rotation.maxRecords`, `filePrefix`
- [ ] Defaults: enabled=true, outputDir=./output, strategy=TIME, interval=5m, prefix=netflow
- [ ] `application.yml` updated with full CSV config block
- [ ] Properties bind correctly on startup

**Dependencies:** M1.S3
**Effort:** S

---

### M5.S2 — Implement CsvWriter

**Description:**
Create `CsvWriter` using Apache Commons CSV for buffered file writing with rotation support.

**Acceptance Criteria:**
- [ ] `CsvWriter.java` at `src/main/java/com/netflow/csv/`
- [ ] Uses `CSVPrinter` with configured fields as header row
- [ ] File naming: `{prefix}_{yyyyMMdd_HHmmss}.csv`
- [ ] Three rotation strategies: time-based, size-based, record-count
- [ ] On rotation: closes file, returns completed file `Path`
- [ ] Buffered I/O; creates output directory if missing
- [ ] Thread-safe writes
- [ ] Unit test (`CsvWriterSpec`): header row, field mapping, all three rotation triggers, file naming

**Dependencies:** M5.S1
**Effort:** L

---

### M5.S3 — Implement Timestamp Conversion

**Description:**
RFC-correct conversion of `firstSwitched`/`lastSwitched` uptime counters to absolute timestamps with 32-bit wrap handling.

**Acceptance Criteria:**
- [ ] Conversion formula: `absoluteTimeMs = (unixSecs * 1000 + unixNSecs / 1_000_000) - unsignedDelta(sysUpTime, switchedTime)`
- [ ] Unsigned modular subtraction via `Integer.toUnsignedLong(sysUpTime - switchedTime)`
- [ ] Output as ISO-8601 with millisecond precision: `2026-02-19T14:30:00.123Z`
- [ ] Unit tests: normal conversion, 32-bit wrap-around, edge values (0, max unsigned 32-bit)

**Dependencies:** M3.S1
**Effort:** M

---

### M5.S4 — Implement CsvFlowHandler

**Description:**
Create `CsvFlowHandler` implementing `FlowRecordHandler` that maps records to CSV columns and triggers storage on rotation.

**Acceptance Criteria:**
- [ ] `CsvFlowHandler.java` at `src/main/java/com/netflow/handler/`
- [ ] Implements `FlowRecordHandler`; conditional bean when `netflow.csv.enabled=true`
- [ ] Maps `FlowRecord` accessors to configured CSV field list
- [ ] Missing fields (common in v9) written as empty string
- [ ] Delegates to `CsvWriter`
- [ ] On rotation, triggers `StorageService.upload()` if available (`Optional` injection)
- [ ] Unit test (`CsvFlowHandlerSpec`): field mapping for v5 and v9, missing fields, rotation trigger

**Dependencies:** M5.S2, M5.S3, M2.S7
**Effort:** M

---

### M5.S5 — Update Application Configuration for CSV

**Description:**
Add the full CSV configuration block to `application.yml`.

**Acceptance Criteria:**
- [ ] `application.yml` contains `netflow.csv` block with all 14 default fields
- [ ] Rotation defaults to `time` with 5-minute interval
- [ ] Application starts without binding errors

**Dependencies:** M5.S1
**Effort:** XS

---

### M5.S6 — CSV Pipeline Integration Test

**Description:**
Integration test verifying: UDP packet -> parse -> CSV file with correct contents.

**Acceptance Criteria:**
- [ ] Sends v5 and v9 packets to running application
- [ ] Verifies CSV file created with correct headers and data
- [ ] Verifies rotation triggers correctly
- [ ] Cleans up generated files after test

**Dependencies:** M5.S4, M3.S7, M4.S13
**Effort:** M

---

## Milestone 6: Storage Abstraction & Implementations

**Goal:** Upload completed CSV files to configurable storage backends via a pluggable abstraction.

---

### M6.S1 — Define StorageService Interface and StorageType Enum

**Description:**
Create the `StorageService` strategy interface and `StorageType` enum.

**Acceptance Criteria:**
- [ ] `StorageService.java` at `src/main/java/com/netflow/storage/`
- [ ] Methods: `type()`, `upload(Path localFile, String remotePath)`, `healthCheck()`
- [ ] `StorageType.java` with values: `FTP`, `S3`

**Dependencies:** M1.S1
**Effort:** XS

---

### M6.S2 — Implement StorageConfig with Conditional Beans

**Description:**
Conditional bean registration: each backend guarded by `enabled=true` AND `type={type}`.

**Acceptance Criteria:**
- [ ] `StorageConfig.java` at `src/main/java/com/netflow/config/`
- [ ] Each bean requires BOTH `storage.enabled=true` and `storage.type={type}`
- [ ] `enabled=false` (default) -> no `StorageService` bean registered
- [ ] `CsvFlowHandler` uses `@Autowired(required = false)` for `StorageService`
- [ ] App starts cleanly with storage disabled and with storage enabled

**Dependencies:** M6.S1, M5.S4
**Effort:** S

---

### M6.S3 — Update Application Configuration for Storage

**Description:**
Add full storage configuration block to `application.yml`.

**Acceptance Criteria:**
- [ ] `netflow.storage` block with: `enabled` (false), `type`, `remote-path-prefix`, `delete-after-upload`
- [ ] FTP sub-block: host, port, username (`${FTP_USER}`), password (`${FTP_PASS}`), passive-mode
- [ ] S3 sub-block: bucket, region, prefix
- [ ] No hardcoded secrets

**Dependencies:** M1.S3
**Effort:** XS

---

### M6.S4 — Implement FtpStorageService

**Description:**
FTP upload implementation using Apache Commons Net.

**Acceptance Criteria:**
- [ ] `FtpStorageService.java` at `src/main/java/com/netflow/storage/ftp/`
- [ ] Implements `StorageService`; `type()` returns `FTP`
- [ ] Configurable: host, port, username, password, passive mode
- [ ] `upload()`: connects, authenticates, uploads, verifies reply code
- [ ] `healthCheck()`: connection + auth test
- [ ] Handles connection errors gracefully
- [ ] Commons Net dependency in `pom.xml`

**Dependencies:** M6.S1
**Effort:** M

---

### M6.S5 — Implement S3StorageService

**Description:**
S3 upload implementation using AWS SDK v2.

**Acceptance Criteria:**
- [ ] `S3StorageService.java` at `src/main/java/com/netflow/storage/s3/`
- [ ] Implements `StorageService`; `type()` returns `S3`
- [ ] Configurable: bucket, region, prefix
- [ ] Uses AWS default credential provider chain
- [ ] `upload()`: puts object at `{prefix}/{remotePath}`; multipart for large files
- [ ] `healthCheck()`: headBucket or listObjects
- [ ] AWS SDK v2 dependency in `pom.xml`

**Dependencies:** M6.S1
**Effort:** M

---

### M6.S6 — Implement Async Upload Trigger

**Description:**
Wire `CsvFlowHandler` to upload rotated files asynchronously without blocking the parsing pipeline.

**Acceptance Criteria:**
- [ ] `CsvFlowHandler` calls `StorageService.upload()` after each rotation (when enabled)
- [ ] Upload runs via `@Async` or dedicated `ExecutorService`
- [ ] Parsing pipeline not blocked
- [ ] Failures logged but don't crash
- [ ] `delete-after-upload=true` deletes local file only after confirmed success

**Dependencies:** M6.S2, M5.S4
**Effort:** M

---

### M6.S7 — Implement Upload Reliability (Retry & Dead-Letter)

**Description:**
Exponential backoff retry and dead-letter directory for exhausted uploads.

**Acceptance Criteria:**
- [ ] Retries with exponential backoff: 2s, 4s, 8s (configurable max attempts, default: 3)
- [ ] Exhausted files moved to `./output/dead-letter/` for manual replay
- [ ] Dead-letter files retain original name
- [ ] Metrics/logging: upload latency, retry count, permanent failures
- [ ] Unit test: success on first try, success on retry, dead-letter after exhaustion

**Dependencies:** M6.S6
**Effort:** M

---

### M6.S8 — Write FTP Storage Integration Test

**Description:**
Spock integration spec for `FtpStorageService` using Testcontainers FTP server.

**Acceptance Criteria:**
- [ ] `FtpStorageServiceSpec.groovy` at `src/test/groovy/com/netflow/storage/`
- [ ] Testcontainers FTP server (vsftpd or similar)
- [ ] Tests: upload, file verification, health check, connection failure
- [ ] Cleanup after test; all pass via `mvn test`

**Dependencies:** M6.S4
**Effort:** M

---

### M6.S9 — Write S3 Storage Integration Test

**Description:**
Spock integration spec for `S3StorageService` using Testcontainers LocalStack.

**Acceptance Criteria:**
- [ ] `S3StorageServiceSpec.groovy` at `src/test/groovy/com/netflow/storage/`
- [ ] Testcontainers with LocalStack for S3 emulation
- [ ] Tests: upload, object verification, health check, bucket-not-found handling
- [ ] Cleanup after test; all pass via `mvn test`

**Dependencies:** M6.S5
**Effort:** M

---

### M6.S10 — End-to-End Pipeline Integration Test

**Description:**
Full pipeline test: UDP -> parse -> CSV -> rotation -> storage upload.

**Acceptance Criteria:**
- [ ] `CsvPipelineIntegrationSpec.groovy` in integration test sources
- [ ] Sends v5 and v9 packets triggering CSV generation and rotation
- [ ] Verifies CSV content correctness
- [ ] Verifies rotated files uploaded to storage (LocalStack or FTP via Testcontainers)
- [ ] Verifies local cleanup after upload when `delete-after-upload=true`
- [ ] No resource leaks; all tests pass via `mvn test`

**Dependencies:** M6.S6, M5.S6, M4.S13
**Effort:** L

---

## Summary

| Milestone | Stories | Effort Breakdown |
|-----------|---------|-----------------|
| **M1: Project Scaffolding** | 8 | 3 XS, 3 S, 2 M |
| **M2: Core Abstractions** | 10 | 4 XS, 3 S, 3 M |
| **M3: NetFlow v5 Parser** | 7 | 2 S, 3 M, 1 L |
| **M4: NetFlow v9 Parser** | 13 | 2 XS, 3 S, 4 M, 4 L |
| **M5: CSV Generation** | 6 | 1 XS, 1 S, 3 M, 1 L |
| **M6: Storage Abstraction** | 10 | 2 XS, 1 S, 6 M, 1 L |
| **Total** | **54** | |

---

## Dependency Graph (Simplified)

```
M1.S1 (Maven)
  |
  +-- M1.S2 (App) -- M1.S3 (Config) -- M1.S4 (Netty) -- M1.S5 (Listener) -- M1.S7 (Verify)
  |     +-- M1.S6 (Logging)
  |     +-- M1.S8 (Spock Gate)
  |
  +-- M2.S1 (Version Enum)
  |     +-- M2.S2 (FieldType) --+-- M2.S4 (FlowRecord)
  |     +-- M2.S3 (FlowHeader) -+-- M2.S5 (Parser Interface) -- M2.S6 (Factory)
  |     |                        +-- M2.S7 (Handler Interface)
  |     +-- M2.S8 (Dispatcher) -- M2.S9 (Buffer) -- M2.S10 (Wire)
  |
  +-- M3.S1 (V5Header) --+
  +-- M3.S2 (V5Record) --+-- M3.S3 (V5Parser) -- M3.S5 (V5 Tests)
  +-- M3.S4 (Fixtures) --+
  +-- M3.S6 (LoggingHandler) ----- M3.S7 (V5 E2E)
  |
  +-- M4.S1 (TemplateKind) --+
  +-- M4.S2 (FieldDef) ------+-- M4.S3 (Template) -- M4.S4 (Cache)
  +-- M4.S5 (V9Header) ------+                          |
  +-- M4.S6 (V9Record) ------+-- M4.S7 (V9 Loop) ------+
  |                                 +-- M4.S8 (Template FS)
  |                                 +-- M4.S9 (Options FS)
  |                                 +-- M4.S10 (Data FS)
  +-- M4.S11 (V9 Fixtures) --------+-- M4.S12 (V9 Tests) -- M4.S13 (V9 E2E)
  |
  +-- M5.S1 (CsvConfig) -- M5.S2 (CsvWriter) --+
  +-- M5.S3 (Timestamps) ----------------------+-- M5.S4 (CsvHandler) -- M5.S6 (CSV E2E)
  +-- M5.S5 (Config Update)
  |
  +-- M6.S1 (StorageInterface)
  |     +-- M6.S4 (FTP) --------- M6.S8 (FTP Test)
  |     +-- M6.S5 (S3) ---------- M6.S9 (S3 Test)
  |     +-- M6.S2 (StorageConfig) -- M6.S6 (Async Upload) -- M6.S7 (Retry) -- M6.S10 (Full E2E)
  +-- M6.S3 (Storage Config YAML)
```

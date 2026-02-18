# NetFlow Parser — Implementation Plan

> A Spring Boot 4 application that listens for NetFlow UDP packets, parses them, logs the flow
> records, and eventually exports them to CSV files uploaded to configurable storage backends.

---

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Project Structure](#2-project-structure)
3. [Architecture Overview](#3-architecture-overview)
4. [Milestone Breakdown](#4-milestone-breakdown)
   - [M1: Project Scaffolding](#m1-project-scaffolding)
   - [M2: Core Abstractions](#m2-core-abstractions)
   - [M3: NetFlow v5 Parser](#m3-netflow-v5-parser)
   - [M4: NetFlow v9 Parser](#m4-netflow-v9-parser)
   - [M5: CSV Generation](#m5-csv-generation)
   - [M6: Storage Abstraction & Implementations](#m6-storage-abstraction--implementations)
5. [Testing Strategy](#5-testing-strategy)
6. [Configuration](#6-configuration)
7. [Risks & Mitigations](#7-risks--mitigations)
8. [Future Considerations](#8-future-considerations)
9. [References](#9-references)

---

## 1. Technology Stack

| Component            | Choice                              | Rationale                                                                 |
|----------------------|-------------------------------------|---------------------------------------------------------------------------|
| **Language**         | Java 21 (LTS)                       | Virtual threads for high-throughput UDP, records, sealed classes, pattern matching |
| **Framework**        | Spring Boot 4.0.x / Spring 7.x     | Latest stable; Jakarta EE 11 baseline; broad ecosystem                    |
| **Build**            | Maven                               | Widely adopted, straightforward dependency management                     |
| **UDP Listener**     | Netty 4.x                           | High-performance non-blocking I/O; Spring Boot integrates well via `reactor-netty` |
| **Testing**          | Spock 2.4 (Groovy 5.0)             | Expressive BDD-style specs; `spock-spring` for Spring integration         |
| **Integration Tests**| Testcontainers                      | LocalStack (S3), FTP server containers for realistic integration tests    |
| **Logging**          | SLF4J + Logback (Spring Boot default) | Structured logging of parsed flow records                              |
| **CSV**              | Apache Commons CSV                  | Lightweight, well-maintained CSV library                                  |

---

## 2. Project Structure

```
netflow-java/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/com/netflow/
│   │   │   ├── NetflowApplication.java              # Spring Boot entry point
│   │   │   ├── config/
│   │   │   │   ├── NettyServerConfig.java            # Netty UDP server bean configuration
│   │   │   │   └── StorageConfig.java                # Storage backend bean configuration
│   │   │   ├── listener/
│   │   │   │   ├── UdpPacketListener.java            # Netty UDP channel handler
│   │   │   │   └── PacketDispatcher.java             # Routes packets to version-specific parsers
│   │   │   ├── model/
│   │   │   │   ├── FlowRecord.java                   # Common flow record (interface or sealed)
│   │   │   │   ├── FlowHeader.java                   # Common header (interface or sealed)
│   │   │   │   ├── v5/
│   │   │   │   │   ├── V5Header.java                 # NetFlow v5 header record
│   │   │   │   │   └── V5FlowRecord.java             # NetFlow v5 flow record
│   │   │   │   └── v9/
│   │   │   │       ├── V9Header.java                 # NetFlow v9 header record
│   │   │   │       ├── V9FlowRecord.java             # NetFlow v9 flow record
│   │   │   │       ├── Template.java                 # Template definition
│   │   │   │       └── FieldDefinition.java          # Field type + length in a template
│   │   │   ├── parser/
│   │   │   │   ├── NetflowParser.java                # Parser interface (strategy)
│   │   │   │   ├── NetflowVersion.java               # Enum for supported versions
│   │   │   │   ├── ParserFactory.java                # Resolves parser by version number
│   │   │   │   ├── v5/
│   │   │   │   │   └── V5Parser.java                 # NetFlow v5 parser implementation
│   │   │   │   └── v9/
│   │   │   │       ├── V9Parser.java                 # NetFlow v9 parser implementation
│   │   │   │       └── TemplateCache.java            # Thread-safe template cache
│   │   │   ├── field/
│   │   │   │   ├── FieldType.java                    # Enum of known field type IDs
│   │   │   │   └── FieldRegistry.java                # Registry mapping type IDs to metadata
│   │   │   ├── handler/
│   │   │   │   ├── FlowRecordHandler.java            # Handler interface (observer)
│   │   │   │   ├── LoggingFlowHandler.java           # Logs parsed flow records
│   │   │   │   └── CsvFlowHandler.java               # Writes flow records to CSV
│   │   │   ├── csv/
│   │   │   │   ├── CsvWriter.java                    # CSV file writing logic
│   │   │   │   └── CsvConfig.java                    # CSV field selection, rotation settings
│   │   │   └── storage/
│   │   │       ├── StorageService.java               # Storage abstraction interface
│   │   │       ├── StorageType.java                  # Enum of storage backend types
│   │   │       ├── ftp/
│   │   │       │   └── FtpStorageService.java        # FTP upload implementation
│   │   │       └── s3/
│   │   │           └── S3StorageService.java         # AWS S3 upload implementation
│   │   └── resources/
│   │       ├── application.yml                       # Default configuration
│   │       └── logback-spring.xml                    # Logging configuration
│   └── test/
│       ├── groovy/com/netflow/                       # Spock specifications
│       │   ├── parser/
│       │   │   ├── v5/V5ParserSpec.groovy
│       │   │   └── v9/V9ParserSpec.groovy
│       │   ├── listener/PacketDispatcherSpec.groovy
│       │   ├── handler/CsvFlowHandlerSpec.groovy
│       │   └── storage/
│       │       ├── FtpStorageServiceSpec.groovy
│       │       └── S3StorageServiceSpec.groovy
│       └── resources/
│           └── packets/                              # Binary sample packets for testing
│               ├── v5-single-flow.bin
│               ├── v5-30-flows.bin
│               ├── v9-template.bin
│               ├── v9-data.bin
│               └── v9-template-and-data.bin
```

---

## 3. Architecture Overview

```
                         UDP (port 2055)
                              │
                              ▼
                    ┌──────────────────┐
                    │  UdpPacketListener│  (Netty ChannelInboundHandler)
                    └────────┬─────────┘
                             │  raw bytes
                             ▼
                    ┌──────────────────┐
                    │ PacketDispatcher │  reads version field (first 2 bytes)
                    └───────┬──┬───────┘
                            │  │
               ┌────────────┘  └────────────┐
               ▼                            ▼
      ┌────────────────┐          ┌────────────────┐
      │   V5Parser     │          │   V9Parser     │
      │ (fixed format) │          │ (template-based)│
      └───────┬────────┘          │                │
              │                   │  TemplateCache │
              │                   └───────┬────────┘
              │                           │
              └─────────┬─────────────────┘
                        │  List<FlowRecord>
                        ▼
              ┌──────────────────────┐
              │  FlowRecordHandler   │  (observer pattern)
              │  chain               │
              ├──────────────────────┤
              │  LoggingFlowHandler  │ → SLF4J structured log
              │  CsvFlowHandler      │ → CSV file
              └──────────┬───────────┘
                         │  (on rotation/flush)
                         ▼
              ┌──────────────────────┐
              │   StorageService     │  (strategy pattern)
              ├──────────────────────┤
              │  FtpStorageService   │
              │  S3StorageService    │
              │  (future: GCS, etc.) │
              └──────────────────────┘
```

### Design Patterns

| Pattern      | Where Applied                    | Purpose                                                     |
|--------------|----------------------------------|-------------------------------------------------------------|
| **Strategy** | `NetflowParser` implementations  | Swap parsing logic per NetFlow version                      |
| **Strategy** | `StorageService` implementations | Swap storage backend without changing upload logic           |
| **Factory**  | `ParserFactory`                  | Resolve the correct parser from the version number          |
| **Observer** | `FlowRecordHandler` chain        | Multiple handlers can process the same flow records         |
| **Template Method** | Common parsing boilerplate | Shared header-reading logic with version-specific record parsing |

---

## 4. Milestone Breakdown

### M1: Project Scaffolding

**Goal:** Bootable Spring Boot 4 application with Maven build, Netty UDP listener receiving and logging raw packets.

**Tasks:**

1. **Initialize Maven project** — Create `pom.xml` with:
   - `spring-boot-starter` (4.0.x)
   - `netty-transport` (UDP)
   - `spock-core`, `spock-spring` (2.4-groovy-5.0)
   - `groovy` (5.0.x) for Spock
   - `testcontainers` BOM
   - Maven compiler plugin targeting Java 21
   - GMavenPlus plugin for compiling Groovy test sources
2. **Create `NetflowApplication.java`** — Standard `@SpringBootApplication` entry point
3. **Create `NettyServerConfig.java`** — Configure a Netty `Bootstrap` for UDP:
   - Bind to configurable port (default `2055`)
   - `NioDatagramChannel` with `NioEventLoopGroup`
   - Wire the `UdpPacketListener` as the channel handler
4. **Create `UdpPacketListener.java`** — Netty `SimpleChannelInboundHandler<DatagramPacket>`:
   - Extract `ByteBuf` content from the datagram
   - Convert to `byte[]` and log packet size + source address
   - Forward bytes to `PacketDispatcher`
5. **Create `application.yml`** with:
   ```yaml
   netflow:
     listener:
       port: 2055
       buffer-size: 65535
   ```
6. **Verify** — Application starts, binds UDP port, and logs incoming packets

**Deliverables:** Running Spring Boot app that receives UDP datagrams on port 2055 and logs them.

---

### M2: Core Abstractions

**Goal:** Define the interfaces and shared models that all parser versions and handlers will implement.

**Tasks:**

1. **`NetflowVersion` enum:**
   ```java
   public enum NetflowVersion {
       V5(5), V9(9);
       // ...
   }
   ```

2. **`FlowHeader` sealed interface** — Common header contract:
   ```java
   public sealed interface FlowHeader permits V5Header, V9Header {
       NetflowVersion version();
       int count();
       long sysUpTime();
       long unixSecs();
       long sequenceNumber();
   }
   ```

3. **`FlowRecord` sealed interface** — Common flow record contract:
   ```java
   public sealed interface FlowRecord permits V5FlowRecord, V9FlowRecord {
       String srcAddress();
       String dstAddress();
       int srcPort();
       int dstPort();
       int protocol();
       long bytes();
       long packets();
   }
   ```

4. **`NetflowParser` interface:**
   ```java
   public interface NetflowParser {
       NetflowVersion version();
       ParseResult parse(byte[] data);
   }
   ```
   Where `ParseResult` is a record containing the header and a list of flow records.

5. **`ParserFactory`** — Spring-managed factory:
   ```java
   @Component
   public class ParserFactory {
       private final Map<NetflowVersion, NetflowParser> parsers;
       // Injected via constructor from all NetflowParser beans
       public NetflowParser getParser(int versionNumber) { ... }
   }
   ```

6. **`FlowRecordHandler` interface:**
   ```java
   public interface FlowRecordHandler {
       void handle(FlowHeader header, List<FlowRecord> records);
   }
   ```

7. **`PacketDispatcher`** — Reads version (first 2 bytes), resolves parser via factory, dispatches parsed results to all registered handlers.

8. **`FieldType` enum** — Maps known NetFlow field type IDs to names and default sizes:
   ```java
   public enum FieldType {
       IN_BYTES(1, 4),
       IN_PKTS(2, 4),
       PROTOCOL(4, 1),
       TOS(5, 1),
       TCP_FLAGS(6, 1),
       L4_SRC_PORT(7, 2),
       IPV4_SRC_ADDR(8, 4),
       // ... remaining types from the research doc
       ;
   }
   ```

9. **`FieldRegistry`** — Lookup utility to resolve `FieldType` by numeric ID. Supports unknown/vendor fields gracefully.

**Deliverables:** Interfaces and models compiled; `PacketDispatcher` wires through to a `LoggingFlowHandler` that logs "parsed N flow records from version X".

---

### M3: NetFlow v5 Parser

**Goal:** Fully parse NetFlow v5 packets (24-byte header + N x 48-byte records) and log structured flow data.

**Tasks:**

1. **`V5Header` record** — Immutable record matching the 24-byte header:
   ```java
   public record V5Header(
       int count,
       long sysUpTime,
       long unixSecs,
       long unixNSecs,
       long flowSequence,
       int engineType,
       int engineId,
       int samplingInterval
   ) implements FlowHeader { ... }
   ```

2. **`V5FlowRecord` record** — All 48-byte fields:
   ```java
   public record V5FlowRecord(
       String srcAddr,
       String dstAddr,
       String nextHop,
       int inputInterface,
       int outputInterface,
       long packets,
       long bytes,
       long firstSwitched,
       long lastSwitched,
       int srcPort,
       int dstPort,
       int tcpFlags,
       int protocol,
       int tos,
       int srcAs,
       int dstAs,
       int srcMask,
       int dstMask
   ) implements FlowRecord { ... }
   ```

3. **`V5Parser` implementation:**
   - Wrap `byte[]` in a `ByteBuffer` (big-endian by default)
   - Validate: first 2 bytes must equal `5`
   - Validate: packet length matches `24 + (count * 48)`
   - Parse header fields using unsigned operations (`& 0xFFFF`, `& 0xFFFFFFFFL`)
   - Parse each flow record; convert 4-byte IP fields to `InetAddress` then string
   - Return `ParseResult` with header + list of records
   - Handle edge cases: truncated packets, count = 0, count > 30

4. **`LoggingFlowHandler`** — Logs each flow record with structured fields:
   ```
   Received v5 flow: src=192.168.1.1:443 dst=10.0.0.5:52341 proto=TCP bytes=15234 packets=12
   ```

5. **Wire everything** — Update `PacketDispatcher` to use `ParserFactory` → `V5Parser` → `LoggingFlowHandler`

**Deliverables:** Receiving a v5 UDP packet results in structured log lines for each flow record.

---

### M4: NetFlow v9 Parser

**Goal:** Parse template-based NetFlow v9 packets with template caching, supporting dynamic record structures.

**Tasks:**

1. **`Template` record:**
   ```java
   public record Template(
       int templateId,
       long sourceId,
       List<FieldDefinition> fields,
       Instant receivedAt
   ) {
       public int recordLength() {
           return fields.stream().mapToInt(FieldDefinition::length).sum();
       }
   }
   ```

2. **`FieldDefinition` record:**
   ```java
   public record FieldDefinition(int typeId, int length) {
       public Optional<FieldType> fieldType() {
           return FieldRegistry.lookup(typeId);
       }
   }
   ```

3. **`TemplateCache`:**
   - Thread-safe map keyed by composite key `(sourceId, templateId)`
   - Configurable TTL for template expiration (default: 30 minutes)
   - `put(Template)`, `get(long sourceId, int templateId)` → `Optional<Template>`
   - Uses `ConcurrentHashMap` with periodic eviction or time-based check on read
   - Log warning when a Data FlowSet references an unknown template

4. **`V9Header` record:**
   ```java
   public record V9Header(
       int count,
       long sysUpTime,
       long unixSecs,
       long sequenceNumber,
       long sourceId
   ) implements FlowHeader { ... }
   ```

5. **`V9FlowRecord`** — Dynamic key-value record:
   ```java
   public record V9FlowRecord(
       Map<FieldType, Object> fields,
       Map<Integer, byte[]> unknownFields
   ) implements FlowRecord {
       // Implement FlowRecord interface methods by looking up known keys
       // e.g., srcAddress() → fields.get(FieldType.IPV4_SRC_ADDR)
   }
   ```

6. **`V9Parser` implementation:**
   - Parse 20-byte header
   - Loop through FlowSets based on remaining bytes:
     - **FlowSet ID = 0 (Template FlowSet):** Parse template definitions, store in `TemplateCache`
     - **FlowSet ID = 1 (Options Template FlowSet):** Parse and cache (similar to templates)
     - **FlowSet ID > 255 (Data FlowSet):** Look up template by FlowSet ID; if found, decode records using field definitions; if not found, skip with warning
   - Handle padding bytes at end of FlowSets (align to 32-bit boundary)
   - Compute number of records per Data FlowSet: `(flowSetLength - 4) / template.recordLength()`

7. **IP address handling** — Support both IPv4 (4 bytes) and IPv6 (16 bytes) based on field type

8. **Wire V9Parser** — Register as a Spring bean; `ParserFactory` now resolves both v5 and v9

**Deliverables:** Application parses v9 template and data packets, caches templates, and logs decoded flow records.

---

### M5: CSV Generation

**Goal:** Write parsed flow records to CSV files with configurable field selection and file rotation.

**Tasks:**

1. **`CsvConfig`** — Configuration properties:
   ```yaml
   netflow:
     csv:
       enabled: true
       output-dir: ./output
       fields:
         - timestamp
         - src_ip
         - dst_ip
         - src_port
         - dst_port
         - protocol
         - bytes
         - packets
         - tcp_flags
         - tos
         - src_as
         - dst_as
         - input_if
         - output_if
       rotation:
         strategy: time       # time | size | records
         interval: 5m         # for time-based rotation
         max-size: 100MB      # for size-based rotation
         max-records: 100000  # for record-count rotation
       file-prefix: netflow
   ```

2. **`CsvWriter`:**
   - Uses Apache Commons CSV with the configured field list as headers
   - Writes records to a buffered file in the output directory
   - File naming: `{prefix}_{timestamp}.csv` (e.g., `netflow_20260218_153000.csv`)
   - Manages file rotation based on the configured strategy
   - On rotation: close current file, return the completed file path (for storage upload)

3. **`CsvFlowHandler` implements `FlowRecordHandler`:**
   - Receives parsed flow records
   - Maps `FlowRecord` fields to the configured CSV columns
   - Writes to `CsvWriter`
   - On file rotation, triggers storage upload (if storage is enabled)

4. **Timestamp handling:**
   - Compute absolute timestamp from header `unixSecs` + record `firstSwitched`/`lastSwitched` relative to `sysUpTime`
   - Format as ISO-8601

**Deliverables:** CSV files are generated in the output directory with correct headers and flow data. Files rotate per configuration.

---

### M6: Storage Abstraction & Implementations

**Goal:** Upload completed CSV files to configurable storage backends via a pluggable abstraction.

**Tasks:**

1. **`StorageService` interface:**
   ```java
   public interface StorageService {
       StorageType type();
       void upload(Path localFile, String remotePath);
       boolean healthCheck();
   }
   ```

2. **`StorageType` enum:**
   ```java
   public enum StorageType {
       FTP, S3
       // Extensible — add GCS, AZURE_BLOB, LOCAL, etc.
   }
   ```

3. **Configuration:**
   ```yaml
   netflow:
     storage:
       enabled: true
       type: s3               # s3 | ftp
       remote-path-prefix: netflow/raw/
       ftp:
         host: ftp.example.com
         port: 21
         username: ${FTP_USER}
         password: ${FTP_PASS}
         passive-mode: true
       s3:
         bucket: my-netflow-bucket
         region: us-east-1
         prefix: netflow/raw/
         # Credentials via standard AWS chain (env vars, instance profile, etc.)
   ```

4. **`FtpStorageService`:**
   - Uses Apache Commons Net `FTPClient` / `FTPSClient`
   - Supports passive mode (configurable)
   - Uploads file, verifies completion
   - Handles connection pooling / reconnection

5. **`S3StorageService`:**
   - Uses AWS SDK v2 (`S3Client`)
   - Multipart upload for large files
   - Configurable bucket, prefix, and region
   - Credentials via default provider chain

6. **`StorageConfig`** — Conditional bean registration:
   - `@ConditionalOnProperty(name = "netflow.storage.type", havingValue = "s3")` → registers `S3StorageService`
   - `@ConditionalOnProperty(name = "netflow.storage.type", havingValue = "ftp")` → registers `FtpStorageService`
   - `@ConditionalOnProperty(name = "netflow.storage.enabled", havingValue = "false")` → no-op / skip

7. **Upload trigger** — `CsvFlowHandler` calls `StorageService.upload()` after each file rotation (if enabled). This runs asynchronously via `@Async` or a dedicated executor to avoid blocking the parsing pipeline.

8. **Extensibility for future backends** — Adding a new storage:
   - Implement `StorageService`
   - Add a new value to `StorageType`
   - Add conditional bean configuration
   - Add backend-specific config properties

**Deliverables:** Completed CSV files are automatically uploaded to S3 or FTP after rotation. Storage is disabled by default; enabling it is a configuration change.

---

## 5. Testing Strategy

### Framework & Tools

| Tool                    | Purpose                                              |
|-------------------------|------------------------------------------------------|
| **Spock 2.4**           | All unit and integration specifications              |
| **Testcontainers**      | LocalStack (S3), vsftpd/FTP containers               |
| **Embedded Netty**      | Send test UDP packets to the listener in tests        |
| **Binary test fixtures**| Pre-captured `.bin` files with known NetFlow packets  |

### Test Categories

#### Unit Specs (per milestone)

| Spec                        | What It Verifies                                                  |
|-----------------------------|-------------------------------------------------------------------|
| `V5ParserSpec`              | Parses valid v5 packets; rejects truncated, wrong-version, count=0 |
| `V9ParserSpec`              | Parses templates + data; handles missing templates, padding        |
| `TemplateCacheSpec`         | Put/get, TTL expiration, thread safety                            |
| `PacketDispatcherSpec`      | Correct parser selection by version; unknown version handling      |
| `FieldRegistrySpec`         | Lookup known types, handle unknown type IDs                       |
| `CsvWriterSpec`             | Correct CSV format, header row, field mapping, rotation triggers  |

#### Integration Specs

| Spec                         | What It Verifies                                                    |
|------------------------------|---------------------------------------------------------------------|
| `UdpListenerIntegrationSpec` | Full pipeline: send UDP → parse → log (using embedded Netty client) |
| `FtpStorageServiceSpec`      | Upload to FTP via Testcontainers FTP server                         |
| `S3StorageServiceSpec`       | Upload to S3 via Testcontainers LocalStack                          |
| `CsvPipelineIntegrationSpec` | End-to-end: UDP → parse → CSV → storage upload                     |

### Test Data

Create binary fixtures by hand-crafting `ByteBuffer` payloads matching the protocol spec:

- **v5-single-flow.bin**: 24-byte header + 1 x 48-byte record (72 bytes total)
- **v5-30-flows.bin**: 24-byte header + 30 x 48-byte records (1464 bytes)
- **v9-template.bin**: Header + one Template FlowSet defining common fields
- **v9-data.bin**: Header + one Data FlowSet referencing the above template
- **v9-template-and-data.bin**: Header + Template FlowSet + Data FlowSet in same packet

A test utility class (`TestPacketBuilder`) should provide programmatic construction of valid and malformed packets for edge-case testing.

---

## 6. Configuration

### Full `application.yml` Reference

```yaml
netflow:
  listener:
    port: 2055
    buffer-size: 65535
    worker-threads: 4        # Netty event loop threads

  parser:
    v9:
      template-cache-ttl: 30m
      template-cache-max-size: 10000

  csv:
    enabled: true
    output-dir: ./output
    fields:
      - timestamp
      - src_ip
      - dst_ip
      - src_port
      - dst_port
      - protocol
      - bytes
      - packets
      - tcp_flags
      - tos
      - src_as
      - dst_as
      - input_if
      - output_if
    rotation:
      strategy: time
      interval: 5m
    file-prefix: netflow

  storage:
    enabled: false
    type: s3
    remote-path-prefix: netflow/raw/
    delete-after-upload: true
    ftp:
      host: localhost
      port: 21
      username: user
      password: pass
      passive-mode: true
    s3:
      bucket: my-netflow-bucket
      region: us-east-1
      prefix: netflow/raw/

logging:
  level:
    com.netflow: INFO
    com.netflow.parser: DEBUG
```

---

## 7. Risks & Mitigations

| Risk                                                   | Impact  | Mitigation                                                                              |
|--------------------------------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Spock 2.4 + Spring Boot 4 compatibility**            | Medium  | Spring Boot 4 is reinstating Spock support (issue #48513). Fallback: use `spock-spring` module directly with manual context configuration. Monitor Spock releases. |
| **High UDP packet rate causes drops**                  | High    | Netty's event loop + configurable worker threads. Consider `SO_RCVBUF` tuning. Add packet-loss metrics via sequence number tracking. |
| **v9 data arrives before template**                    | Medium  | Buffer un-parseable Data FlowSets briefly and retry when the template arrives. Log a warning and discard after timeout. |
| **Large CSV files cause memory pressure**              | Low     | Buffered streaming writes; rotate files before they grow too large. |
| **Network errors during storage upload**               | Medium  | Retry with exponential backoff. Keep local files until upload is confirmed. |
| **Template cache memory growth**                       | Low     | Configurable max size + TTL. Evict oldest entries when limit is reached. |

---

## 8. Future Considerations

These are **out of scope** for the initial implementation but should be kept in mind during design:

- **IPFIX (v10) support** — Very similar to v9; extend `V9Parser` or create `IpfixParser` sharing the template infrastructure. Add variable-length field handling and enterprise Information Elements.
- **REST API** — Expose endpoints for querying recent flows, active templates, and collector health.
- **Metrics & Observability** — Spring Boot Actuator + Micrometer for packet rates, parse errors, storage upload latency, template cache stats.
- **Multi-port / Multi-protocol listening** — Support multiple UDP ports or TCP/SCTP for IPFIX.
- **Database storage** — Time-series DB (InfluxDB, TimescaleDB) as an additional `StorageService` implementation.
- **Kafka integration** — Publish parsed flow records to a Kafka topic for downstream processing.
- **GCS / Azure Blob** — Additional `StorageService` implementations following the same pattern.

---

## 9. References

- [NetFlow Protocol Research](../research/netflow-protocol-research.md) — Comprehensive protocol research document
- [RFC 3954 — NetFlow v9](https://www.rfc-editor.org/rfc/rfc3954)
- [RFC 7011 — IPFIX Protocol](https://www.rfc-editor.org/rfc/rfc7011)
- [Cisco NetFlow v5 Format](https://www.cisco.com/c/en/us/td/docs/net_mgmt/netflow_collection_engine/3-6/user/guide/format.html)
- [IANA IPFIX Information Elements](https://www.iana.org/assignments/ipfix/ipfix.xhtml)
- [Spring Boot 4.0 Release Notes](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Release-Notes)
- [Spock Framework 2.4](https://spockframework.org/spock/docs/2.4/release_notes.html)
- [Testcontainers](https://testcontainers.com/)

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
   - Extract sender `InetAddress` from the `DatagramPacket`
   - Convert to `byte[]` and log packet size + source address
   - Forward bytes and sender address to `PacketDispatcher`
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

3. **`FlowRecord` sealed interface** — Common flow record contract. The base interface is kept minimal because v9 templates are arbitrary and may omit any field. Version-specific accessors live on the concrete types:
   ```java
   public sealed interface FlowRecord permits V5FlowRecord, V9FlowRecord {
       /** The NetFlow version that produced this record. */
       NetflowVersion version();

       /**
        * Retrieve a field value by type. Returns Optional.empty() when the
        * field is not present in the record (common for template-based v9).
        */
       Optional<Object> getField(FieldType fieldType);

       /**
        * Convenience accessors — return Optional to accommodate v9 templates that may omit fields.
        * Address accessors fall back to the IPv6 field type when the IPv4 field is absent,
        * so both address families are represented correctly in logs and CSV output.
        */
       default Optional<String> srcAddress() {
           return getField(FieldType.IPV4_SRC_ADDR)
               .or(() -> getField(FieldType.IPV6_SRC_ADDR))
               .map(Object::toString);
       }
       default Optional<String> dstAddress() {
           return getField(FieldType.IPV4_DST_ADDR)
               .or(() -> getField(FieldType.IPV6_DST_ADDR))
               .map(Object::toString);
       }
       default Optional<Integer> srcPort()    { return getField(FieldType.L4_SRC_PORT).map(v -> ((Number) v).intValue()); }
       default Optional<Integer> dstPort()    { return getField(FieldType.L4_DST_PORT).map(v -> ((Number) v).intValue()); }
       default Optional<Integer> protocol()   { return getField(FieldType.PROTOCOL).map(v -> ((Number) v).intValue()); }
       default Optional<Long> bytes()         { return getField(FieldType.IN_BYTES).map(v -> ((Number) v).longValue()); }
       default Optional<Long> packets()       { return getField(FieldType.IN_PKTS).map(v -> ((Number) v).longValue()); }
   }
   ```
   `V5FlowRecord` implements `getField()` by mapping its fixed fields to the corresponding `FieldType`. `V9FlowRecord` delegates to its internal `Map<FieldType, Object>`.

   **Numeric normalization:** v9 field decoding is template-length-driven — field values may arrive as 1-, 2-, 4-, or 8-byte values and end up boxed as `Byte`, `Short`, `Integer`, or `Long` depending on width. **All** typed accessors use safe widening via `((Number) v).intValue()` or `((Number) v).longValue()` so callers always receive a consistent type regardless of the underlying boxed representation. This prevents `ClassCastException` for any template-defined width.

4. **`NetflowParser` interface:**
   ```java
   public interface NetflowParser {
       NetflowVersion version();
       ParseResult parse(byte[] data, InetAddress exporterAddress);
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

7. **`PacketDispatcher`** — Receives raw bytes and the exporter `InetAddress`. **Minimum-length guard:** validates `data.length >= 2` before reading the version field; sub-2-byte datagrams are silently dropped with a DEBUG log (on an unauthenticated UDP listener these are expected noise). Reads version (first 2 bytes), resolves parser via factory (passing the exporter address to v9 for template cache scoping), dispatches parsed results to all registered handlers.

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

4. **`LoggingFlowHandler`** — Logs each flow record with structured fields (uses `Optional`-aware accessors so missing v9 fields render as `N/A`):
   ```
   Received v5 flow: src=192.168.1.1:443 dst=10.0.0.5:52341 proto=TCP bytes=15234 packets=12
   ```

5. **Wire everything** — Update `PacketDispatcher` to use `ParserFactory` → `V5Parser` → `LoggingFlowHandler`

**Deliverables:** Receiving a v5 UDP packet results in structured log lines for each flow record.

---

### M4: NetFlow v9 Parser

**Goal:** Parse template-based NetFlow v9 packets with template caching, supporting dynamic record structures.

**Tasks:**

1. **`TemplateKind` enum** — distinguishes regular flow templates from options templates so the parser can route them correctly:
   ```java
   public enum TemplateKind { FLOW, OPTIONS }
   ```

2. **`Template` record:**
   ```java
   public record Template(
       int templateId,
       long sourceId,
       TemplateKind kind,        // FLOW or OPTIONS
       List<FieldDefinition> fields,
       Instant receivedAt
   ) {
       public int recordLength() {
           return fields.stream().mapToInt(FieldDefinition::length).sum();
       }
       public boolean isOptions() { return kind == TemplateKind.OPTIONS; }
   }
   ```

3. **`FieldDefinition` record:**
   ```java
   public record FieldDefinition(int typeId, int length) {
       public Optional<FieldType> fieldType() {
           return FieldRegistry.lookup(typeId);
       }
   }
   ```

4. **`TemplateCache`:**
   - Thread-safe map keyed by composite key `(exporterIp, exporterPort, sourceId, templateId)` — the exporter IP alone is not enough because in NATed deployments multiple exporters can share one collector-visible IP and reuse common Source IDs / template IDs. Including the UDP source port disambiguates distinct transport sessions behind the same NAT.
   - **Trade-off note:** UDP source ports can change across device reboots or NAT remapping, which would orphan previously cached templates. The configurable TTL (below) handles cleanup; a DEBUG-level log is emitted when a template is re-learned under a new port for the same `(exporterIp, sourceId, templateId)` tuple.
   - Configurable TTL for template expiration (default: 30 minutes)
   - `put(ExporterKey key, Template)`, `get(ExporterKey key, int templateId)` → `Optional<Template>`, `remove(ExporterKey key, int templateId)` → `boolean` (for zero-field template withdrawals) where `ExporterKey` is `record ExporterKey(InetAddress ip, int port, long sourceId)`
   - Uses `ConcurrentHashMap` with periodic eviction or time-based check on read. **Max-size enforcement:** the cache is bounded by `netflow.parser.v9.template-cache-max-size` (default: 10 000 entries). When the limit is reached, the least-recently-used entry is evicted before inserting a new template. This prevents unbounded memory growth under high-cardinality exporter/template-ID combinations where TTL alone is insufficient (templates arrive faster than they expire).
   - Log warning when a Data FlowSet references an unknown template

5. **`V9Header` record:**
   ```java
   public record V9Header(
       int count,
       long sysUpTime,
       long unixSecs,
       long sequenceNumber,
       long sourceId
   ) implements FlowHeader { ... }
   ```

6. **`V9FlowRecord`** — Dynamic key-value record:
   ```java
   public record V9FlowRecord(
       Map<FieldType, Object> fields,
       Map<Integer, byte[]> unknownFields
   ) implements FlowRecord {
       @Override
       public NetflowVersion version() { return NetflowVersion.V9; }

       @Override
       public Optional<Object> getField(FieldType fieldType) {
           return Optional.ofNullable(fields.get(fieldType));
       }
   }
   ```

7. **`V9Parser` implementation:**
   - **Minimum packet length:** Validate `data.length >= 20` at parser entry before reading the v9 header. The dispatcher's `>= 2` guard only ensures version dispatch; a 2–19 byte datagram tagged as version 9 would cause buffer underflow when reading the 20-byte header. Undersized packets are dropped with a WARN log.
   - Parse 20-byte header
   - **FlowSet header read guard:** Before reading the FlowSet ID and length fields, verify `remainingBytes >= 4`. If fewer than 4 bytes remain (1–3 trailing bytes from prior FlowSets or a truncated packet), stop iteration with a DEBUG log — there is not enough data for a valid FlowSet header and attempting the read would throw an underflow/index exception.
   - **FlowSet length validation:** After reading the 4-byte FlowSet header, validate: (a) `length >= 4` (the minimum — 2-byte FlowSet ID + 2-byte length), and (b) `length <= remainingBytes`. If either check fails, log a WARN with the offending value and **drop the rest of the packet** (subsequent FlowSets cannot be located reliably when a length field is corrupt). This prevents a `length=0` from stalling the cursor in an infinite loop and an oversized length from reading past buffer bounds — both trivially exploitable on an unauthenticated UDP collector.
   - Loop through FlowSets based on remaining bytes:
     - **FlowSet ID = 0 (Template FlowSet):** Parse template definitions. **Zero-field withdrawal:** if `fieldCount == 0`, treat the template record as a *withdrawal* — remove the existing entry for that template ID from `TemplateCache` (via `remove(exporterKey, templateId)`) and log at INFO level. This is not defined in RFC 3954 but is standard IPFIX semantics (RFC 7011 §8.1) that some v9 exporters adopt; treating it as a cache removal instead of a rejection prevents stale templates from lingering until TTL expiry during exporter reconfiguration or template refresh cycles. For templates with `fieldCount > 0`, store in `TemplateCache` with `kind = FLOW`. **Per-template bounds check:** before iterating field definitions, verify that the declared body size (`4 + fieldCount * 4` bytes for regular templates) fits within the remaining FlowSet bytes. If it does not, skip the malformed template with a WARN log and stop parsing further templates in this FlowSet (remaining offsets are unreliable).
     - **FlowSet ID = 1 (Options Template FlowSet):** Parse scope/option field definitions. Apply the same zero-field withdrawal logic as for regular templates. For non-empty options templates, store in `TemplateCache` with `kind = OPTIONS`. Apply the same per-template bounds check (`6 + scopeLength + optionLength` bytes, where `scopeLength` and `optionLength` are the byte-length header fields, not field counts) before iterating fields. Options templates optionally can validate that `scopeLength` and `optionLength` are each 4-byte aligned before parsing.
     - **FlowSet ID > 255 (Data FlowSet):** Look up template by FlowSet ID:
       - If not found: skip with warning (template not yet received)
       - If found and `kind = FLOW`: decode as `V9FlowRecord` instances → emit to `FlowRecordHandler` chain
       - If found and `kind = OPTIONS`: decode as exporter metadata (sampling rate, interface info, etc.) → log at DEBUG level only; **do not** emit to `FlowRecordHandler` chain
   - Handle padding bytes at end of FlowSets (align to 32-bit boundary)
   - **Zero-length template guard (defence-in-depth):** Templates with `fieldCount == 0` are handled upstream as withdrawal messages (cache removal), so they should never reach the Data FlowSet decoding path. As a defence-in-depth measure, the Data FlowSet loop still validates `template.recordLength() > 0` before the record-count division and short-circuits with a WARN log if the check fails. This prevents `ArithmeticException` if a zero-field template were ever cached due to a bug in the withdrawal logic.
   - Compute number of records per Data FlowSet: `(flowSetLength - 4) / template.recordLength()`

8. **IP address handling** — Support both IPv4 (4 bytes) and IPv6 (16 bytes) based on field type

9. **Wire V9Parser** — Register as a Spring bean; `ParserFactory` now resolves both v5 and v9

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
   - `firstSwitched` and `lastSwitched` are **exporter-uptime counters** (milliseconds since device boot), not Unix timestamps. The correct conversion per RFC 3954 uses millisecond precision throughout:
     ```
     exportEpochMs  = unixSecs * 1_000 + unixNSecs / 1_000_000
     absoluteTimeMs = exportEpochMs - (sysUpTime - switchedTime)
     ```
     `unixNSecs` is the sub-second residual from the v5 header (`V5Header.unixNSecs`). Including it raises timestamp precision from whole-second to millisecond resolution, which matters for ordering flows that start/end within the same second (dropping it shifts emitted timestamps by up to ~999 ms). The uptime delta is already in milliseconds, so no unit conversion is needed for that term.
   - **32-bit uptime wrap:** Both `sysUpTime` and `switchedTime` are unsigned 32-bit millisecond counters that wrap every ~49.7 days. The delta `(sysUpTime - switchedTime)` must use **unsigned modular subtraction** (i.e., `Integer.toUnsignedLong(sysUpTime - switchedTime)` in Java) so that a flow that started before a wrap boundary and was exported after it still produces the correct positive offset instead of a large negative value that would corrupt the resulting timestamp.
   - Apply the same formula for both `firstSwitched` and `lastSwitched`
   - Format result as ISO-8601 with millisecond precision (e.g. `2026-02-19T14:30:00.123Z`)

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
   - Each backend bean is guarded by **both** conditions combined so no bean is ever created when storage is disabled:
     ```java
     @Bean
     @ConditionalOnProperty(name = "netflow.storage.enabled", havingValue = "true")
     @ConditionalOnProperty(name = "netflow.storage.type",    havingValue = "s3")
     public StorageService s3StorageService(...) { ... }

     @Bean
     @ConditionalOnProperty(name = "netflow.storage.enabled", havingValue = "true")
     @ConditionalOnProperty(name = "netflow.storage.type",    havingValue = "ftp")
     public StorageService ftpStorageService(...) { ... }
     ```
   - When `enabled=false` (the default) no `StorageService` bean is registered at all, eliminating the ambiguous-candidate risk.
   - `CsvFlowHandler` declares `StorageService` as an `Optional` injection (`@Autowired(required = false)`) so it starts cleanly even when no backend is active.

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
| `V9ParserSpec`              | Parses templates + data; options data skipped from flow pipeline; handles missing templates, padding |
| `TemplateCacheSpec`         | Put/get, TTL expiration, thread safety, FLOW vs OPTIONS kind distinction |
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

# NetFlow Java Parser

A Java-based parser for Cisco NetFlow traffic monitoring data, supporting multiple versions of the NetFlow protocol.

## What is NetFlow?

NetFlow is a network protocol developed by Cisco Systems for collecting IP traffic information and monitoring network flow. It was originally introduced in Cisco IOS 11.1 in 1996. A **flow** is defined as a unidirectional sequence of packets that share the same:

- Source and destination IP address
- Source and destination port
- IP protocol
- Type of Service (ToS)
- Input logical interface

NetFlow data is exported by a **Flow Exporter** (typically a router or switch) to a **Flow Collector**, where it can be stored and analyzed. This architecture makes NetFlow valuable for:

- **Network traffic analysis** — understand what traffic flows through your network
- **Security monitoring** — detect anomalies, port scans, and DDoS attacks
- **Capacity planning** — identify bandwidth bottlenecks
- **Billing and accounting** — measure traffic per customer or application

## Protocol Versions

### NetFlow v5 (Most Common)
The most widely deployed version. Exports fixed-length records with a 24-byte header and 48-byte flow records. Only supports IPv4.

**Header fields:** version, count, uptime, timestamp, sequence number, engine type/ID.

**Flow record fields:** source/destination IP, next-hop IP, interface indexes (SNMP), packet/byte counts, timestamps, source/destination ports, TCP flags, protocol, ToS, source/destination AS numbers, prefix lengths.

Reference: [Cisco NetFlow v5 Format](https://www.cisco.com/c/en/us/td/docs/net_mgmt/netflow_collection_engine/3-6/user/guide/format.html)

### NetFlow v9 (Template-Based)
Introduced in RFC 3954. Uses a flexible, template-based format that allows exporters to define their own record structure. Supports both IPv4 and IPv6, MPLS, BGP next-hop, and more.

Key concepts:
- **Templates** define the fields included in data records
- **Options Templates** carry metadata about the exporter itself
- Templates are sent periodically so collectors can decode data records

Reference: [RFC 3954 - Cisco Systems NetFlow Services Export Version 9](https://www.rfc-editor.org/rfc/rfc3954)

### IPFIX (v10 / IP Flow Information Export)
The IETF standardization of NetFlow v9, defined in RFC 7011. Considered the successor to NetFlow v9 with a wider set of standard information elements and enterprise-defined extensions.

Reference: [RFC 7011 - Specification of the IPFIX Protocol](https://www.rfc-editor.org/rfc/rfc7011)

## Packet Structure

### NetFlow v5 Packet Layout

```
+---------------------------+
|       Header (24 bytes)   |
|  version | count          |
|  sys uptime               |
|  unix timestamp (sec)     |
|  unix timestamp (nsec)    |
|  flow sequence            |
|  engine type | engine id  |
|  sampling interval        |
+---------------------------+
|   Flow Record 1 (48 bytes)|
+---------------------------+
|   Flow Record 2 (48 bytes)|
+---------------------------+
|          ...              |
+---------------------------+
|   Flow Record N (48 bytes)|
+---------------------------+
```

### NetFlow v9 Packet Layout

```
+-------------------------------+
|        Header (20 bytes)      |
|  version=9 | count            |
|  sys uptime                   |
|  unix timestamp               |
|  package sequence             |
|  source id                    |
+-------------------------------+
|  FlowSet 1 (Template or Data) |
+-------------------------------+
|  FlowSet 2                    |
+-------------------------------+
|            ...                |
+-------------------------------+
```

## Implementation Plan

This project will be implemented in phases:

1. **Phase 1 — NetFlow v5 Parser**
   - UDP listener to receive exported packets
   - Binary parser for the v5 fixed header and flow records
   - Java model classes for header and flow record fields
   - Console output / JSON serialization of parsed flows

2. **Phase 2 — NetFlow v9 Parser**
   - Template management and caching
   - Options template handling
   - Dynamic record decoding based on received templates

3. **Phase 3 — IPFIX Support**
   - Extend v9 parser to handle IPFIX information elements
   - Enterprise-defined element support

4. **Phase 4 — Storage & Export**
   - Write parsed flows to CSV, JSON, or a time-series database
   - REST API for querying stored flows

## References

- [RFC 3954 — NetFlow v9](https://www.rfc-editor.org/rfc/rfc3954)
- [RFC 7011 — IPFIX Protocol Specification](https://www.rfc-editor.org/rfc/rfc7011)
- [Cisco NetFlow v5/v8 Export Format](https://www.cisco.com/c/en/us/td/docs/net_mgmt/netflow_collection_engine/3-6/user/guide/format.html)
- [IANA IPFIX Information Elements](https://www.iana.org/assignments/ipfix/ipfix.xhtml)
- [nfdump — open-source NetFlow collector](https://github.com/phaag/nfdump)

## Build & Run

> Build configuration coming soon (Maven/Gradle).

```bash
# Example (once implemented)
mvn clean package
java -jar target/netflow-java.jar --port 2055
```

## License

MIT

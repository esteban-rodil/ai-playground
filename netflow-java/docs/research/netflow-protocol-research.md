# NetFlow Protocol Research

> Comprehensive research document covering the NetFlow protocol, its versions, packet formats,
> use cases, related protocols, and implementation references for building a Java-based NetFlow library.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [NetFlow Versions](#3-netflow-versions)
   - [Version 1](#31-netflow-v1)
   - [Version 5](#32-netflow-v5)
   - [Version 9](#33-netflow-v9)
4. [IPFIX (NetFlow v10)](#4-ipfix-netflow-v10)
5. [Packet Format Specifications](#5-packet-format-specifications)
   - [NetFlow v5 Packet Format](#51-netflow-v5-packet-format)
   - [NetFlow v9 Packet Format](#52-netflow-v9-packet-format)
6. [Field Type Definitions](#6-field-type-definitions)
7. [Related Flow Protocols](#7-related-flow-protocols)
8. [Use Cases](#8-use-cases)
9. [Java Implementation Reference](#9-java-implementation-reference)
10. [RFCs and Standards](#10-rfcs-and-standards)
11. [References](#11-references)

---

## 1. Overview

**NetFlow** is a network protocol developed by Cisco Systems (circa 1996) for collecting IP network
traffic information as it enters or exits a router interface. It enables network administrators to
determine the source and destination of traffic, class of service, and causes of congestion.

A **network flow** is defined as a unidirectional sequence of packets sharing a common set of
attributes. Traditional NetFlow identifies flows using a **7-tuple**:

| # | Key Field                  |
|---|----------------------------|
| 1 | Source IP Address           |
| 2 | Destination IP Address      |
| 3 | Source Port (TCP/UDP)       |
| 4 | Destination Port (TCP/UDP)  |
| 5 | IP Protocol (e.g., TCP=6, UDP=17) |
| 6 | Type of Service (ToS)       |
| 7 | Input Interface (SNMP ifIndex)    |

When any of these values differs, a new flow is created. Flow records are exported over **UDP**
(commonly on port **2055**, though 9555 and 9995 are also used) to a collector for storage and analysis.

### Key Characteristics

- **Unidirectional**: Each flow represents traffic in one direction only
- **Stateful tracking**: The exporter maintains flow state in memory (cache)
- **Summarized data**: Exports metadata about conversations, not full packet payloads
- **UDP transport**: Flow records are exported via UDP datagrams (no delivery guarantee)

---

## 2. Architecture

A typical NetFlow deployment consists of three components:

```
┌──────────────┐         UDP          ┌──────────────┐         ┌──────────────────┐
│              │  ──── NetFlow ─────>  │              │  ────>  │                  │
│ Flow Exporter│    Export Packets     │Flow Collector│         │ Analysis/Reporting│
│ (Router/     │                      │ (Storage &   │         │ Application       │
│  Switch)     │                      │  Processing) │         │                  │
└──────────────┘                      └──────────────┘         └──────────────────┘
```

| Component              | Responsibility                                                                 |
|------------------------|--------------------------------------------------------------------------------|
| **Flow Exporter**      | Aggregates packets into flows, maintains a flow cache, and exports flow records when flows expire or the cache is flushed. |
| **Flow Collector**     | Receives, validates, stores, and pre-processes flow data from one or more exporters. |
| **Analysis Application** | Analyzes flow data for traffic profiling, anomaly detection, capacity planning, or intrusion detection. |

### Flow Lifecycle

1. A packet arrives at the exporter interface
2. The exporter checks if the packet belongs to an existing flow (7-tuple match)
3. If yes, counters (bytes, packets) are updated; if no, a new flow entry is created
4. Flows are exported when they expire (idle timeout, active timeout, cache full, or TCP FIN/RST)
5. The collector receives the UDP datagram containing one or more flow records

---

## 3. NetFlow Versions

### 3.1 NetFlow v1

The original version of NetFlow. It was superseded quickly and is now **obsolete**.

- Limited to IPv4 only
- No support for IP network masks or autonomous system numbers (ASNs)
- No sequence numbers for detecting lost datagrams
- Versions 2, 3, and 4 were internal Cisco versions and were never publicly released

### 3.2 NetFlow v5

NetFlow v5 is the **most widely deployed** version and remains in broad use today. It introduced
several enhancements over v1, including BGP autonomous system information and flow sequence numbers.

**Key characteristics:**

- **Fixed record format** — every flow record contains the same set of fields (48 bytes per record)
- **IPv4 only** — no IPv6 support
- **Ingress only** — monitors only incoming traffic at the interface
- **Up to 30 flow records** per export datagram
- **24-byte header** + N x 48-byte records

**Limitations:**

| Limitation              | Impact                                                   |
|-------------------------|----------------------------------------------------------|
| Fixed fields            | Cannot export custom or vendor-specific data              |
| IPv4 only               | No support for IPv6, MPLS, or VXLAN                      |
| Ingress only            | Cannot monitor egress (outgoing) traffic                  |
| No templates            | Collector must hardcode the record layout                 |

Despite these limitations, v5 remains viable for environments that only need IPv4 monitoring with
the standard set of traffic attributes.

### 3.3 NetFlow v9

NetFlow v9 introduced a **template-based** architecture, often referred to as **Flexible NetFlow**.
This is a fundamental shift from v5's fixed format.

**Key characteristics:**

- **Template-based** — record structure is defined dynamically by template records
- **IPv6 support** — full support for IPv6 traffic monitoring
- **Egress support** — can monitor both ingress and egress traffic
- **Extensible** — new field types can be added without changing the protocol format
- **MPLS and VLAN support** — can export labels and VLAN IDs
- **20-byte header** + FlowSets (template, data, or options)

**How templates work:**

1. The exporter sends a **Template FlowSet** defining the structure (field types and lengths)
2. Each template has a unique **Template ID** (>255)
3. Subsequent **Data FlowSets** reference a Template ID
4. The collector caches templates and uses them to parse incoming data records
5. Templates are periodically refreshed (by packet count or time interval)

The collector **must** receive the template before it can parse any data records that reference it.
If a template is missed, the corresponding data records cannot be decoded until the template is
re-sent.

---

## 4. IPFIX (NetFlow v10)

**IPFIX** (IP Flow Information Export) is the **IETF standard** derived from NetFlow v9. It is
sometimes referred to as "NetFlow v10" due to its lineage.

- Published as **RFC 7011** (obsoletes RFC 5101) in 2013
- Template-based, like NetFlow v9, but with additional capabilities
- **Vendor-neutral** — supported by Barracuda, Nortel, Juniper, Xirrus, and many others
- Supports **variable-length fields** (NetFlow v9 does not)
- Supports **SCTP** and **TCP** transport in addition to UDP
- Enterprise-specific Information Elements allow vendor extensions

### NetFlow v5 vs v9 vs IPFIX Comparison

| Feature                     | NetFlow v5         | NetFlow v9         | IPFIX              |
|-----------------------------|--------------------|--------------------|---------------------|
| **Record format**           | Fixed              | Template-based     | Template-based      |
| **IPv6 support**            | No                 | Yes                | Yes                 |
| **MPLS / VXLAN**            | No                 | Yes                | Yes                 |
| **Egress monitoring**       | No                 | Yes                | Yes                 |
| **Variable-length fields**  | No                 | No                 | Yes                 |
| **Transport protocols**     | UDP                | UDP                | UDP, TCP, SCTP      |
| **Standard**                | Proprietary Cisco  | Proprietary Cisco  | IETF (RFC 7011)     |
| **Vendor support**          | Broad (legacy)     | Cisco + others     | Vendor-neutral      |
| **Extensibility**           | None               | Template fields    | Templates + enterprise IEs |

---

## 5. Packet Format Specifications

### 5.1 NetFlow v5 Packet Format

A NetFlow v5 export datagram consists of a **24-byte header** followed by one or more **48-byte
flow records** (maximum 30 records per packet).

#### 5.1.1 Header (24 bytes)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Version (5)             |            Count              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          SysUpTime                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          UNIX Secs                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          UNIX NSecs                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Flow Sequence                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Engine Type  |   Engine ID   |     Sampling Interval         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Offset | Size    | Field                | Description                                                  |
|--------|---------|----------------------|--------------------------------------------------------------|
| 0      | 2 bytes | **Version**          | Export format version (`5`)                                  |
| 2      | 2 bytes | **Count**            | Number of flow records in this packet (1–30)                 |
| 4      | 4 bytes | **SysUpTime**        | Milliseconds since the exporter booted                       |
| 8      | 4 bytes | **UNIX Secs**        | Seconds since epoch (1970-01-01 00:00 UTC)                   |
| 12     | 4 bytes | **UNIX NSecs**       | Residual nanoseconds since epoch                             |
| 16     | 4 bytes | **Flow Sequence**    | Sequence counter of total flows exported                     |
| 20     | 1 byte  | **Engine Type**      | Type of flow-switching engine (RP=0, VIP/LC=1)               |
| 21     | 1 byte  | **Engine ID**        | Slot number of the flow-switching engine                     |
| 22     | 2 bytes | **Sampling Interval**| First 2 bits = sampling mode; remaining 14 bits = interval   |

**Sequence number usage:** Because NetFlow uses UDP (unreliable), the sequence number allows the
collector to detect lost datagrams. The expected sequence equals the previous datagram's sequence
plus its flow count. Any gap indicates lost exports.

#### 5.1.2 Flow Record (48 bytes)

Each v5 flow record is exactly 48 bytes:

| Offset | Size    | Field              | Description                                           |
|--------|---------|--------------------|-------------------------------------------------------|
| 0      | 4 bytes | **srcAddr**        | Source IP address                                     |
| 4      | 4 bytes | **dstAddr**        | Destination IP address                                |
| 8      | 4 bytes | **nextHop**        | IP address of next-hop router                         |
| 12     | 2 bytes | **input**          | SNMP ifIndex of input interface                       |
| 14     | 2 bytes | **output**         | SNMP ifIndex of output interface                      |
| 16     | 4 bytes | **dPkts**          | Packets in the flow                                   |
| 20     | 4 bytes | **dOctets**        | Total bytes (Layer 3) in the flow                     |
| 24     | 4 bytes | **first**          | SysUpTime at start of flow (ms)                       |
| 28     | 4 bytes | **last**           | SysUpTime at time of last packet (ms)                 |
| 32     | 2 bytes | **srcPort**        | TCP/UDP source port or equivalent                     |
| 34     | 2 bytes | **dstPort**        | TCP/UDP destination port or equivalent                |
| 36     | 1 byte  | **pad1**           | Unused (zero)                                         |
| 37     | 1 byte  | **tcpFlags**       | Cumulative OR of TCP flags over flow lifetime         |
| 38     | 1 byte  | **prot**           | IP protocol type (TCP=6, UDP=17, ICMP=1)              |
| 39     | 1 byte  | **tos**            | IP Type of Service byte                               |
| 40     | 2 bytes | **srcAs**          | Source autonomous system number (BGP)                 |
| 42     | 2 bytes | **dstAs**          | Destination autonomous system number (BGP)            |
| 44     | 1 byte  | **srcMask**        | Source address prefix mask bits (CIDR)                |
| 45     | 1 byte  | **dstMask**        | Destination address prefix mask bits (CIDR)           |
| 46     | 2 bytes | **pad2**           | Unused (zero)                                         |

**Total datagram size** = 24 + (Count x 48) bytes. Maximum = 24 + (30 x 48) = **1464 bytes**.

> **Note on ICMP flows:** For ICMP, the source port field is zero, and the destination port
> encodes the ICMP message Type (high byte) and Code (low byte).

### 5.2 NetFlow v9 Packet Format

A NetFlow v9 export packet consists of a **20-byte header** followed by one or more **FlowSets**.

#### 5.2.1 Header (20 bytes)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Version (9)             |            Count              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          SysUpTime                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          UNIX Secs                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Sequence Number                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          Source ID                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Offset | Size    | Field               | Description                                                  |
|--------|---------|---------------------|--------------------------------------------------------------|
| 0      | 2 bytes | **Version**         | Export format version (`9`)                                  |
| 2      | 2 bytes | **Count**           | Total number of records (template + data + options) in packet|
| 4      | 4 bytes | **SysUpTime**       | Milliseconds since the exporter booted                       |
| 8      | 4 bytes | **UNIX Secs**       | Seconds since epoch (1970-01-01 00:00 UTC)                   |
| 12     | 4 bytes | **Sequence Number** | Incremental sequence counter of all export packets           |
| 16     | 4 bytes | **Source ID**       | Identifies the Observation Domain (exporter + domain)        |

> **Key difference from v5:** The v9 Count field counts total *records* across all FlowSets,
> not just flow data records. The Sequence Number counts *packets*, not flows.

#### 5.2.2 FlowSets

FlowSets are the building blocks of v9 packets. There are three types:

| FlowSet Type             | FlowSet ID | Description                                               |
|--------------------------|------------|-----------------------------------------------------------|
| **Template FlowSet**     | 0          | Defines the structure of future data records               |
| **Options Template FlowSet** | 1     | Defines options data (scope and option fields)             |
| **Data FlowSet**         | > 255      | Contains actual flow records; ID maps to a Template ID     |

**FlowSet IDs 2–255 are reserved.**

#### 5.2.3 Template FlowSet Structure

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       FlowSet ID (0)          |          Length               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Template ID             |        Field Count            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Field Type 1            |        Field Length 1         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Field Type 2            |        Field Length 2         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       ...                     |        ...                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field           | Size    | Description                                              |
|-----------------|---------|----------------------------------------------------------|
| **FlowSet ID**  | 2 bytes | Always `0` for Template FlowSets                        |
| **Length**       | 2 bytes | Total length of this FlowSet in bytes                    |
| **Template ID** | 2 bytes | Unique ID for this template (>255)                       |
| **Field Count** | 2 bytes | Number of field definitions in this template             |
| **Field Type**  | 2 bytes | Numeric identifier for the field (see Section 6)         |
| **Field Length** | 2 bytes | Length of the field value in bytes                       |

A single Template FlowSet can contain **multiple template definitions**.

#### 5.2.4 Data FlowSet Structure

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   FlowSet ID (= Template ID) |          Length               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Record 1 Fields                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Record 2 Fields                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        ...                                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Padding (0–3 bytes)                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field          | Size     | Description                                                 |
|----------------|----------|-------------------------------------------------------------|
| **FlowSet ID** | 2 bytes  | Maps to a previously received Template ID (>255)            |
| **Length**      | 2 bytes  | Total length including ID, length, records, and padding     |
| **Records**    | Variable | Field values as defined by the referenced template          |
| **Padding**    | 0–3 bytes| Aligns the FlowSet to a 32-bit boundary                    |

#### 5.2.5 Template Management

- Templates must be received **before** data records can be parsed
- Templates are refreshed periodically (configurable by packet count or time interval)
- If a template is not refreshed, it expires and associated data records become un-parseable
- The collector **must cache** all received templates keyed by (Source ID, Template ID)
- A new template with the same ID replaces the cached version

---

## 6. Field Type Definitions

The following table lists the most commonly used field type IDs as defined in RFC 3954 and Cisco
documentation. These IDs are used in NetFlow v9 template definitions and IPFIX Information Elements.

| Type ID | Name                | Size (bytes) | Description                                        |
|---------|---------------------|-------------:|----------------------------------------------------|
| 1       | `IN_BYTES`          | 4 (or 8)    | Incoming counter for bytes in the flow              |
| 2       | `IN_PKTS`           | 4 (or 8)    | Incoming counter for packets in the flow            |
| 3       | `FLOWS`             | 4            | Number of flows aggregated                          |
| 4       | `PROTOCOL`          | 1            | IP protocol type (TCP=6, UDP=17, ICMP=1)            |
| 5       | `TOS`               | 1            | Type of Service byte                                |
| 6       | `TCP_FLAGS`         | 1            | Cumulative OR of TCP flags                          |
| 7       | `L4_SRC_PORT`       | 2            | TCP/UDP source port                                 |
| 8       | `IPV4_SRC_ADDR`     | 4            | Source IPv4 address                                 |
| 9       | `SRC_MASK`          | 1            | Source address prefix mask bits                     |
| 10      | `INPUT_SNMP`        | 2 (or 4)    | Input interface SNMP ifIndex                        |
| 11      | `L4_DST_PORT`       | 2            | TCP/UDP destination port                            |
| 12      | `IPV4_DST_ADDR`     | 4            | Destination IPv4 address                            |
| 13      | `DST_MASK`          | 1            | Destination address prefix mask bits                |
| 14      | `OUTPUT_SNMP`       | 2 (or 4)    | Output interface SNMP ifIndex                       |
| 15      | `IPV4_NEXT_HOP`     | 4            | IPv4 address of the next-hop router                 |
| 16      | `SRC_AS`            | 2 (or 4)    | Source BGP autonomous system number                 |
| 17      | `DST_AS`            | 2 (or 4)    | Destination BGP autonomous system number            |
| 18      | `BGP_IPV4_NEXT_HOP` | 4            | BGP next-hop IPv4 address                           |
| 21      | `LAST_SWITCHED`     | 4            | SysUpTime when last packet of flow was switched     |
| 22      | `FIRST_SWITCHED`    | 4            | SysUpTime when first packet of flow was switched    |
| 27      | `IPV6_SRC_ADDR`     | 16           | Source IPv6 address                                 |
| 28      | `IPV6_DST_ADDR`     | 16           | Destination IPv6 address                            |
| 29      | `IPV6_SRC_MASK`     | 1            | Source IPv6 prefix mask bits                        |
| 30      | `IPV6_DST_MASK`     | 1            | Destination IPv6 prefix mask bits                   |
| 32      | `ICMP_TYPE`         | 2            | ICMP type * 256 + ICMP code                         |
| 40      | `TOTAL_BYTES_EXP`   | 4 (or 8)    | Counter for bytes exported by the exporter          |
| 41      | `TOTAL_PKTS_EXP`    | 4 (or 8)    | Counter for packets exported by the exporter        |
| 46      | `MPLS_TOP_LABEL_TYPE` | 1          | MPLS top label type                                 |
| 56      | `IN_SRC_MAC`        | 6            | Source MAC address (incoming)                       |
| 58      | `VLAN_ID`           | 2            | VLAN ID of the incoming packet                      |
| 61      | `DIRECTION`         | 1            | Flow direction: 0=ingress, 1=egress                 |
| 62      | `IPV6_NEXT_HOP`     | 16           | IPv6 address of the next-hop router                 |

> The full list contains over 100 field types. See RFC 3954 Section 8 and the
> [IANA IPFIX Information Elements registry](https://www.iana.org/assignments/ipfix/ipfix.xhtml)
> for the complete reference.

### NetFlow v5 to v9 Field Mapping

When representing v5 fixed fields as v9 template fields:

| v5 Record Field | v9 Field Type ID | v9 Field Name       |
|-----------------|------------------|----------------------|
| srcAddr         | 8                | `IPV4_SRC_ADDR`     |
| dstAddr         | 12               | `IPV4_DST_ADDR`     |
| nextHop         | 15               | `IPV4_NEXT_HOP`     |
| input           | 10               | `INPUT_SNMP`        |
| output          | 14               | `OUTPUT_SNMP`       |
| dPkts           | 2                | `IN_PKTS`           |
| dOctets         | 1                | `IN_BYTES`          |
| first           | 22               | `FIRST_SWITCHED`    |
| last            | 21               | `LAST_SWITCHED`     |
| srcPort         | 7                | `L4_SRC_PORT`       |
| dstPort         | 11               | `L4_DST_PORT`       |
| tcpFlags        | 6                | `TCP_FLAGS`         |
| prot            | 4                | `PROTOCOL`          |
| tos             | 5                | `TOS`               |
| srcAs           | 16               | `SRC_AS`            |
| dstAs           | 17               | `DST_AS`            |
| srcMask         | 9                | `SRC_MASK`          |
| dstMask         | 13               | `DST_MASK`          |

---

## 7. Related Flow Protocols

NetFlow is not the only flow monitoring protocol. Several vendor-specific and open alternatives
exist:

| Protocol       | Vendor/Origin     | Description                                                      |
|----------------|-------------------|------------------------------------------------------------------|
| **NetFlow**    | Cisco             | Original flow protocol; v5 (fixed) and v9 (template-based)       |
| **IPFIX**      | IETF Standard     | Standardized evolution of NetFlow v9; vendor-neutral              |
| **sFlow**      | InMon Corporation | Packet-sampling protocol; samples 1-in-N packets                 |
| **J-Flow**     | Juniper Networks  | Juniper's flow protocol; largely compatible with NetFlow v5/v9    |
| **NetStream**  | Huawei / 3Com     | Huawei's NetFlow equivalent                                      |
| **cflowd**     | Alcatel-Lucent    | Flow data collection daemon; NetFlow-compatible                   |
| **RFlow**      | Ericsson          | Ericsson's flow export format                                     |

### NetFlow vs sFlow

| Aspect                | NetFlow                              | sFlow                                  |
|-----------------------|--------------------------------------|----------------------------------------|
| **Method**            | Full flow tracking (stateful)        | Packet sampling (stateless)            |
| **Accuracy**          | High (tracks every packet)           | Statistical (samples 1-in-N)           |
| **Device overhead**   | Higher CPU/memory (maintains cache)  | Very low (no flow cache)               |
| **Layer support**     | IP traffic (L3-L4)                   | L2-L7 (network-layer independent)      |
| **Non-IP traffic**    | Not captured                         | Captured (Ethernet, FC, etc.)          |
| **Payload visibility**| No                                   | Partial (sampled packet headers/payload)|
| **Best for**          | Accuracy-focused enterprise/WAN      | High-speed data centers, scale         |

### NetFlow vs IPFIX

- IPFIX is essentially "NetFlow v10" — derived directly from NetFlow v9
- IPFIX adds **variable-length fields**, **SCTP/TCP transport**, and **enterprise IEs**
- IPFIX is the recommended choice for **new deployments** and **multi-vendor environments**
- Many modern collectors accept both NetFlow and IPFIX interchangeably

---

## 8. Use Cases

### 8.1 Network Monitoring and Visibility

- Identify **top talkers** and **top listeners** on the network
- Visualize traffic patterns across routers, switches, and the entire network
- Proactive problem detection, efficient troubleshooting, and rapid resolution
- Monitor interface utilization and traffic distribution

### 8.2 Security Analysis and Threat Detection

- **DDoS detection**: Many flows from multiple sources to one destination indicates a volumetric attack
- **Port scanning**: Many flows from one source to many destination ports
- **Data exfiltration**: Unusually large outbound flows to external destinations
- **Lateral movement**: Retrospective flow analysis to trace attacker movement during incident response
- **Anomaly detection**: Establish baselines and alert on deviations from normal traffic patterns
- Combine with DNS records to identify suspicious or malicious traffic

### 8.3 Bandwidth and Traffic Engineering

- Determine which users, applications, and protocols consume the most bandwidth
- Verify that QoS policies allocate appropriate bandwidth per Class of Service
- Identify over- or under-subscribed traffic classes
- Inform strategic decisions on peering, transit, and backbone upgrades

### 8.4 Capacity Planning

- Analyze historical traffic trends to forecast future bandwidth requirements
- Identify peak usage times and plan provisioning accordingly
- Usage-based billing for departments or customers

### 8.5 Compliance and Forensics

- Maintain historical flow records for audit and regulatory compliance
- Forensic investigation: who communicated with whom, when, and how much data was transferred
- Flow records serve as evidence in security incident investigations

### 8.6 Cloud Environments

- **AWS VPC Flow Logs**, **Azure NSG Flow Logs**, and **GCP VPC Flow Logs** provide similar
  flow-level visibility in public cloud environments
- Verify security group rules and detect anomalous inter-zone traffic

---

## 9. Java Implementation Reference

### 9.1 Existing Java Libraries and Projects

| Project                         | Description                                                  | Version Support      |
|---------------------------------|--------------------------------------------------------------|----------------------|
| **Graylog NetFlow Plugin**      | Full NetFlow collector with v5 and v9 parsers (Netty-based)  | v5, v9               |
| **JNCA**                        | Java NetFlow Collect/Analyzer; stores to DB via JDBC          | v1, v5, v7, v8, v9  |
| **LUMASERV netflow-java**       | Lightweight v9 parser and collector library                   | v9                   |

### 9.2 Collector Architecture (Java)

A basic Java NetFlow collector follows this pattern:

```
┌──────────────────────────────────────────────────┐
│                  UDP Listener                     │
│           (DatagramSocket on port 2055)           │
├──────────────────────────────────────────────────┤
│                 Packet Dispatcher                 │
│        (Reads version field, routes to parser)    │
├────────────────────┬─────────────────────────────┤
│   V5 Parser        │        V9 Parser             │
│  (Fixed format)    │  (Template-based)            │
│                    │  ┌─────────────────────┐     │
│                    │  │  Template Cache      │     │
│                    │  │  (Source ID + Tmpl ID)│     │
│                    │  └─────────────────────┘     │
├────────────────────┴─────────────────────────────┤
│               Flow Record Handler                 │
│       (Callback / Queue / Storage)                │
└──────────────────────────────────────────────────┘
```

### 9.3 Key Implementation Considerations

**Byte order**: All NetFlow fields are in **network byte order (big-endian)**. Java's `ByteBuffer`
defaults to big-endian, making it a natural fit. Use `ByteBuffer.wrap(byte[])` to wrap raw UDP
datagram data.

**Parsing v5 packets (pseudocode):**

```java
// 1. Receive UDP datagram
DatagramSocket socket = new DatagramSocket(2055);
byte[] buffer = new byte[1500]; // Max UDP payload
DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
socket.receive(packet);

// 2. Wrap in ByteBuffer (already big-endian by default)
ByteBuffer buf = ByteBuffer.wrap(packet.getData(), 0, packet.getLength());

// 3. Parse header (24 bytes)
int version = buf.getShort() & 0xFFFF;   // offset 0: should be 5
int count   = buf.getShort() & 0xFFFF;   // offset 2: flow count (1-30)
long sysUpTime  = buf.getInt() & 0xFFFFFFFFL;  // offset 4
long unixSecs   = buf.getInt() & 0xFFFFFFFFL;  // offset 8
long unixNSecs  = buf.getInt() & 0xFFFFFFFFL;  // offset 12
long flowSeq    = buf.getInt() & 0xFFFFFFFFL;  // offset 16
int engineType  = buf.get() & 0xFF;            // offset 20
int engineId    = buf.get() & 0xFF;            // offset 21
int samplingInterval = buf.getShort() & 0xFFFF; // offset 22

// 4. Parse each flow record (48 bytes each)
for (int i = 0; i < count; i++) {
    byte[] srcAddrBytes = new byte[4];
    buf.get(srcAddrBytes);
    InetAddress srcAddr = InetAddress.getByAddress(srcAddrBytes);
    // ... parse remaining 44 bytes per record
}
```

**Parsing v9 packets (key differences):**

```java
// 1. Parse header (20 bytes) — similar to v5 but with Source ID
// 2. Loop through FlowSets until end of packet:
while (buf.remaining() > 4) {
    int flowSetId = buf.getShort() & 0xFFFF;
    int length    = buf.getShort() & 0xFFFF;

    if (flowSetId == 0) {
        // Template FlowSet — parse and cache template definitions
        parseTemplateFlowSet(buf, length - 4);
    } else if (flowSetId == 1) {
        // Options Template FlowSet
        parseOptionsTemplateFlowSet(buf, length - 4);
    } else if (flowSetId > 255) {
        // Data FlowSet — look up template by flowSetId
        Template tmpl = templateCache.get(sourceId, flowSetId);
        if (tmpl != null) {
            parseDataFlowSet(buf, length - 4, tmpl);
        } else {
            buf.position(buf.position() + length - 4); // skip unknown template
        }
    }
}
```

### 9.4 Design Recommendations for netflow-java

Based on the research, the following design considerations are recommended:

1. **Multi-version support**: Support v5 (fixed) and v9 (template-based) at minimum; IPFIX as a stretch goal
2. **ByteBuffer-based parsing**: Leverage Java's `ByteBuffer` for zero-copy, big-endian parsing
3. **Template cache**: Implement a thread-safe template cache keyed by `(SourceID, TemplateID)` with configurable TTL
4. **Event-driven collector**: Use Java NIO (`DatagramChannel`) or Netty for high-performance UDP reception
5. **Pluggable handlers**: Allow users to register callbacks or listeners for received flow records
6. **Unsigned integer handling**: Java lacks unsigned types; use bitmask operations (`& 0xFFFF`, `& 0xFFFFFFFFL`) or `Integer.toUnsignedLong()`
7. **Sequence tracking**: Track sequence numbers per exporter to detect and report packet loss
8. **Modular field definitions**: Define field types as an enum or registry mapping type IDs to names and sizes

---

## 10. RFCs and Standards

| Document   | Title                                                    | Status        |
|------------|----------------------------------------------------------|---------------|
| **RFC 3954** | Cisco Systems NetFlow Services Export Version 9         | Informational |
| **RFC 7011** | Specification of the IPFIX Protocol (obsoletes RFC 5101)| Standards Track |
| **RFC 7012** | IPFIX Information Elements (obsoletes RFC 5102)         | Standards Track |
| **RFC 7013** | IPFIX Guidelines for Defining New Information Elements  | Standards Track |
| **RFC 7014** | IPFIX Per-SCTP-Stream and Template-Based Data Reduction | Standards Track |
| **RFC 7015** | IPFIX File Format                                       | Standards Track |
| **RFC 5103** | Bidirectional Flow Export Using IPFIX                    | Standards Track |
| **RFC 6313** | IPFIX Structured Data Information Elements              | Standards Track |

---

## 11. References

- [Cisco - NetFlow Export Datagram Format](https://www.cisco.com/c/en/us/td/docs/net_mgmt/netflow_collection_engine/3-6/user/guide/format.html)
- [Cisco - NetFlow Version 9 Flow-Record Format (White Paper)](https://www.cisco.com/en/US/technologies/tk648/tk362/technologies_white_paper09186a00800a3db9.html)
- [RFC 3954 - Cisco Systems NetFlow Services Export Version 9](https://datatracker.ietf.org/doc/html/rfc3954)
- [RFC 7011 - Specification of the IPFIX Protocol](https://datatracker.ietf.org/doc/html/rfc7011)
- [RFC 7012 - IPFIX Information Elements](https://datatracker.ietf.org/doc/html/rfc7012)
- [IANA - IPFIX Information Elements Registry](https://www.iana.org/assignments/ipfix/ipfix.xhtml)
- [Wikipedia - NetFlow](https://en.wikipedia.org/wiki/NetFlow)
- [Noction - The Evolution of Network Flow Monitoring](https://www.noction.com/blog/network-flow-monitoring)
- [Noction - NetFlow vs sFlow vs IPFIX vs NetStream](https://www.noction.com/blog/netflow-sflow-ipfix-netstream)
- [Kentik - What is NetFlow?](https://www.kentik.com/kentipedia/what-is-netflow-overview/)
- [Kentik - NetFlow vs sFlow](https://www.kentik.com/blog/netflow-vs-sflow/)
- [Varonis - Network Flow Monitoring Explained](https://www.varonis.com/blog/flow-monitoring)
- [Gigamon - IPFIX vs NetFlow](https://blog.gigamon.com/2019/09/17/ipfix-vs-netflow/)
- [ManageEngine - What is NetFlow](https://www.manageengine.com/products/netflow/what-is-netflow.html)
- [Progress - Introducing Flow Formats and Their Differences](https://www.progress.com/blogs/introducing-flow-formats-and-their-differences)
- [Plixer - NetFlow v9 Overview](https://www.plixer.com/blog/netflow-v9-overview-netflow-basics/)
- [IBM - NetFlow V5 Formats](https://www.ibm.com/docs/en/npi/1.3.0?topic=versions-netflow-v5-formats)
- [IBM - V9 Field Type Definitions](https://www.ibm.com/docs/en/npi/1.3.0?topic=versions-v9-field-type-definitions)
- [NetFlow Logic - V5 to V9 Field Types Mapping](https://docs.netflowlogic.com/nfo_user_guide/appendix-1/)
- [Graylog NetFlow Plugin (GitHub)](https://github.com/Graylog2/graylog-plugin-netflow)
- [LUMASERV netflow-java (GitHub)](https://github.com/LUMASERV/netflow-java)
- [JNCA - Java NetFlow Collect-Analyzer (SourceForge)](https://sourceforge.net/projects/jnca/)
- [SolarWinds - What is NetFlow](https://www.solarwinds.com/netflow-traffic-analyzer/use-cases/what-is-netflow)
- [CiscoPress - NetFlow for Cybersecurity](https://www.ciscopress.com/articles/article.asp?p=2812391&seqNum=5)

# Data Flow Diagrams (DFD)

This document contains Data Flow Diagrams (DFD) at Level 0, Level 1, and Level 2, outlining the flow of data between users, processes, and database stores in FoodConnect.

---

## 1. DFD Level 0 — Context Diagram
The Context Diagram represents the high-level boundary of the FoodConnect application, showing external entities and their primary interactions.

```mermaid
graph TD
    Donor([Food Donor])
    NGO([Recipient NGO])
    Admin([Platform Admin])
    
    System[("FoodConnect System
    (Django App)")]
    
    %% Donor flows
    Donor -->|1. Register / Login credentials| System
    Donor -->|2. Food Donation details| System
    System -->|3. Gamification impact rank & scores| Donor
    System -->|4. Pickup confirmation notifications| Donor

    %% NGO flows
    NGO -->|1. Register details & License document| System
    NGO -->|2. Claim request & pickup status| System
    NGO -->|3. Post-pickup quality feedback| System
    System -->|4. Real-time available food feed| NGO
    System -->|5. Donor contact info & geolocation coordinates| NGO

    %% Admin flows
    Admin -->|1. Admin credentials| System
    Admin -->|2. Approvals / Rejections / Ban requests| System
    System -->|3. Verification queue & user profiles| Admin
    System -->|4. Site metrics & donation history| Admin
```

---

## 2. DFD Level 1 — System Level Diagram
The Level 1 DFD decomposes the system into major functional processes and tracks the flow of data to and from our database stores.

```mermaid
graph TD
    %% External Entities
    Donor([Food Donor])
    NGO([Recipient NGO])
    Admin([Platform Admin])

    %% Processes
    P1["1.0 Auth & Profile Manager"]
    P2["2.0 Donation Posting & Geolocation"]
    P3["3.0 Feed & Claim Processor"]
    P4["4.0 Collection & Score Engine"]
    P5["5.0 Admin Control Queue"]
    P6["6.0 Real-time SSE Broker"]

    %% Data Stores
    D1[("D1: User Profiles (accounts_user)")]
    D2[("D2: Donations (donations_donation)")]
    D3[("D3: Feedback Logs (donations_qualityfeedback)")]

    %% P1 Flows
    Donor & NGO -->|Credentials & Profile info| P1
    P1 <-->|Read / Write credentials| D1
    
    %% P2 Flows
    Donor -->|Submit food items + Lat/Lng| P2
    P2 -->|Save Available donation| D2
    P2 -.->|Emit donation_posted signal| P6
    
    %% P3 Flows
    NGO -->|Browse active listings| P3
    P3 <-->|Read / Write status transitions| D2
    P3 -->|Query NGO status| D1
    P3 -.->|Emit donation_claimed signal| P6
    P3 -->|Reveal donor details| NGO
    
    %% P4 Flows
    NGO -->|Confirm pickup & submit audit| P4
    P4 -->|Write Collected status & timestamp| D2
    P4 -->|Increment impact score| D1
    P4 -->|Save quality feedback| D3
    P4 -.->|Emit donation_collected signal| P6
    
    %% P5 Flows
    Admin -->|Approve NGO / Ban user| P5
    P5 <-->|Verify NGO doc / Set is_banned| D1
    P5 -.->|Emit ngo_verified / user_banned signals| P6

    %% P6 Flows
    P6 -->|Push notifications / Feed updates| Donor & NGO
```

---

## 3. DFD Level 2 — Concurrency-Safe Claiming & Live Update Stream
The Level 2 DFD breaks down the claiming engine (Process 3.0) and the SSE broadcast pipeline (Process 6.0) to highlight the integration of transactional row-level database locks with the reactive push channel.

```mermaid
graph TD
    NGO([Recipient NGO])
    Donor([Food Donor])
    
    D1[("D1: User Profiles")]
    D2[("D2: Donations")]
    
    subgraph Claiming Engine
        P31["3.1 Validate Session & Verification"]
        P32["3.2 Claim Request (POST)"]
        P33["3.3 Lock Row & Verify Status
        (select_for_update)"]
        P34["3.4 Commit Status change
        (Set status='Claimed')"]
    end
    
    subgraph SSE Push Engine
        P61["6.1 Signal Handler intercept"]
        P62["6.2 SSE Queue Broker"]
        P63["6.3 Client Connection Stream"]
    end

    %% Claim Flow
    NGO -->|Claim click| P31
    P31 -->|Check verification / bans| D1
    P31 -->|Proceed| P32
    P32 -->|Fetch donation details| P33
    P33 <-->|Lock row in DB transaction| D2
    P33 -->|Status is Available?| P34
    P34 -->|Update status| D2
    
    %% Signal emission & Event Stream
    P34 -.->|Emit donation_claimed signal| P61
    P61 -->|Package JSON payload| P62
    P62 -->|Enqueue event| P63
    P63 -->|Stream: event: donation_claimed| NGO
    P63 -->|Stream: event: donation_claimed| Donor
```

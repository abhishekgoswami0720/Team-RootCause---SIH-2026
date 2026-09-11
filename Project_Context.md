# PROJECT_CONTEXT

> **Project Name:** MandiQ
> **Version:** 1.0
> **Purpose:** Provide complete project context for developers, designers, AI assistants, mentors, and future contributors before any implementation begins.

---

# 1. Project Vision

MandiQ aims to transform the agricultural procurement process by replacing uncertain physical queues with an intelligent, voice-first procurement management system.

Instead of farmers waiting for hours or days at procurement centers, MandiQ ensures they know **exactly when to arrive**, minimizing unnecessary waiting, reducing operational inefficiencies, and improving the overall procurement experience.

The project is designed as a Smart India Hackathon prototype demonstrating how AI-assisted voice interaction and intelligent queue management can modernize agricultural procurement.

---

# 2. Background

Agricultural procurement in many mandis still follows a largely manual process.

Farmers typically travel long distances with loaded produce, register themselves, and wait in physical queues without knowing when procurement will begin.

This creates operational inefficiencies for mandi officials while placing unnecessary financial and physical burdens on farmers.

Although digital procurement systems exist, most focus on registration and record management rather than intelligent queue scheduling or proactive farmer communication.

MandiQ addresses this operational gap.

---

# 3. Problem Statement

The current procurement process suffers from several critical challenges:

* Farmers travel before knowing when their turn will come.
* Long waiting periods increase fuel consumption and operational costs.
* Queue congestion causes delays for both farmers and procurement officials.
* Crop quality may deteriorate during prolonged waiting.
* Communication between farmers and procurement centers is largely manual.
* Existing systems do not dynamically adapt to delays or disruptions.

These issues reduce overall procurement efficiency and negatively impact farmer experience.

---

# 4. Existing Workflow

Current procurement process:

```text
Farmer

↓

Travels to Mandi

↓

Registration

↓

Waits in Queue

↓

Procurement

↓

Returns Home
```

The waiting period is unpredictable and often represents the largest source of inefficiency.

---

# 5. Our Solution

MandiQ introduces an AI-powered, multilingual, voice-first procurement management platform.

Instead of requiring smartphone applications, farmers interact using ordinary phone calls.

The platform:

* Books procurement slots
* Allocates tokens
* Predicts waiting times
* Continuously monitors queues
* Provides live operational visibility
* Handles disruptions through intelligent rescheduling

This significantly improves operational transparency for both farmers and mandi officials.

---

# 6. Project Goals

The primary objectives of MandiQ are:

* Reduce farmer waiting time
* Improve procurement transparency
* Support feature-phone users
* Provide multilingual voice interaction
* Optimize queue utilization
* Enable dynamic slot allocation
* Provide live operational monitoring
* Support intelligent exception handling

---

# 7. Non Goals

The prototype does **not** aim to provide:

* Online payments
* Farmer marketplace
* Crop trading platform
* Warehouse management
* Supply chain optimization
* Inventory management
* Financial services

These are considered future expansion opportunities and remain outside the current prototype scope.

---

# 8. Stakeholders

The system primarily serves the following stakeholders:

## Farmers

* Book procurement slots
* Receive token information
* Receive notifications
* Minimize waiting time

---

## Mandi Officials

* Monitor procurement operations
* Track queue progress
* Manage exceptions
* Handle procurement disruptions

---

## Procurement Staff

* Process arriving farmers
* Update procurement status
* Maintain queue flow

---

## Administrators

* Configure system settings
* Monitor overall operations
* Review analytics

---

# 9. End-to-End User Journey

```text
Farmer

↓

Calls MandiQ

↓

Voice Interaction

↓

Language Selection

↓

Slot Booking

↓

Token Generation

↓

SMS Confirmation

↓

Arrives at Mandi

↓

Procurement

↓

Completion
```

If procurement is interrupted, the system automatically enters the exception handling workflow.

---

# 10. System Overview

The project consists of several interconnected modules:

* Voice Processing
* Booking Engine
* Queue Engine
* Dashboard
* Exception Center
* Notification Service
* Analytics Module
* Database Layer

Each module operates independently while communicating through well-defined APIs.

---

# 11. Core Components

## Voice Agent

Handles farmer interaction using voice and keypad inputs.

---

## Booking Engine

Responsible for slot allocation and token generation.

---

## Queue Engine

Calculates queue position and estimated waiting time.

---

## Dashboard

Provides mandi officials with a live operational control center.

---

## Exception Center

Handles operational disruptions including:

* Farmer delays
* Medical emergencies
* Vehicle breakdowns
* Weather-related disruptions
* Queue delays
* Procurement halt events

---

## HALT Procurement

Allows operators to temporarily suspend procurement operations.

The system automatically:

* Stops queue progression
* Reschedules affected farmers
* Generates updated slots
* Sends notifications
* Updates dashboard information

---

# 12. Major Features

* Voice-based booking
* Feature phone compatibility
* Multilingual interaction
* Smart slot allocation
* Dynamic queue estimation
* Token generation
* Dashboard monitoring
* Exception management
* HALT procurement workflow
* SMS notifications
* Analytics

---

# 13. Business Rules

The following rules govern the prototype:

* One farmer may have only one active booking.
* Token numbers must remain unique.
* Slot capacity cannot exceed configured limits.
* Queue calculations are dynamic.
* Procurement status must update in real time.
* HALT operations automatically trigger rescheduling.
* Dashboard always reflects the latest operational state.

---

# 14. Design Principles

The system follows these guiding principles:

* Voice-first interaction
* Farmer simplicity over technical complexity
* Operational transparency
* Human-assisted decision making
* Modular architecture
* Scalable design
* Real-time visibility
* Graceful exception handling

---

# 15. Constraints

Current prototype constraints include:

* Built specifically for Smart India Hackathon
* Limited implementation timeline
* Prototype-level integrations
* Feature phone compatibility
* Internet availability assumed for dashboard
* Voice interactions simulated where necessary

---

# 16. Assumptions

The prototype assumes:

* Farmers possess a mobile phone.
* SMS delivery is available.
* Mandi officials have dashboard access.
* Procurement counters regularly update status.
* Database remains continuously available during operations.

---

# 17. Prototype Scope

The SIH prototype demonstrates:

* Voice-based booking
* Queue management
* Token generation
* Live dashboard
* Exception Center
* HALT Procurement
* Basic analytics
* Notification workflow

Advanced production features remain outside the current implementation.

---

# 18. Future Scope

Possible future enhancements include:

* Government procurement integration
* Weather-aware scheduling
* GPS-assisted arrival prediction
* AI-based procurement forecasting
* Multi-mandi deployment
* National scalability
* WhatsApp integration
* Advanced analytics

---

# 19. Success Metrics

The prototype will be evaluated using:

* Booking success rate
* Queue efficiency
* Average waiting time
* Slot utilization
* Dashboard responsiveness
* Exception handling efficiency
* Overall system usability

---

# 20. Glossary

| Term             | Description                                                 |
| ---------------- | ----------------------------------------------------------- |
| Farmer           | Person delivering produce for procurement                   |
| Mandi            | Agricultural procurement center                             |
| Slot             | Scheduled procurement time                                  |
| Token            | Queue identifier assigned after booking                     |
| Queue Engine     | Calculates waiting time and queue order                     |
| Dashboard        | Operational interface for mandi officials                   |
| Exception Center | Module for handling operational disruptions                 |
| HALT             | Emergency procurement suspension and rescheduling mechanism |

---

# Document Purpose

This document serves as the primary reference for understanding the business context, project objectives, system boundaries, and design philosophy of MandiQ.

Every technical document within this repository should align with the principles and scope defined here.

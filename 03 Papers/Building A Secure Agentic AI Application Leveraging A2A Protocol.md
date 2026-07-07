---
title: "Building A Secure Agentic AI Application Leveraging Google's A2A Protocol"
created: 2026-07-06
tags: [paper, agenten, infrastruktur, security]
---
# Building A Secure Agentic AI Application Leveraging Google's A2A Protocol

## Metadata
Autoren: Habler (Intuit), Huang (DistributedApps.ai), Narajala (AWS), Kulkarni (Google Cloud) · Jahr: 2025 (Mai) · Typ: arXiv-Preprint · Link: https://arxiv.org/abs/2504.16902 · Code: https://github.com/kenhuangus/a2a-secure-coding-examples

## Research Question
Welche Sicherheitsrisiken entstehen beim Aufbau von Multi-Agent-Systemen mit Googles Agent2Agent-Protokoll (A2A), und wie lassen sie sich systematisch absichern?

## Motivation
Kein reines Finance-Paper, sondern **Infrastruktur-Grundlage für das WU-Vorhaben "Multi-Agent-Environment"** (mehrere Mitarbeiter, je eigener Agent, gemeinsame Projekte). A2A ist neben MCP das zweite zentrale Protokoll für Agent-zu-Agent-Kommunikation (Koordination/Delegation) – Ergänzung zu MCP (Agent-zu-Tool/Daten).

## Data
Kein empirisches Datenset; konzeptionelle Sicherheitsanalyse + zwei Fallstudien (kollaborative Dokumentenbearbeitung, verteilte Datenanalyse).

## Methodology
Bedrohungsmodellierung mit dem **MAESTRO-Framework** (7-Schichten-Referenzarchitektur für Agentic AI: Foundation Models, Data Operations, Agent Frameworks, Deployment/Infra, Evaluation/Observability, Security/Compliance, Agent Ecosystem). Darauf aufbauend 10 konkrete A2A-Bedrohungen identifiziert und Gegenmaßnahmen abgeleitet.

## Main Findings
10 zentrale Bedrohungsklassen: Agent-Card-Spoofing, Task-Replay, Message-Schema-Verletzungen, Server-Impersonation, Cross-Agent-Task-Escalation, Artifact-Tampering, Insider-Threat/Logging-Evasion, Supply-Chain-Angriffe über Agent-Dependencies, Authentifizierungs-/Identitäts-Schwächen (JWT/OAuth), und **"Poisoned AgentCard"** – Prompt-Injection über die maschinenlesbare Agent-Beschreibung selbst, die ein anderer Agent automatisch verarbeitet. Für jede Bedrohung werden konkrete Mitigationen genannt (digitale Signaturen auf Agent Cards, mTLS, Nonces/Timestamps gegen Replay, strikte Schema-Validierung, RBAC + Audit-Logging, SBOM für Dependencies). A2A und MCP werden als **komplementär** positioniert: A2A für horizontale Agent-zu-Agent-Koordination, MCP für vertikale Agent-zu-Tool-Anbindung.

## Contributions
Erste systematische, framework-gestützte Sicherheitsanalyse von A2A-Deployments; praktische Best-Practice-Checkliste für sichere A2A-Server/-Clients; End-to-End-Beispielfluss, der A2A (Task-Delegation zwischen spezialisierten Agenten) und MCP (Tool-/Datenzugriff jedes einzelnen Agenten) im selben Workflow zeigt.

## Limitations
Kein Peer-Review; rein konzeptionell/deskriptiv, keine quantitative Evaluation der Angriffe oder Gegenmaßnahmen; Autoren mit Interessenbindung an beteiligten Unternehmen (Intuit, AWS, Google Cloud) – explizit als "nicht Positionsmeinung des Arbeitgebers" gekennzeichnet; A2A selbst ist ein junges, sich noch entwickelndes Protokoll.

## Research Opportunities
Direkt relevant für die Sicherheits-/Governance-Schicht des [[Multi-Agent-Research-Environment]]-Vorhabens, sobald dort Agent-zu-Agent-Delegation (nicht nur Agent-zu-Repo/MLflow) eingeführt wird – insbesondere bei sensiblen Insolvenz-/Firmendaten ist "Poisoned AgentCard" und Supply-Chain-Absicherung relevant, bevor Agenten sich gegenseitig Teilaufgaben delegieren.

## Related Concepts
–

## Related Papers
–

## Related Projects
[[Multi-Agent-Research-Environment]]

## Related Methods
–

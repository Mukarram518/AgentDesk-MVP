\# AgentDesk MVP — AI Coding Agent Instructions



\## 1. Project Purpose



This repository contains the time-boxed MVP of \*\*AgentDesk\*\*, a multi-agent AI platform for small businesses.



The MVP is being developed for the \*\*AI Engineer Associate application\*\*.



The MVP must demonstrate the core product idea through a working end-to-end flow.



This is NOT the complete university FYP implementation.



The full FYP exists in a separate repository:



```text

AgentDesk-FYP

```



The MVP should remain architecturally compatible with the FYP so that useful concepts can later be reused.



\---



\## 2. MVP Goal



The MVP must demonstrate:



1\. Business information / knowledge

2\. Knowledge retrieval / RAG

3\. AI customer chat

4\. Lead detection and capture

5\. Lead scoring

6\. Basic appointment intent / booking flow

7\. Simple business-owner dashboard



The core demonstration flow is:



```text

Customer

&#x20;  ↓

Web Chat

&#x20;  ↓

AI Agent

&#x20;  ↓

Business Knowledge / RAG

&#x20;  ↓

Helpful Response

&#x20;  ↓

Lead Detection

&#x20;  ↓

Lead Capture

&#x20;  ↓

Lead Dashboard

```



Appointment capability should be implemented if it can be completed without putting the core flow at risk.



\---



\## 3. MVP Technology



Use:



\### Frontend



\* Next.js

\* TypeScript

\* Tailwind CSS



\### Backend



\* Python

\* FastAPI

\* Pydantic



\### Database



\* PostgreSQL

\* pgvector



\### AI



\* Provider abstraction

\* LLM provider

\* Embeddings provider

\* RAG retrieval



\### Deployment



Use a simple deployment strategy suitable for a working demo.



Do not over-engineer deployment.



\---



\## 4. Architecture



Use this basic architecture:



```text

Next.js Frontend

&#x20;      ↓

FastAPI Backend

&#x20;      ↓

Application Services

&#x20;      ↓

PostgreSQL + pgvector

&#x20;      ↓

AI/RAG Layer

&#x20;      ↓

LLM Provider

```



The AI agent must not directly access the database.



Use backend-controlled operations.



\---



\## 5. MVP Features



\### Business



Use one demo business initially.



The business should contain:



\* Business name

\* Description

\* Services

\* Prices

\* Opening hours

\* Contact information

\* FAQs



The MVP may use seeded demo business data.



Do not build full multi-business onboarding unless necessary.



\---



\### Knowledge Base



Support business knowledge through:



\* FAQ entries

\* Text/business information

\* Optional PDF upload if time permits



Knowledge should be retrievable through semantic search.



Use pgvector for vector retrieval.



Do not fake RAG by simply hardcoding chatbot responses.



\---



\### AI Chat



Create a customer-facing web chat.



The customer should be able to ask questions such as:



```text

What services do you provide?



How much does teeth whitening cost?



Are you open on Sunday?



I want to book an appointment.

```



The AI should use the business knowledge to answer.



Unknown information should not be invented.



\---



\### Lead Agent



The system should identify buying intent.



Collect when available:



\* Name

\* Contact information

\* Customer need

\* Conversation



Assign:



```text

HOT

WARM

COLD

```



based on simple documented rules.



The scoring logic must be deterministic where possible.



\---



\### Dashboard



Provide a simple owner dashboard showing:



\* Recent conversations

\* Leads

\* Lead score

\* Customer need

\* Basic appointment information



The dashboard should prioritize demonstration value over visual complexity.



\---



\### Appointment



If implemented in the MVP:



Support a simple flow such as:



```text

Customer:

I want an appointment tomorrow at 3 PM.



Agent:

Collect required information.



Backend:

Validate requested time.



System:

Create appointment.



Dashboard:

Show appointment.

```



A local/mock calendar implementation is acceptable for the MVP if real Google Calendar integration would risk the deadline.



Do NOT pretend a mock calendar is a real Google Calendar integration.



\---



\## 6. MVP Scope



Prioritize:



```text

1\. Working web chat

2\. Real RAG retrieval

3\. AI response

4\. Lead capture

5\. Lead scoring

6\. Dashboard

7\. Appointment flow

```



Do not spend MVP time implementing:



\* WhatsApp

\* Voice

\* Deepgram

\* ElevenLabs

\* Real telephony

\* Google OAuth

\* Advanced analytics

\* Billing

\* Native mobile application

\* Complex role management

\* Production-scale infrastructure



\---



\## 7. AI Rules



The AI must:



\* Use business context

\* Use retrieved knowledge

\* Avoid inventing business information

\* Detect lead intent

\* Extract structured lead information

\* Use controlled backend operations

\* Keep customer information within the current demo business



Do not allow arbitrary code execution.



Do not allow the LLM to execute raw SQL.



\---



\## 8. Security



Even though this is an MVP:



\* Never commit API keys.

\* Never commit `.env`.

\* Use `.env.example`.

\* Validate backend input.

\* Do not expose private API keys in Next.js client code.

\* Keep AI provider keys server-side.

\* Do not expose database credentials to the frontend.



\---



\## 9. Development Rules



This is a time-boxed MVP.



Prefer:



```text

Simple

Reliable

Demonstrable

```



over:



```text

Complex

Over-engineered

Incomplete

```



Do not add unnecessary frameworks.



Do not create unnecessary abstractions.



Do not spend time implementing FYP-only features.



\---



\## 10. FYP Compatibility



The MVP must remain conceptually compatible with the full AgentDesk FYP.



Important concepts should remain consistent:



\* FastAPI backend

\* Next.js frontend

\* PostgreSQL

\* pgvector

\* RAG

\* AI orchestrator concept

\* Agent/tool separation

\* Business knowledge

\* Lead capture

\* Appointment capability



However, MVP simplifications are allowed because this repository is a prototype.



Do not modify the FYP repository from this repository.



\---



\## 11. Git Rules



Make small logical commits.



Examples:



```text

chore: initialize MVP project

feat: add backend foundation

feat: add business knowledge

feat: add RAG retrieval

feat: add AI chat

feat: add lead capture

feat: add owner dashboard

feat: add appointment flow

```



Do not automatically push unless explicitly instructed.



\---



\## 12. Priority Rule



If time becomes limited, protect this flow:



```text

Customer

&#x20;  ↓

Chat

&#x20;  ↓

AI

&#x20;  ↓

RAG

&#x20;  ↓

Answer

&#x20;  ↓

Lead Capture

&#x20;  ↓

Dashboard

```



A smaller working MVP is better than a large incomplete system.



\---



\## 13. Human Approval



The human developer remains the final decision-maker.



Do not:



\* Redesign the product

\* Replace the technology stack

\* Add major dependencies

\* Delete working features

\* Commit secrets

\* Modify the separate FYP repository

\* Expand the scope without approval



If a major architectural decision is required, stop and ask.




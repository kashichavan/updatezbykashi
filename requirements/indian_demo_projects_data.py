"""
Curated Library of Realistic, Fictional Demonstration Projects based on Indian IT Industry Use Cases.
Covers major Indian technology hubs (Bengaluru, Hyderabad, Pune, Mumbai, Chennai, Gurugram, Noida, Ahmedabad, Kochi, etc.)
across 6 core job families:
1. Python / Django Developer (8 projects)
2. Java / Spring Boot Developer (6 projects)
3. React / Full-Stack Developer (6 projects)
4. DevOps / Cloud Engineer (6 projects)
5. Data Engineer / PySpark / Databricks (6 projects)
6. QA / Automation Engineer (4 projects)
Total: 36 Projects with complete Google XYZ bullet templates and architectural breakdowns.
"""

INDIAN_DEMO_PROJECTS = [
    # =========================================================================
    # 1. PYTHON / DJANGO DEVELOPER (8 PROJECTS)
    # =========================================================================
    {
        "slug": "in-py-employee-payroll-bengaluru",
        "title": "Employee Management and Payroll System",
        "fictional_company_name": "Koramangala TechOps Labs (Fictional)",
        "location_city": "Bengaluru",
        "location_state": "Karnataka",
        "industry": "Human Resources & Payroll Tech",
        "target_job_roles": ["Python / Django Developer", "Backend Engineer", "Full Stack Python"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Enterprise-grade employee self-service and multi-tier payroll engine automating Indian statutory deductions (PF, ESI, Professional Tax, TDS) with monthly automated payslip dispatch.",
        "problem_statement": "Manual Excel-based payroll across distributed engineering teams caused calculation errors in statutory deductions and delayed salary disbursement notifications.",
        "technical_stack": ["Python", "Django", "Django REST Framework", "PostgreSQL", "Celery", "Redis", "Docker"],
        "key_features": [
            "Configurable statutory tax deduction engines (Provident Fund, ESI, Professional Tax, TDS Section 192).",
            "Asynchronous Celery batch dispatch generating password-protected PDF payslips for 1,000+ employees in under 4 minutes.",
            "Role-Based Access Control (RBAC) separating HR Admins, Department Leads, and Staff.",
            "Biometric attendance CSV reconciliation and leave accrual ledger."
        ],
        "architecture_summary": "Modular Django monolith structured into authentication, payroll, attendance, and reporting apps, backed by PostgreSQL and asynchronous Celery worker pools with Redis message queues.",
        "database_design_summary": "Normalized relational schema with Employee, SalaryStructure, PayrollRun, DeductionsLedger, and AttendanceLog tables with composite indexes on (employee_id, payroll_month).",
        "api_design_summary": "RESTful endpoints with JWT authentication: /api/v1/payroll/compute/, /api/v1/employees/{id}/payslips/, /api/v1/attendance/reconcile/.",
        "resume_bullet_templates": [
            "Architected automated payroll computation engine using Python, Django, and PostgreSQL, processing 1,000+ monthly salary structures compliant with Indian PF, ESI, and TDS regulations.",
            "Optimized monthly payslip generation by offloading PDF compilation to asynchronous Celery worker pools, cutting batch processing time from 45 mins to 3.8 mins.",
            "Integrated role-based access control (RBAC) and audit-logged salary adjustments, ensuring zero unauthorized payroll revisions across multi-department operations."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Statutory payroll calculation algorithms", "Asynchronous Celery PDF generation", "Database transactions and locking in Django"]
    },
    {
        "slug": "in-py-hospital-appointment-hyderabad",
        "title": "Hospital Appointment and Patient Management Platform",
        "fictional_company_name": "AarogyaCare HealthTech (Fictional)",
        "location_city": "Hyderabad",
        "location_state": "Telangana",
        "industry": "Healthcare & Telemedicine",
        "target_job_roles": ["Python / Django Developer", "Backend Engineer", "API Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Multi-specialty outpatient appointment scheduling, doctor availability calendar, and encrypted electronic health records (EHR) management system with SMS/WhatsApp alerts.",
        "problem_statement": "Overcrowded hospital OPD counters in urban centers experienced double-booking and average patient waiting times exceeding 75 minutes.",
        "technical_stack": ["Python", "Django REST Framework", "PostgreSQL", "Redis", "Twilio / Gupshup API", "Docker"],
        "key_features": [
            "Doctor slot allocation engine with atomic concurrency locking preventing double-booking during peak morning hours.",
            "Encrypted diagnostic lab report upload with pre-signed secure S3 URLs and QR-code patient verification.",
            "Automated appointment reminder dispatch via SMS and WhatsApp webhooks reducing no-show rates.",
            "Doctor dashboard displaying live OPD queue status and historical electronic prescription timeline."
        ],
        "architecture_summary": "RESTful backend exposing patient and physician portals, utilizing Redis caching for real-time doctor availability calendars and PostgreSQL with Row-Level Security for patient privacy.",
        "database_design_summary": "Doctor, Patient, Specialization, TimeSlot, Appointment, Prescription, and DiagnosticReport tables with database constraints enforcing non-overlapping slot bookings.",
        "api_design_summary": "Secure REST APIs: /api/v1/doctors/{id}/slots/, /api/v1/appointments/book/, /api/v1/patients/records/ with rate limiting at 60 req/min.",
        "resume_bullet_templates": [
            "Engineered outpatient scheduling backend using Django REST Framework and PostgreSQL, handling 500+ daily appointment bookings across 12 clinical specialties.",
            "Eliminated slot collision and double-booking by enforcing database-level atomic transactions and Redis-backed slot reservation locks.",
            "Developed automated SMS and WhatsApp notification pipeline via Celery tasks, reducing patient appointment no-show rates by 34%."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Concurrency control and atomic transactions", "Healthcare data security standards", "Third-party messaging webhook integrations"]
    },
    {
        "slug": "in-py-ecommerce-inventory-mumbai",
        "title": "E-commerce Order and Inventory Management System",
        "fictional_company_name": "MahaCommerce Retail Solutions (Fictional)",
        "location_city": "Mumbai",
        "location_state": "Maharashtra",
        "industry": "Retail & E-Commerce Logistics",
        "target_job_roles": ["Python / Django Developer", "Backend Systems Engineer"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "Multi-warehouse inventory synchronization, order fulfillment routing, and automated stock reorder trigger platform handling rapid flash-sale order spikes.",
        "problem_statement": "Fast-growing omnichannel retailers faced inventory discrepancy across warehouses and overselling during high-velocity festive sales events.",
        "technical_stack": ["Python", "Django", "PostgreSQL", "Redis", "Celery", "Stripe / Razorpay Sandbox"],
        "key_features": [
            "Distributed stock decrement engine with Redis distributed locking preventing overselling under concurrent checkouts.",
            "Intelligent order allocation assigning shipments to the nearest fulfillment hub based on pin-code geo-distance.",
            "Automated low-stock threshold alerting and purchase order PDF drafting for supplier procurement.",
            "Webhook ingestion pipeline reconciling payment gateway success callbacks with idempotent database transactions."
        ],
        "architecture_summary": "Event-driven Django application integrating asynchronous order state machines, Redis caching for fast stock checks, and PostgreSQL relational storage for order books.",
        "database_design_summary": "Warehouse, ProductSKU, StockLedger, CustomerOrder, OrderItem, and ShipmentTracking models with optimistic locking on inventory balances.",
        "api_design_summary": "High-throughput APIs: /api/v1/orders/checkout/, /api/v1/inventory/sync/, /api/v1/webhooks/payment/ with idempotency keys.",
        "resume_bullet_templates": [
            "Developed multi-warehouse inventory management API using Django and PostgreSQL, managing 10,000+ SKUs across 4 regional distribution centers.",
            "Prevented overselling during simulated flash-sale traffic (1,200 concurrent checkouts) using Redis distributed locking and database row-level locking.",
            "Architected idempotent payment webhook consumer processing transaction status updates, eliminating duplicate order fulfillment records."
        ],
        "estimated_duration": "4 weeks",
        "learning_outcomes": ["High-concurrency inventory reservation", "Idempotency design patterns", "Warehouse fulfillment routing algorithms"]
    },
    {
        "slug": "in-py-placement-recruitment-pune",
        "title": "College Placement and Recruitment Portal",
        "fictional_company_name": "CampusHire Pune Tech (Fictional)",
        "location_city": "Pune",
        "location_state": "Maharashtra",
        "industry": "EdTech & University Recruitment",
        "target_job_roles": ["Python / Django Developer", "Full Stack Developer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Campus recruitment automation platform managing student eligibility filtration, company drive schedules, resume verification, and round-by-round interview result publishing.",
        "problem_statement": "Engineering college training and placement offices spent hundreds of hours filtering candidate eligibility across CGPA, active backlogs, and branch criteria using spreadsheets.",
        "technical_stack": ["Python", "Django", "PostgreSQL", "Bootstrap 5", "Chart.js", "ReportLab"],
        "key_features": [
            "Dynamic eligibility filtration engine matching student profiles against company hiring cutoffs (CGPA, 10th/12th %, maximum backlogs).",
            "One-click verified student resume bundle exporter generating uniform PDF packages for visiting HR teams.",
            "Live multi-round interview tracking dashboard (Online Assessment, Technical, HR) with automated shortlisting notifications.",
            "Interactive placement analytics displaying branch-wise hiring percentages and compensation package percentiles."
        ],
        "architecture_summary": "Django MVC web application featuring student, placement coordinator, and corporate recruiter portals with CSV import/export engines and Chart.js analytics.",
        "database_design_summary": "StudentProfile, AcademicRecord, PlacementDrive, EligibilityCriteria, JobApplication, and DriveRound models with foreign key constraints and audit timestamps.",
        "api_design_summary": "Clean RESTful endpoints: /api/drives/{id}/eligible-candidates/, /api/applications/{id}/promote-round/, /api/analytics/summary/.",
        "resume_bullet_templates": [
            "Built end-to-end campus recruitment management portal using Django and PostgreSQL, supporting 2,500+ student profiles and 60+ corporate recruitment drives.",
            "Automated student candidate eligibility evaluation across academic cutoffs and branch constraints, reducing manual HR screening overhead by 85%.",
            "Implemented batch PDF resume export and placement statistical dashboard using Chart.js, delivering real-time hiring metrics to university administration."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Complex relational filtering with Django ORM", "Batch document generation", "Role-based authorization and workflows"]
    },
    {
        "slug": "in-py-gst-invoice-dashboard-ahmedabad",
        "title": "GST Invoice and Business Reporting Dashboard",
        "fictional_company_name": "VyaaparLedger Labs (Fictional)",
        "location_city": "Ahmedabad",
        "location_state": "Gujarat",
        "industry": "FinTech & SME Accounting",
        "target_job_roles": ["Python / Django Developer", "Backend Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "GST-compliant electronic invoicing, HSN/SAC tax breakdown, vendor accounts receivable ledger, and GSTR-1/GSTR-3B summary export dashboard for Indian MSMEs.",
        "problem_statement": "Small and medium manufacturing enterprises in Gujarat struggled with manual GST tax rate calculations, resulting in filing mismatches and delayed input tax credit reconciliation.",
        "technical_stack": ["Python", "Django", "Django REST Framework", "PostgreSQL", "Pandas", "WeasyPrint"],
        "key_features": [
            "Automated dual-tax engine calculating CGST, SGST for intra-state and IGST for inter-state transactions based on recipient state codes.",
            "HSN/SAC code search directory with automatic slab tax rate lookup (0%, 5%, 12%, 18%, 28%).",
            "PDF tax invoice generator with digital signature placeholder and QR-code verification string.",
            "Monthly GSTR-1 export compiling B2B and B2C sales registers into government-compliant JSON and Excel formats."
        ],
        "architecture_summary": "Django backend with decoupled calculation services for tax apportionment, Pandas-driven reporting aggregations, and HTML-to-PDF invoice rendering via WeasyPrint.",
        "database_design_summary": "CompanyProfile, CustomerAccount, ProductItem, InvoiceHeader, InvoiceLineItem, and GSTSummary tables with decimal precision fields preventing rounding discrepancies.",
        "api_design_summary": "Financial APIs: /api/invoices/generate/, /api/reports/gstr1-summary/, /api/customers/{id}/ledger/ with strict decimal validation.",
        "resume_bullet_templates": [
            "Developed GST electronic invoicing and financial ledger system using Python, Django, and PostgreSQL, handling B2B/B2C billing with intra/inter-state tax splits.",
            "Created automated GSTR-1 and GSTR-3B tax export engine using Pandas, generating reconciliation datasets compliant with Indian GST portal specifications.",
            "Designed high-precision financial calculation service maintaining zero rounding discrepancy across 50,000+ line items using Python Decimal types."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Indian GST taxation calculation algorithms", "High-precision financial data modeling", "Pandas reporting pipelines in Django"]
    },
    {
        "slug": "in-py-travel-tour-kochi",
        "title": "Travel Booking and Tour Management Platform",
        "fictional_company_name": "KeralaVoyage Systems (Fictional)",
        "location_city": "Kochi",
        "location_state": "Kerala",
        "industry": "Travel & Hospitality Tech",
        "target_job_roles": ["Python / Django Developer", "Full Stack Developer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Dynamic holiday itinerary builder, houseboat/hotel inventory reservation system, and customized package booking platform with Razorpay sandbox integration.",
        "problem_statement": "Regional tour operators relied on fragmented WhatsApp and phone booking channels, causing double-booked houseboats and unconfirmed customer itineraries during peak seasons.",
        "technical_stack": ["Python", "Django", "PostgreSQL", "Redis", "Razorpay Sandbox", "Leaflet.js"],
        "key_features": [
            "Interactive holiday package customizer calculating dynamic per-person pricing based on seasonality, hotel tier, and group size.",
            "Calendar-based houseboat and resort room inventory allocation engine with holding timers during checkout.",
            "Integrated payment gateway sandbox supporting UPI, NetBanking, and credit card payments with automated booking voucher generation.",
            "Interactive tour map rendering route coordinates and daily destination highlights using Leaflet.js."
        ],
        "architecture_summary": "Django application utilizing Redis for temporary inventory reservation locks during customer checkout sessions, backed by PostgreSQL relational storage and Leaflet mapping.",
        "database_design_summary": "Destination, PackageTour, DayItinerary, HotelInventory, BookingReservation, and CustomerReview models with foreign key integrity and reservation expiration timers.",
        "api_design_summary": "Consumer and admin APIs: /api/tours/search/, /api/bookings/reserve/, /api/payments/verify/.",
        "resume_bullet_templates": [
            "Engineered travel tour booking and itinerary management portal using Django and PostgreSQL, supporting dynamic package customization and inventory reservation.",
            "Implemented 15-minute checkout reservation hold mechanism using Redis cache keys, preventing duplicate houseboat bookings during high-demand seasons.",
            "Integrated Razorpay payment gateway sandbox with automated booking confirmation dispatch and PDF travel itinerary compilation."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Session holding and reservation timers", "Dynamic package pricing logic", "Third-party payment gateway integration"]
    },
    {
        "slug": "in-py-chat-notification-chennai",
        "title": "Real-Time Chat and Notification Platform",
        "fictional_company_name": "DravidaConnect Telemetry (Fictional)",
        "location_city": "Chennai",
        "location_state": "Tamil Nadu",
        "industry": "Collaborative SaaS & Real-Time Comms",
        "target_job_roles": ["Python / Django Developer", "Backend Systems Engineer"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "High-concurrency real-time group messaging and event notification backend utilizing Django Channels, WebSockets, and Redis channel layers for team collaboration.",
        "problem_statement": "Distributed engineering teams experienced 4-8 second delivery delays and missing unread counters when using traditional HTTP polling for messaging.",
        "technical_stack": ["Python", "Django Channels", "ASGI", "WebSockets", "Redis Channel Layer", "PostgreSQL"],
        "key_features": [
            "Bi-directional WebSocket communication handling group chat rooms, direct messaging, and typing presence indicators.",
            "Redis pub/sub channel layer ensuring sub-40ms message broadcast latency across concurrent user sessions.",
            "Unread message counter tracking and push notification delivery triggers when recipients are offline.",
            "Attachment handling with virus scan validation and thumbnail generation for shared code snippets and images."
        ],
        "architecture_summary": "Asynchronous ASGI architecture using Daphne, Django Channels, and Redis channel layer for real-time pub/sub, persisting conversation history asynchronously to PostgreSQL.",
        "database_design_summary": "UserPresence, ChatRoom, RoomParticipant, ChatMessage, MessageReceipt, and Notification models with indexed timestamp ordering.",
        "api_design_summary": "WebSocket routing at ws://domain/ws/chat/{room_name}/ paired with REST endpoints for historical message pagination: /api/rooms/{id}/messages/?cursor=xxx.",
        "resume_bullet_templates": [
            "Architected real-time WebSocket messaging backend using Django Channels, ASGI, and Redis channel layers, supporting 1,500+ concurrent active socket connections.",
            "Reduced message broadcast latency to sub-35ms by implementing Redis Pub/Sub distribution and asynchronous database writes.",
            "Designed cursor-based message pagination and offline notification queue, ensuring zero message loss during intermittent mobile connectivity."
        ],
        "estimated_duration": "4 weeks",
        "learning_outcomes": ["Asynchronous Python and ASGI with Django Channels", "WebSocket protocol lifecycle management", "Cursor-based pagination for high-volume datasets"]
    },
    {
        "slug": "in-py-saas-subscription-gurugram",
        "title": "SaaS Subscription and Billing Platform",
        "fictional_company_name": "CyberHub SaaS Engine (Fictional)",
        "location_city": "Gurugram",
        "location_state": "Haryana",
        "industry": "B2B SaaS & Recurring Billing",
        "target_job_roles": ["Python / Django Developer", "Backend Engineer", "API Engineer"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "Multi-tenant B2B subscription billing system supporting usage-based metering, tiered feature entitlements, automated recurring renewals, and tax invoices.",
        "problem_statement": "Enterprise B2B startups struggled with revenue leakage due to unmetered API overages and manual invoice follow-ups across monthly and annual enterprise clients.",
        "technical_stack": ["Python", "Django", "Django REST Framework", "PostgreSQL", "Stripe / LemonSqueezy Webhooks", "Docker"],
        "key_features": [
            "Multi-tenant data isolation with schema/tenant-aware middleware ensuring complete customer data segregation.",
            "Usage-based API metering pipeline aggregating monthly requests and calculating tiered overage charges.",
            "Automated subscription lifecycle management (Trial, Active, Past Due, Canceled, Suspended) with dunning email triggers.",
            "Idempotent webhook listener handling subscription renewals, failed charge retries, and prorated plan upgrades."
        ],
        "architecture_summary": "Multi-tenant Django REST API with middleware-driven tenant context, background Celery tasks for periodic billing runs, and normalized PostgreSQL ledger tables.",
        "database_design_summary": "TenantOrganization, SubscriptionPlan, Subscription, UsageMeter, Invoice, and PaymentTransaction models with tenant_id foreign keys and strict database constraints.",
        "api_design_summary": "Tenant APIs: /api/v1/subscriptions/subscribe/, /api/v1/metering/ingest/, /api/v1/invoices/ with API-key and JWT authentication.",
        "resume_bullet_templates": [
            "Engineered multi-tenant subscription management engine using Django REST Framework and PostgreSQL, automating tiered billing and plan upgrades.",
            "Implemented usage-based API metering service aggregating 500,000+ monthly requests and calculating precise overage surcharges.",
            "Designed resilient webhook ingestion pipeline with exponential backoff retries, ensuring 100% billing reconciliation accuracy across payment gateways."
        ],
        "estimated_duration": "4 weeks",
        "learning_outcomes": ["Multi-tenant application architecture", "Subscription lifecycle and dunning state machines", "Usage metering and aggregation algorithms"]
    },

    # =========================================================================
    # 2. JAVA / SPRING BOOT DEVELOPER (6 PROJECTS)
    # =========================================================================
    {
        "slug": "in-java-digital-banking-mumbai",
        "title": "Digital Banking Transaction Management System",
        "fictional_company_name": "Nariman FinServices Labs (Fictional)",
        "location_city": "Mumbai",
        "location_state": "Maharashtra",
        "industry": "Banking & Financial Services",
        "target_job_roles": ["Java / Spring Boot Developer", "Backend Engineer", "Java Microservices Developer"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "Enterprise core banking transaction engine featuring double-entry accounting ledger, concurrent fund transfers, fraud detection rules, and NEFT/RTGS/IMPS simulators.",
        "problem_statement": "Legacy core banking modules suffered from thread contention during concurrent fund transfers, leading to balance inconsistency and slow audit reconciliation.",
        "technical_stack": ["Java 17", "Spring Boot", "Spring Data JPA", "PostgreSQL", "Redis", "Kafka", "Docker"],
        "key_features": [
            "Double-entry bookkeeping ledger ensuring total debits equal total credits for every transaction with ACID compliance.",
            "Optimistic and pessimistic database locking strategies preventing race conditions during concurrent account balance debits.",
            "Event-driven audit logging via Apache Kafka streaming financial events to an immutable compliance ledger.",
            "Rule-based transaction anomaly detector flagging rapid velocity withdrawals and transfers above threshold limits."
        ],
        "architecture_summary": "Layered Spring Boot microservice implementing Clean Architecture (Controller, Service, Domain, Repository) with Kafka event streaming and Redis caching for balance inquiries.",
        "database_design_summary": "Account, TransactionLedger, JournalEntry, AccountBalance, and FraudRule tables with pessimistic write locks on AccountBalance during fund transfers.",
        "api_design_summary": "Idempotent Banking REST APIs: POST /api/v1/transfers/internal, POST /api/v1/transfers/imps, GET /api/v1/accounts/{accountNumber}/statement.",
        "resume_bullet_templates": [
            "Architected double-entry core banking ledger service using Java 17, Spring Boot, and PostgreSQL, maintaining 100% mathematical balance integrity across simulated accounts.",
            "Prevented concurrent transfer race conditions and negative balance anomalies by implementing JPA pessimistic locking and Redis idempotency tokens.",
            "Streamed high-frequency transaction event records to an immutable compliance ledger using Apache Kafka, achieving sub-20ms event publication latency."
        ],
        "estimated_duration": "4 weeks",
        "learning_outcomes": ["Double-entry accounting ledger design", "Concurrency locking in JPA/Hibernate", "Apache Kafka event-driven architecture"]
    },
    {
        "slug": "in-java-microservices-ecommerce-bengaluru",
        "title": "Microservices-Based E-commerce Platform",
        "fictional_company_name": "Whitefield Commerce Cloud (Fictional)",
        "location_city": "Bengaluru",
        "location_state": "Karnataka",
        "industry": "E-Commerce & Distributed Systems",
        "target_job_roles": ["Java / Spring Boot Developer", "Backend Architect", "Microservices Engineer"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "Decomposed cloud-native e-commerce architecture comprising Product Catalog, Order Processing, Payment, and Notification microservices coordinated via Spring Cloud.",
        "problem_statement": "Monolithic retail systems experienced complete downtime during product catalog crashes and suffered cascading failures during festive sale traffic surges.",
        "technical_stack": ["Java 17", "Spring Boot", "Spring Cloud Gateway", "Eureka Service Discovery", "Resilience4j", "PostgreSQL", "Docker"],
        "key_features": [
            "API Gateway routing with JWT authentication, rate limiting, and dynamic path-based service dispatching.",
            "Fault tolerance and cascading failure prevention using Resilience4j Circuit Breakers, Retries, and Fallbacks.",
            "Distributed transaction management implementing the Saga pattern with asynchronous choreographies across Order and Inventory services.",
            "Centralized configuration management and dynamic property refresh using Spring Cloud Config."
        ],
        "architecture_summary": "Microservices mesh with Eureka Discovery, Spring Cloud Gateway, Resilience4j circuit breakers, decoupled PostgreSQL databases per service, and Docker Compose orchestration.",
        "database_design_summary": "Database-per-service pattern: CatalogDB (Products, Categories), OrderDB (Orders, OrderItems), and PaymentDB (Transactions, Refunds) ensuring loose coupling.",
        "api_design_summary": "Gateway APIs: /api/v1/catalog/**, /api/v1/orders/**, /api/v1/payments/** with standardized HTTP response envelopes and correlation IDs.",
        "resume_bullet_templates": [
            "Engineered distributed e-commerce microservices ecosystem using Spring Boot, Spring Cloud Gateway, and Eureka Discovery across 4 decoupled business domains.",
            "Implemented Resilience4j circuit breaker and rate-limiting patterns, preventing cascading service outages and maintaining 99.95% system uptime under simulated load.",
            "Coordinated distributed multi-service checkout workflows via the Saga pattern, ensuring inventory rollback consistency upon payment authorization failures."
        ],
        "estimated_duration": "4-5 weeks",
        "learning_outcomes": ["Microservices service mesh with Spring Cloud", "Resilience4j circuit breaker implementation", "Distributed Saga pattern and database-per-service"]
    },
    {
        "slug": "in-java-insurance-claims-hyderabad",
        "title": "Insurance Claims Processing System",
        "fictional_company_name": "HITEC InsureTech Systems (Fictional)",
        "location_city": "Hyderabad",
        "location_state": "Telangana",
        "industry": "FinTech & Insurance",
        "target_job_roles": ["Java / Spring Boot Developer", "Backend Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Health and motor insurance claims adjudication workflow platform automating document validation, surveyor review assignment, policy deductible deduction, and settlement payout.",
        "problem_statement": "Health insurance third-party administrators (TPAs) required 14-21 days to manually review and settle cashless hospital claims due to paper-heavy workflows.",
        "technical_stack": ["Java 17", "Spring Boot", "Spring Security", "PostgreSQL", "Hibernate", "AWS S3 / MinIO", "Docker"],
        "key_features": [
            "Multi-stage claim adjudication workflow engine (Intimation, Document Verification, Medical Audit, Surveyor Assessment, Settlement Approval).",
            "Automated policy coverage validator verifying active policy tenure, pre-existing condition exclusions, and deductible limits.",
            "Encrypted diagnostic bill and discharge summary document repository with SHA-256 integrity hashing.",
            "Audit trail logging tracking state transitions, timestamps, reviewer comments, and claim settlement amounts."
        ],
        "architecture_summary": "Spring Boot application implementing state machine workflows, Hibernate ORM with second-level cache, Spring Security with JWT tokens, and S3-compatible document storage.",
        "database_design_summary": "InsurancePolicy, PolicyHolder, ClaimRegistration, ClaimDocument, ClaimAuditLog, and SettlementPayout tables with foreign key indexing.",
        "api_design_summary": "Adjudication APIs: /api/claims/register, /api/claims/{id}/adjudicate, /api/claims/{id}/settlement-payout with role-based method security (@PreAuthorize).",
        "resume_bullet_templates": [
            "Developed insurance claims adjudication platform using Java 17, Spring Boot, and PostgreSQL, automating multi-stage medical claim validation workflows.",
            "Implemented state machine tracking claim transitions across 6 adjudication milestones, cutting simulated claim processing turnaround from 14 days to 48 hours.",
            "Enforced granular method-level authorization using Spring Security and JWT, protecting confidential medical diagnosis documents and financial records."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Workflow state machine design in Spring", "Spring Security method-level authorization", "Document storage with cryptographic integrity checks"]
    },
    {
        "slug": "in-java-logistics-tracking-chennai",
        "title": "Logistics and Shipment Tracking Platform",
        "fictional_company_name": "Coromandel Freight Telemetry (Fictional)",
        "location_city": "Chennai",
        "location_state": "Tamil Nadu",
        "industry": "Supply Chain & Logistics Tech",
        "target_job_roles": ["Java / Spring Boot Developer", "Backend Systems Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Multi-modal freight tracking system tracking waypoint check-ins, delivery hub transfers, consignment weight verifications, and delivery SLA milestone alerts.",
        "problem_statement": "Interstate freight carriers suffered from blind spots between hub departures and destination arrivals, leading to inaccurate customer estimated time of arrival (ETA).",
        "technical_stack": ["Java 17", "Spring Boot", "PostgreSQL", "Redis", "Kafka", "Docker"],
        "key_features": [
            "Consignment barcode tracking pipeline recording timestamped waypoint scans across regional distribution hubs.",
            "Real-time hub inventory count tracking active parcels pending vehicle dispatch.",
            "Automated SLA breach predictor alerting logistics managers when consignments remain stationary beyond 6 hours.",
            "Customer-facing tracking API returning chronological shipment journeys with estimated delivery dates."
        ],
        "architecture_summary": "High-throughput Spring Boot service ingesting hub scanner telemetry via Kafka, caching latest parcel statuses in Redis for rapid consumer queries, and persisting to PostgreSQL.",
        "database_design_summary": "Consignment, HubLocation, WaypointScan, VehicleManifest, and DeliveryException tables with B-Tree indexes on tracking_number.",
        "api_design_summary": "Telemetry APIs: POST /api/v1/shipments/scan, GET /api/v1/shipments/track/{trackingNumber}, POST /api/v1/manifests/dispatch.",
        "resume_bullet_templates": [
            "Built logistics consignment tracking backend using Spring Boot and PostgreSQL, processing 25,000+ daily barcode waypoint scans across 18 regional hubs.",
            "Optimized shipment status query response times to sub-15ms by caching current milestone locations and ETAs in Redis.",
            "Engineered automated delivery SLA breach detector triggering alerts for delayed transit consignments, improving on-time dispatch rates by 28%."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["High-volume barcode scanner telemetry ingestion", "Redis caching for high-read APIs", "SLA monitoring and threshold alerting"]
    },
    {
        "slug": "in-java-loan-workflow-pune",
        "title": "Loan Eligibility and Application Workflow",
        "fictional_company_name": "Deccan Credit Solutions (Fictional)",
        "location_city": "Pune",
        "location_state": "Maharashtra",
        "industry": "FinTech & Retail Lending",
        "target_job_roles": ["Java / Spring Boot Developer", "Backend Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Automated retail loan origination platform evaluating applicant credit criteria (CIBIL simulator, debt-to-income ratio, employment tenure) with document verification workflows.",
        "problem_statement": "Manual underwriting of personal and auto loan applications took 5-7 business days and suffered from subjective credit risk assessments.",
        "technical_stack": ["Java 17", "Spring Boot", "Spring Data JPA", "PostgreSQL", "Swagger / OpenAPI", "JUnit 5", "Mockito"],
        "key_features": [
            "Configurable credit risk evaluation engine calculating maximum permissible loan principal based on monthly income and existing EMI burden.",
            "Underwriter dashboard with loan application approval/rejection workflows and audit note capture.",
            "Document verification checklist tracking PAN card, Aadhaar, bank statements, and salary slips.",
            "Automated amortization schedule calculator generating monthly principal and interest installment breakdowns."
        ],
        "architecture_summary": "Enterprise Spring Boot service structured with clean domain services, OpenAPI documentation, and thorough unit testing suite achieving 90%+ code coverage.",
        "database_design_summary": "LoanApplicant, LoanApplication, CreditScoreRecord, AmortizationSchedule, and UnderwriterReview models with strict validation constraints.",
        "api_design_summary": "REST APIs: /api/v1/loans/apply, /api/v1/loans/evaluate-eligibility, /api/v1/underwrite/decision with OpenAPI 3.0 documentation.",
        "resume_bullet_templates": [
            "Developed retail loan origination workflow service using Java 17 and Spring Boot, automating applicant eligibility screening against debt-to-income benchmarks.",
            "Implemented financial amortization calculation engine delivering precise monthly principal/interest schedules across variable loan tenures.",
            "Authored 80+ unit and integration test cases using JUnit 5 and Mockito, achieving 92% code coverage and ensuring regression-free underwriting logic."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Financial math and loan amortization modeling", "Unit and integration testing with Mockito", "OpenAPI documentation and REST contract design"]
    },
    {
        "slug": "in-java-enterprise-employee-noida",
        "title": "Enterprise Employee Management System",
        "fictional_company_name": "NCR Enterprise Systems (Fictional)",
        "location_city": "Noida",
        "location_state": "Uttar Pradesh",
        "industry": "Enterprise IT Services",
        "target_job_roles": ["Java / Spring Boot Developer", "Java Full Stack Developer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Comprehensive IT services employee resource management system coordinating project allocations, billable bench tracking, skill matrices, and appraisal performance reviews.",
        "problem_statement": "Large IT service consultancies experienced revenue loss due to delayed bench resource redeployment and uncataloged employee technology proficiencies.",
        "technical_stack": ["Java 17", "Spring Boot", "Spring Security", "PostgreSQL", "Redis", "Docker"],
        "key_features": [
            "Skill matrix search engine matching employee technical competencies and certification levels against incoming client project requirements.",
            "Billable bench allocation optimizer tracking shadow and billable project assignments with start/end date schedules.",
            "Annual 360-degree performance appraisal workflow with peer review collection and manager rating calibrations.",
            "Departmental headcount and attrition analytics dashboard aggregating monthly joining and exit trends."
        ],
        "architecture_summary": "Spring Boot application featuring Spring Security RBAC, JPA auditing, Redis caching for fast organizational directory searches, and containerized deployment.",
        "database_design_summary": "Employee, Department, Designation, ProjectAllocation, SkillCompetency, and AppraisalReview tables with hierarchical manager-subordinate self-referencing relationships.",
        "api_design_summary": "Resource Management APIs: /api/v1/employees/search?skill=Java, /api/v1/allocations/assign, /api/v1/appraisals/submit.",
        "resume_bullet_templates": [
            "Architected enterprise resource and skill management system using Spring Boot, Hibernate, and PostgreSQL, tracking 3,000+ technical employees across 4 delivery centers.",
            "Optimized bench resource allocation by building a skill-matching search service with Redis caching, accelerating project staffing turnaround by 50%.",
            "Implemented hierarchical organizational role management with Spring Security, securing confidential appraisal data and compensation banding."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Hierarchical database modeling in JPA", "Skill-based search optimization", "Enterprise resource allocation algorithms"]
    },

    # =========================================================================
    # 3. REACT / FULL-STACK DEVELOPER (6 PROJECTS)
    # =========================================================================
    {
        "slug": "in-fs-job-portal-bengaluru",
        "title": "Job Search and Application Tracking Portal",
        "fictional_company_name": "SiliconPlateau Careers (Fictional)",
        "location_city": "Bengaluru",
        "location_state": "Karnataka",
        "industry": "HR Tech & Job Aggregation",
        "target_job_roles": ["React / Full-Stack Developer", "Frontend Engineer", "MERN / Python Full Stack"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Modern responsive job discovery portal with real-time application status tracking, candidate resume profile builder, bookmarking, and recruiter application review dashboards.",
        "problem_statement": "Job seekers struggled with opaque application pipelines and sluggish mobile interfaces when searching for verified engineering openings in Indian tech hubs.",
        "technical_stack": ["React 18", "TypeScript", "Tailwind CSS", "Node.js / Express or Django", "PostgreSQL", "Lucide Icons"],
        "key_features": [
            "Faceted search interface filtering jobs by Indian cities, technology stacks, salary brackets, and work mode (Remote / Hybrid / On-site).",
            "Kanban-style application pipeline for job seekers tracking Applied, Shortlisted, Interviewing, and Offer stages.",
            "Interactive candidate resume profile builder exporting clean standardized resume previews.",
            "Recruiter applicant management interface with one-click candidate shortlisting and rejection email notifications."
        ],
        "architecture_summary": "React 18 Single Page Application (SPA) built with TypeScript and Tailwind CSS, communicating with a RESTful backend using Axios with optimistic UI updates.",
        "database_design_summary": "User, CandidateProfile, JobPosting, JobApplication, SavedJob, and CompanyProfile tables with relational integrity.",
        "api_design_summary": "RESTful endpoints: GET /api/jobs?city=Bengaluru&tech=React, POST /api/applications/apply, PATCH /api/applications/{id}/status.",
        "resume_bullet_templates": [
            "Developed responsive job portal and application tracking interface using React 18, TypeScript, and Tailwind CSS, supporting 10,000+ monthly active candidate sessions.",
            "Implemented client-side faceted filtering and debounced search, reducing API query overhead by 45% while delivering sub-100ms search results.",
            "Built interactive drag-and-drop Kanban application pipeline tracker, enhancing user engagement and job application visibility for candidates."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Modern React 18 state management and custom hooks", "TypeScript typing for complex API contracts", "Faceted search UI engineering with Tailwind CSS"]
    },
    {
        "slug": "in-fs-lms-platform-hyderabad",
        "title": "Online Learning Management Platform",
        "fictional_company_name": "Gachibowli Edutech Labs (Fictional)",
        "location_city": "Hyderabad",
        "location_state": "Telangana",
        "industry": "EdTech & E-Learning",
        "target_job_roles": ["React / Full-Stack Developer", "Frontend Developer", "Full Stack Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Course authoring, video lesson streaming, interactive coding quizzes, student learning progress tracking, and automated completion certificate generation platform.",
        "problem_statement": "Coding bootcamps lacked an integrated portal where students could watch video modules, submit practice assignments, and track their weekly syllabus completion.",
        "technical_stack": ["React 18", "Next.js / Vite", "Tailwind CSS", "Node.js / Python", "PostgreSQL", "Video.js"],
        "key_features": [
            "Course curriculum player with chapter bookmarking, playback speed control, and video lesson completion tracking.",
            "Interactive multi-choice quiz module with instant score calculation and answer explanations.",
            "Student learning progress dashboard visualizing module milestones and overall course completion percentages.",
            "One-click automated certificate generator rendering student name, course title, and unique verification ID upon 100% course completion."
        ],
        "architecture_summary": "Vite React SPA featuring modular component architecture, Video.js media playback integration, and responsive layout styling with Tailwind CSS design tokens.",
        "database_design_summary": "Course, Module, Lesson, QuizQuestion, StudentEnrollment, LessonProgress, and Certificate tables.",
        "api_design_summary": "APIs: GET /api/courses/{slug}/curriculum, POST /api/lessons/{id}/complete, POST /api/quizzes/{id}/submit, GET /api/certificates/{id}.",
        "resume_bullet_templates": [
            "Engineered interactive online learning platform using React 18, Vite, and Tailwind CSS, supporting video course streaming and assignment submissions.",
            "Implemented video player progress tracking and lesson completion state management, automatically resuming playback from the exact dropped timestamp.",
            "Developed dynamic PDF certificate generation engine with cryptographic verification IDs for students completing full curriculum requirements."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Media player event handling in React", "Course progress state synchronization", "Dynamic PDF canvas generation in frontend"]
    },
    {
        "slug": "in-fs-restaurant-delivery-chennai",
        "title": "Restaurant Ordering and Delivery Dashboard",
        "fictional_company_name": "Adyar Foods Telemetry (Fictional)",
        "location_city": "Chennai",
        "location_state": "Tamil Nadu",
        "industry": "FoodTech & Quick Commerce",
        "target_job_roles": ["React / Full-Stack Developer", "Frontend Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Customer digital menu ordering interface, live kitchen order display system (KDS), delivery partner assignment, and real-time order status tracking.",
        "problem_statement": "Cloud kitchens in urban tech corridors struggled with mismatched order tickets between customer apps and busy kitchen preparation stations.",
        "technical_stack": ["React 18", "Redux Toolkit", "Tailwind CSS", "Node.js / Express", "Socket.io", "MongoDB / PostgreSQL"],
        "key_features": [
            "Interactive digital food menu with dietary filters (Veg, Non-Veg, Vegan), item customizations (add-ons, spice levels), and live price recalculations.",
            "Persistent cart management with coupon code redemption and GST tax breakdown calculation.",
            "Kitchen Display System (KDS) updating kitchen staff with incoming, preparing, and ready orders in real-time via WebSockets.",
            "Live order status tracker displaying progress through Received, Kitchen, Out for Delivery, and Delivered stages."
        ],
        "architecture_summary": "React application with centralized Redux Toolkit state for cart and checkout, integrated with Socket.io client for real-time kitchen ticket updates.",
        "database_design_summary": "Restaurant, MenuItem, MenuCategory, CustomerOrder, OrderItemCustomization, and DeliveryAgent models.",
        "api_design_summary": "REST & WebSocket endpoints: /api/menu, POST /api/orders/create, ws://domain/socket.io for kitchen broadcast events.",
        "resume_bullet_templates": [
            "Built responsive food ordering and kitchen management dashboard using React 18, Redux Toolkit, and Tailwind CSS, supporting real-time order state progression.",
            "Streamlined kitchen order fulfillment with live WebSocket updates via Socket.io, reducing ticket preparation latency by 30%.",
            "Architected persistent client-side cart state with coupon discount algorithms and statutory GST computation."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Redux Toolkit cart architecture", "Real-time kitchen order synchronization", "Dietary taxonomy and customization UI design"]
    },
    {
        "slug": "in-fs-real-estate-pune",
        "title": "Real Estate Listing and Property Management Platform",
        "fictional_company_name": "Hinjawadi Properties Tech (Fictional)",
        "location_city": "Pune",
        "location_state": "Maharashtra",
        "industry": "PropTech & Real Estate",
        "target_job_roles": ["React / Full-Stack Developer", "Frontend Developer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Property buy/rent marketplace featuring interactive photo galleries, neighborhood amenities mapping, EMI calculators, and agent inquiry scheduling.",
        "problem_statement": "Prospective tenants and home buyers in IT hubs struggled to verify true carpet areas, location amenities, and accurate monthly EMI figures on fragmented classified sites.",
        "technical_stack": ["React 18", "Next.js", "Tailwind CSS", "Node.js / Django", "PostgreSQL", "Leaflet.js"],
        "key_features": [
            "Faceted property search filtering by BHK configuration (1BHK, 2BHK, 3BHK), rent/buy budget, furnishing status, and pet friendliness.",
            "Interactive home loan EMI calculator estimating monthly installments based on down-payment and interest rates.",
            "Interactive neighborhood map displaying distances to nearby metro stations, IT tech parks, and hospitals using Leaflet.js.",
            "Direct owner/agent inquiry modal with automated WhatsApp chat trigger."
        ],
        "architecture_summary": "Next.js hybrid rendering combining Server-Side Rendering (SSR) for search-engine-friendly property listings with client-side interactive calculators.",
        "database_design_summary": "PropertyListing, PropertyAmenity, PropertyImage, OwnerProfile, and UserInquiry models with geospatial coordinates.",
        "api_design_summary": "APIs: GET /api/properties?city=Pune&bhk=2, POST /api/inquiries/submit, GET /api/properties/{slug}.",
        "resume_bullet_templates": [
            "Developed responsive real estate marketplace platform using React 18, Next.js, and Tailwind CSS, delivering sub-second page loads via Server-Side Rendering.",
            "Integrated Leaflet.js interactive maps to visualize nearby IT parks and public transit distances for 200+ property listings.",
            "Engineered interactive client-side loan EMI amortization calculator, increasing user time-on-site by 40%."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Next.js SSR for content-heavy marketplaces", "Interactive mapping with Leaflet.js", "Financial calculator widgets in React"]
    },
    {
        "slug": "in-fs-support-ticket-gurugram",
        "title": "Customer Support Ticketing Dashboard",
        "fictional_company_name": "UdyogVihar Desk Solutions (Fictional)",
        "location_city": "Gurugram",
        "location_state": "Haryana",
        "industry": "Enterprise Customer Experience (CX)",
        "target_job_roles": ["React / Full-Stack Developer", "Frontend Developer", "MERN Developer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Multi-agent customer support desk with ticket priority triage, threaded conversation replies, SLA response countdown timers, and customer satisfaction ratings.",
        "problem_statement": "Customer support teams experienced missed SLAs and collision between multiple agents responding to the same customer ticket simultaneously.",
        "technical_stack": ["React 18", "TypeScript", "Tailwind CSS", "Node.js / Express", "PostgreSQL", "Socket.io"],
        "key_features": [
            "Agent collision detection warning staff when another support representative is actively viewing or typing a response.",
            "Color-coded SLA countdown timer alerting agents to impending response breach deadlines.",
            "Threaded conversation timeline displaying customer inquiries, internal team notes, and email attachments.",
            "Manager performance analytics tracking First Contact Resolution (FCR) rate and average customer satisfaction (CSAT) scores."
        ],
        "architecture_summary": "React SPA with TypeScript strict typing, Socket.io for live agent presence indicators, and Tailwind CSS responsive dashboard layout.",
        "database_design_summary": "Customer, SupportAgent, SupportTicket, TicketMessage, InternalNote, and CSATSurvey tables with foreign key constraints.",
        "api_design_summary": "REST & WS APIs: /api/tickets, PATCH /api/tickets/{id}/assign, POST /api/tickets/{id}/messages, ws://domain/socket.io for presence.",
        "resume_bullet_templates": [
            "Built multi-agent customer support ticketing dashboard using React 18, TypeScript, and Tailwind CSS, managing end-to-end customer resolution workflows.",
            "Implemented real-time agent collision detection via WebSockets, preventing duplicate support representative responses on open customer tickets.",
            "Designed dynamic SLA countdown timer and automated priority sorting, improving first-response turnaround by 35% across simulated ticket queues."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Real-time agent presence detection", "Complex threaded messaging UI", "SLA timer state machines in React"]
    },
    {
        "slug": "in-fs-travel-agency-kochi",
        "title": "Travel Agency Booking Website",
        "fictional_company_name": "Malabar Coast Expeditions (Fictional)",
        "location_city": "Kochi",
        "location_state": "Kerala",
        "industry": "Tourism & Hospitality",
        "target_job_roles": ["React / Full-Stack Developer", "Frontend Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Luxury travel portal featuring destination discovery, customized multi-day tour package bookings, photo carousels, and verified customer testimonials.",
        "problem_statement": "Boutique eco-tourism operators struggled to convert international website visitors due to static brochure websites lacking transparent pricing and instant booking.",
        "technical_stack": ["React 18", "Next.js", "Tailwind CSS", "Framer Motion", "PostgreSQL", "Stripe / Razorpay Sandbox"],
        "key_features": [
            "Fluid micro-animations and smooth page transitions across destination discovery guides using Framer Motion.",
            "Dynamic tour cost estimator calculating seasonal price adjustments and private vehicle transportation options.",
            "Multi-step checkout modal with passenger detail capture, dietary preferences, and instant payment sandbox authorization.",
            "Curated customer reviews module with verified trip photos and star rating aggregations."
        ],
        "architecture_summary": "Next.js frontend with Framer Motion spring physics animations, optimized static asset delivery, and responsive mobile-first typography.",
        "database_design_summary": "TourPackage, TourDay, PackageAddon, BookingOrder, PassengerDetail, and CustomerReview models.",
        "api_design_summary": "APIs: GET /api/packages, POST /api/bookings/checkout, POST /api/reviews/submit.",
        "resume_bullet_templates": [
            "Developed luxury travel booking web platform using React 18, Next.js, and Tailwind CSS, featuring engaging destination discovery workflows.",
            "Integrated Framer Motion spring-physics micro-interactions and responsive photo galleries, elevating user engagement and brand perception.",
            "Architected multi-step reservation checkout flow with dynamic seasonal cost computation and sandbox payment gateway confirmation."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Framer Motion animation design", "Next.js image optimization", "Multi-step form wizard architecture"]
    },

    # =========================================================================
    # 4. DEVOPS / CLOUD ENGINEER (6 PROJECTS)
    # =========================================================================
    {
        "slug": "in-devops-microservices-docker-bengaluru",
        "title": "Dockerized Microservices Deployment Platform",
        "fictional_company_name": "OuterRing Cloud DevOps Lab (Fictional)",
        "location_city": "Bengaluru",
        "location_state": "Karnataka",
        "industry": "Cloud Infrastructure & Containerization",
        "target_job_roles": ["DevOps / Cloud Engineer", "Site Reliability Engineer", "Platform Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Multi-container containerization and local orchestration suite bundling microservices, NGINX reverse proxy, Redis cache, and PostgreSQL with health-check automation.",
        "problem_statement": "Engineering teams experienced the classic 'works on my machine' defect due to divergent runtime library versions across developer laptops and production servers.",
        "technical_stack": ["Docker", "Docker Compose", "NGINX", "Linux", "Bash", "PostgreSQL", "Redis"],
        "key_features": [
            "Multi-stage Dockerfile construction optimizing image sizes by 65% using alpine and distroless runtime bases.",
            "NGINX reverse proxy routing traffic to backend microservice containers with SSL termination and gzip compression.",
            "Automated health-check probes ensuring dependent database and cache services are healthy before application startup.",
            "Non-root container user enforcement and minimal attack surface configuration adhering to CIS benchmark standards."
        ],
        "architecture_summary": "Docker Compose orchestration defining isolated bridge networks, named persistent volumes for PostgreSQL data, and NGINX edge gateway routing.",
        "database_design_summary": "Automated PostgreSQL database initialization with schema migration scripts executed via container entrypoint hooks.",
        "api_design_summary": "Infrastructure endpoints: http://localhost/health, http://localhost/nginx_status, and proxied application routes.",
        "resume_bullet_templates": [
            "Containerized multi-tier microservice architecture using Docker and Docker Compose, reducing developer onboarding environment setup time from 2 days to 15 minutes.",
            "Optimized application Docker container images using multi-stage builds, reducing final artifact size by 65% (from 850MB to 145MB).",
            "Configured NGINX reverse proxy with SSL termination, connection keep-alives, and health-check dependent service startup ordering."
        ],
        "estimated_duration": "2-3 weeks",
        "learning_outcomes": ["Multi-stage Dockerfile optimization", "Container network isolation and volume persistence", "NGINX reverse proxy and load balancing"]
    },
    {
        "slug": "in-devops-kubernetes-deployment-hyderabad",
        "title": "Kubernetes-Based Application Deployment Lab",
        "fictional_company_name": "Cyberabad K8s Infrastructure (Fictional)",
        "location_city": "Hyderabad",
        "location_state": "Telangana",
        "industry": "Cloud-Native & Container Orchestration",
        "target_job_roles": ["DevOps / Cloud Engineer", "Kubernetes Engineer", "SRE"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "Production-ready Kubernetes deployment architecture featuring Horizontal Pod Autoscaling (HPA), zero-downtime rolling updates, Ingress routing, and ConfigMap/Secret management.",
        "problem_statement": "Web applications crashed during sudden traffic spikes due to lack of automated horizontal replica scaling and suffered downtime during version deployments.",
        "technical_stack": ["Kubernetes", "Minikube / Kind / EKS", "Helm", "NGINX Ingress", "Metrics Server", "Docker"],
        "key_features": [
            "Horizontal Pod Autoscaler (HPA) automatically scaling pod replicas from 2 to 10 based on real-time CPU and memory threshold metrics.",
            "Zero-downtime rolling update deployments configured with readiness and liveness probes eliminating dropped requests.",
            "NGINX Ingress controller managing path-based routing, TLS termination, and rate-limiting annotations.",
            "Centralized configuration decoupled via ConfigMaps and Secrets mounted as environment variables and volume projections."
        ],
        "architecture_summary": "Kubernetes manifest and Helm chart architecture separating staging and production namespaces, utilizing cluster resource quotas and network policies.",
        "database_design_summary": "StatefulSet deployment with persistent volume claims (PVC) backed by dynamic storage provisioners for reliable database persistence.",
        "api_design_summary": "Kubelet health probes: livenessProbe on /healthz and readinessProbe on /ready configured with initialDelaySeconds.",
        "resume_bullet_templates": [
            "Architected production-grade Kubernetes deployment manifests and Helm charts, achieving zero-downtime rolling updates for web application workloads.",
            "Implemented Horizontal Pod Autoscaler (HPA) based on CPU and memory metrics, automatically scaling pod replicas to accommodate simulated 5x traffic surges.",
            "Configured NGINX Ingress Controller with SSL termination and custom liveness/readiness health probes, preventing unready pods from serving live traffic."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Kubernetes deployment patterns and rolling updates", "HPA and metrics-server scaling", "Helm chart packaging and parameterization"]
    },
    {
        "slug": "in-devops-cicd-github-actions-pune",
        "title": "CI/CD Pipeline with GitHub Actions",
        "fictional_company_name": "ShivajiNagar Automation Systems (Fictional)",
        "location_city": "Pune",
        "location_state": "Maharashtra",
        "industry": "DevSecOps & Continuous Delivery",
        "target_job_roles": ["DevOps / Cloud Engineer", "DevSecOps Engineer", "Build & Release Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Automated end-to-end continuous integration and deployment pipeline enforcing linting, unit testing, static code analysis, Docker image building, and staging deployment.",
        "problem_statement": "Development teams suffered from slow release cycles and undetected security vulnerabilities due to manual testing and manual SSH deployment scripts.",
        "technical_stack": ["GitHub Actions", "Docker Hub / GHCR", "SonarQube / Trivy", "Bash", "Linux", "SSH / AWS EC2"],
        "key_features": [
            "Multi-job GitHub Actions workflow triggered on pull requests running unit tests, code coverage reports, and formatting checks.",
            "Security vulnerability scanning with Trivy detecting CVEs in container base images before artifact publishing.",
            "Automated semantic version tagging and container image publishing to GitHub Container Registry (GHCR).",
            "Zero-downtime staging deployment via automated SSH deployment hooks and Docker Compose reloads."
        ],
        "architecture_summary": "Declarative YAML workflow executing parallel matrix jobs, caching dependencies (pip/npm/maven) to accelerate pipeline execution, and gated production environments.",
        "database_design_summary": "Automated database schema migration validation executed inside ephemeral test containers during the CI test phase.",
        "api_design_summary": "Webhook notifications dispatched to Slack/Discord upon pipeline pass or failure with commit author details.",
        "resume_bullet_templates": [
            "Constructed automated CI/CD pipeline using GitHub Actions, reducing software build, test, and staging deployment cycles from 45 mins to 6 mins.",
            "Integrated Trivy container security scanning and automated code coverage quality gates, preventing high-severity CVEs from reaching production.",
            "Automated container build and publishing to GHCR with semantic versioning, eliminating manual deployment errors across environments."
        ],
        "estimated_duration": "2-3 weeks",
        "learning_outcomes": ["GitHub Actions declarative YAML syntax", "Dependency caching and build acceleration", "DevSecOps vulnerability scanning with Trivy"]
    },
    {
        "slug": "in-devops-aws-monitoring-mumbai",
        "title": "AWS Monitoring and Alerting Dashboard",
        "fictional_company_name": "Bandra Cloud Telemetry (Fictional)",
        "location_city": "Mumbai",
        "location_state": "Maharashtra",
        "industry": "Observability & SRE",
        "target_job_roles": ["DevOps / Cloud Engineer", "SRE", "Cloud Administrator"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "CloudWatch and Prometheus monitoring infrastructure aggregating system metrics, application error rates, and automated PagerDuty/Slack incident alerts.",
        "problem_statement": "Engineering teams only discovered production outages when customers reported them on social media due to absence of proactive threshold alerting.",
        "technical_stack": ["AWS CloudWatch", "Prometheus", "Grafana", "Alertmanager", "Node Exporter", "Docker"],
        "key_features": [
            "Prometheus scraping architecture capturing host CPU, memory, disk I/O, and HTTP 5xx error rate telemetry.",
            "Grafana visualization dashboards displaying real-time cluster health, request latency percentiles (p50, p95, p99), and throughput.",
            "Alertmanager routing with severity-based escalation (P1 Critical, P2 Warning) dispatched to Slack and email channels.",
            "Custom CloudWatch metric filters monitoring application log files for recurring critical exception patterns."
        ],
        "architecture_summary": "Decoupled monitoring stack running Node Exporter on target servers, centralized Prometheus metric aggregation, Grafana dashboards, and Alertmanager routing.",
        "database_design_summary": "Prometheus Time-Series Database (TSDB) configured with 30-day retention policies and disk space volume limits.",
        "api_design_summary": "Scrape endpoints: /metrics on target instances adhering to OpenMetrics/Prometheus exposition standards.",
        "resume_bullet_templates": [
            "Built centralized cloud monitoring and alerting infrastructure using Prometheus, Grafana, and AWS CloudWatch, tracking 15+ microservice metrics.",
            "Designed executive Grafana dashboards visualizing p95/p99 latency percentiles, error rates, and system utilization, cutting Mean Time to Detect (MTTD) by 60%.",
            "Configured Alertmanager notification rules with severity-based escalation to Slack, enabling proactive remediation of impending server memory exhaustion."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Prometheus time-series metric collection", "Grafana dashboard craftsmanship and PromQL", "Alert routing and notification escalation"]
    },
    {
        "slug": "in-devops-terraform-iac-chennai",
        "title": "Infrastructure as Code Demonstration Using Terraform",
        "fictional_company_name": "TidelPark Cloud Automation (Fictional)",
        "location_city": "Chennai",
        "location_state": "Tamil Nadu",
        "industry": "Cloud Architecture & Infrastructure as Code",
        "target_job_roles": ["DevOps / Cloud Engineer", "Cloud Architect", "Platform Engineer"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "Modular Terraform architecture provisioning high-availability AWS Virtual Private Cloud (VPC), public/private subnets, Auto Scaling Groups, Application Load Balancers, and RDS databases.",
        "problem_statement": "Cloud resources were provisioned manually via the AWS Management Console, creating configuration drift and unreplicable staging environments.",
        "technical_stack": ["Terraform", "AWS (VPC, EC2, ALB, RDS, S3)", "LocalStack (for local emulation)", "tflint", "Git"],
        "key_features": [
            "Multi-tier VPC module configuring public subnets with Internet Gateway and private subnets with NAT Gateways across multiple Availability Zones.",
            "Remote state management with S3 backend and DynamoDB distributed state locking preventing concurrent deployment conflicts.",
            "Reusable Terraform modules parameterizing environment differences (Dev, Staging, Prod) via tfvars configurations.",
            "Automated static code linting with tflint and security policy checking with checkov."
        ],
        "architecture_summary": "Modular Terraform HCL project following standard module structures (modules/vpc, modules/compute, modules/database) with remote S3 state backend.",
        "database_design_summary": "Multi-AZ AWS RDS PostgreSQL instance provisioned inside isolated private subnets with encrypted storage and automated snapshot backups.",
        "api_design_summary": "Terraform outputs exposing ALB DNS names, VPC IDs, and database endpoints for dependent application pipelines.",
        "resume_bullet_templates": [
            "Provisioned high-availability AWS multi-tier cloud infrastructure using Terraform, automating VPC, ALB, Auto Scaling, and RDS provisioning across multiple Availability Zones.",
            "Implemented secure remote state architecture using Amazon S3 and DynamoDB state locking, preventing configuration drift and concurrent deployment collisions.",
            "Architected reusable, parameterized Terraform modules for Dev, Staging, and Production environments, reducing environment replication time from days to under 15 minutes."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Terraform module design and HCL best practices", "Remote state locking with S3 and DynamoDB", "AWS enterprise VPC networking architecture"]
    },
    {
        "slug": "in-devops-logging-elk-noida",
        "title": "Centralized Logging and Observability Platform",
        "fictional_company_name": "Sector62 Observability Labs (Fictional)",
        "location_city": "Noida",
        "location_state": "Uttar Pradesh",
        "industry": "Enterprise Monitoring & Log Analytics",
        "target_job_roles": ["DevOps / Cloud Engineer", "SRE", "Systems Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Centralized log aggregation and search platform utilizing Elasticsearch, Fluentd/Logstash, and Kibana (EFK/ELK) for real-time error log troubleshooting.",
        "problem_statement": "Engineers spent hours manually SSH-ing into dozens of distributed production servers and grepping through gigabytes of scattered log files during outages.",
        "technical_stack": ["Elasticsearch", "Logstash / Fluent Bit", "Kibana", "Docker", "Linux", "Filebeat"],
        "key_features": [
            "Log shipping agent (Filebeat/Fluent Bit) tailing application container stdout and system syslog files with low CPU footprint.",
            "Log parsing and enrichment pipeline extracting JSON fields, HTTP status codes, and user IDs using Logstash Grok filters.",
            "Kibana discovery dashboards with Lucene query syntax facilitating rapid root-cause analysis during production incidents.",
            "Automated index lifecycle management (ILM) rolling over daily indexes and deleting log records older than 30 days."
        ],
        "architecture_summary": "Distributed log shipping pipeline from Filebeat edge daemons through Logstash enrichment workers into Elasticsearch cluster with Kibana visualization UI.",
        "database_design_summary": "Elasticsearch inverted index mappings configured with timestamp fields, keyword analyzers, and ILM policy attachments.",
        "api_design_summary": "Elasticsearch REST APIs: GET /app-logs-*/_search with complex boolean query payloads.",
        "resume_bullet_templates": [
            "Constructed centralized log aggregation platform using the ELK Stack (Elasticsearch, Logstash, Kibana) and Filebeat, ingesting 100GB+ of daily application logs.",
            "Engineered Logstash Grok parsing pipelines to structure raw log events into searchable JSON schemas, reducing production issue diagnosis time from hours to minutes.",
            "Configured Elasticsearch Index Lifecycle Management (ILM) policies, optimizing disk storage consumption by 40% through automated index rollover and archival."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Log shipping architectures with Filebeat and Logstash", "Grok pattern parsing and log enrichment", "Elasticsearch index lifecycle management (ILM)"]
    },

    # =========================================================================
    # 5. DATA ENGINEER / PYSPARK / DATABRICKS (6 PROJECTS)
    # =========================================================================
    {
        "slug": "in-data-banking-etl-mumbai",
        "title": "Banking Transactions ETL and Analytics Platform",
        "fictional_company_name": "Fort Financial Analytics (Fictional)",
        "location_city": "Mumbai",
        "location_state": "Maharashtra",
        "industry": "FinTech & Banking Analytics",
        "target_job_roles": ["Data Engineer", "PySpark Developer", "Big Data Engineer"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "High-volume batch and micro-batch ETL pipeline processing millions of banking transactions, reconciling daily ledger balances, and populating compliance data marts.",
        "problem_statement": "End-of-day bank transaction reconciliation jobs failed to complete within overnight batch windows, causing delayed regulatory reporting and customer balance mismatches.",
        "technical_stack": ["Python", "PySpark", "Apache Airflow", "PostgreSQL", "AWS S3 / MinIO", "Parquet"],
        "key_features": [
            "PySpark batch processing transforming raw CSV and JSON transaction dumps into partitioned columnar Parquet datasets.",
            "Apache Airflow Directed Acyclic Graph (DAG) scheduling data extraction, transformation, quality checks, and warehouse loading.",
            "Data quality validation layer verifying zero missing transaction IDs, positive debit/credit amounts, and balanced ledger sums.",
            "Automated partition pruning on (transaction_year, transaction_month) accelerating downstream analytical SQL queries."
        ],
        "architecture_summary": "Medallion data architecture: Bronze (raw ingested records), Silver (cleansed and validated Parquet files), and Gold (aggregated customer account marts) orchestrated by Airflow.",
        "database_design_summary": "Star-schema dimensional model with Fact_Transaction and Dim_Customer, Dim_Branch, Dim_Account, and Dim_Date tables.",
        "api_design_summary": "Analytical SQL query interfaces and Airflow REST APIs: /api/v1/dags/banking_etl_pipeline/dagRuns.",
        "resume_bullet_templates": [
            "Architected scalable batch ETL pipeline using Python, PySpark, and Apache Airflow, processing 5M+ daily simulated banking transactions into partitioned Parquet datasets.",
            "Designed automated data-quality audit framework validating schema conformity, null value thresholds, and ledger balance reconciliation across ETL stages.",
            "Optimized Spark transformations using broadcast joins and partition pruning, reducing overnight batch execution runtime by 55%."
        ],
        "estimated_duration": "4 weeks",
        "learning_outcomes": ["Medallion data lake architecture", "PySpark execution plan optimization and broadcast joins", "Apache Airflow DAG scheduling and error handling"]
    },
    {
        "slug": "in-data-ecommerce-lakehouse-bengaluru",
        "title": "E-commerce Sales Data Lakehouse",
        "fictional_company_name": "Bellandur Analytics Cloud (Fictional)",
        "location_city": "Bengaluru",
        "location_state": "Karnataka",
        "industry": "E-Commerce & Lakehouse Analytics",
        "target_job_roles": ["Data Engineer", "Databricks Engineer", "Cloud Data Architect"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "Modern Delta Lake / Databricks lakehouse unifying clickstream click-events, order transactions, and inventory snapshots for real-time business intelligence.",
        "problem_statement": "E-commerce marketing teams experienced 24-hour delays in customer conversion attribution and suffered from duplicate orders in analytical dashboards.",
        "technical_stack": ["PySpark", "Delta Lake", "Databricks", "Python", "SQL", "Apache Spark"],
        "key_features": [
            "Delta Lake implementation providing ACID transactions, time travel history, and schema enforcement over object storage.",
            "Merge (upsert) CDC pipeline reconciling order cancellations, returns, and inventory modifications without full table scans.",
            "Z-Order clustering on customer_id and event_timestamp optimizing BI dashboard query latency.",
            "Aggregated customer lifetime value (CLV) and churn propensity feature tables for marketing analytics."
        ],
        "architecture_summary": "Databricks Delta Lake medallion architecture running PySpark structured streaming and batch merges over cloud object storage.",
        "database_design_summary": "Delta tables: bronze_events, silver_orders, gold_customer_metrics with partition by date and Z-Order on high-cardinality keys.",
        "api_design_summary": "SQL queries and Spark SQL views feeding BI reporting tools via Databricks SQL endpoints.",
        "resume_bullet_templates": [
            "Engineered modern data lakehouse platform using PySpark and Delta Lake, ingesting 10M+ daily e-commerce clickstream and order transaction events.",
            "Implemented Delta Lake ACID upserts (MERGE) for change data capture (CDC), eliminating duplicate order records and ensuring transactional consistency.",
            "Accelerated analytical BI queries by 4x by applying Delta Z-Order clustering and file compaction on high-cardinality customer dimensions."
        ],
        "estimated_duration": "4-5 weeks",
        "learning_outcomes": ["Delta Lake ACID transaction guarantees and time travel", "CDC upsert patterns with PySpark", "Z-Order clustering and data layout optimization"]
    },
    {
        "slug": "in-data-telecom-pipeline-hyderabad",
        "title": "Telecom Usage Analytics Pipeline",
        "fictional_company_name": "Telangana Cellular Data Labs (Fictional)",
        "location_city": "Hyderabad",
        "location_state": "Telangana",
        "industry": "Telecommunications & Big Data",
        "target_job_roles": ["Data Engineer", "Big Data Engineer", "PySpark Developer"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "High-throughput Call Detail Record (CDR) aggregation pipeline computing data consumption trends, dropped call rates, and network tower load heatmaps.",
        "problem_statement": "Telecom network operations teams lacked real-time visibility into cell tower congestion and high-usage subscriber bands, leading to delayed network optimization.",
        "technical_stack": ["PySpark", "Python", "Apache Kafka", "PostgreSQL", "Docker", "Parquet"],
        "key_features": [
            "Call Detail Record (CDR) parser ingesting high-velocity telecom records and extracting call duration, byte transfer, and tower IDs.",
            "Aggregated cell tower usage metrics identifying peak congestion hours and degraded quality-of-service zones.",
            "Subscriber data consumption windowing calculating data rollover and fair usage policy (FUP) tier breaches.",
            "Data masking and pseudonymization protecting sensitive phone numbers and subscriber PII."
        ],
        "architecture_summary": "Streaming and micro-batch processing engine ingesting CDR events through Kafka into PySpark aggregations, writing summarized marts to PostgreSQL.",
        "database_design_summary": "cdr_raw, tower_hourly_summary, subscriber_daily_usage, and network_outage_events tables.",
        "api_design_summary": "Analytical SQL views: vw_tower_congestion_hotspots, vw_subscriber_plan_utilization.",
        "resume_bullet_templates": [
            "Constructed big data telecom analytics pipeline using PySpark and Kafka, ingesting and aggregating 15M+ daily Call Detail Records (CDRs).",
            "Engineered hourly cell tower congestion windowing aggregations, enabling network operations teams to identify degraded service zones rapidly.",
            "Implemented subscriber data privacy masking pipelines in compliance with telecom regulatory standards, securing customer phone numbers and identities."
        ],
        "estimated_duration": "4 weeks",
        "learning_outcomes": ["High-velocity telecom CDR aggregation", "PySpark windowing functions and aggregations", "PII data anonymization in big data pipelines"]
    },
    {
        "slug": "in-data-retail-warehouse-pune",
        "title": "Retail Inventory Data Warehouse",
        "fictional_company_name": "Sahyadri Retail Insights (Fictional)",
        "location_city": "Pune",
        "location_state": "Maharashtra",
        "industry": "Retail & Supply Chain Analytics",
        "target_job_roles": ["Data Engineer", "SQL Developer", "ETL Developer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Dimensional data warehouse and ETL pipeline tracking retail store sales, stock replenishment turnover, supplier lead times, and seasonal demand forecasting.",
        "problem_statement": "Supermarket retail chains suffered stockouts of high-velocity grocery items while slow-moving inventory tied up working capital across regional stores.",
        "technical_stack": ["Python", "SQL", "PostgreSQL", "dbt (data build tool)", "Pandas", "Docker"],
        "key_features": [
            "Kimball dimensional model implementing Star Schema with Fact_StoreSales and Slowly Changing Dimensions (SCD Type 2) for product pricing history.",
            "dbt transformation models with automated schema tests ensuring primary key uniqueness and referential integrity.",
            "Inventory turnover and days-of-supply metrics calculated per store location and product category.",
            "Automated CSV ingestion from Point of Sale (POS) terminals with data sanitization and anomaly logging."
        ],
        "architecture_summary": "dbt-driven analytical data warehouse structured into staging, intermediate, and marts layers running over PostgreSQL warehouse storage.",
        "database_design_summary": "Dim_Product (SCD Type 2), Dim_Store, Dim_Date, Dim_Supplier, and Fact_DailyInventorySales tables with surrogate keys.",
        "api_design_summary": "dbt documentation portal and analytical SQL views for store inventory health and reorder recommendations.",
        "resume_bullet_templates": [
            "Designed Kimball dimensional data warehouse using PostgreSQL and dbt, modeling store sales and inventory turnover across 25 regional supermarket locations.",
            "Implemented Slowly Changing Dimension (SCD Type 2) tracking historical product price shifts and supplier lead time alterations.",
            "Configured automated dbt testing suites for schema validation and referential integrity, eliminating data pipeline regressions."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Kimball dimensional modeling and star schema design", "dbt transformation workflows and testing", "Slowly Changing Dimensions (SCD Type 2)"]
    },
    {
        "slug": "in-data-logistics-delivery-chennai",
        "title": "Logistics Delivery Analytics Pipeline",
        "fictional_company_name": "Marina Express Analytics (Fictional)",
        "location_city": "Chennai",
        "location_state": "Tamil Nadu",
        "industry": "Logistics & Supply Chain Telemetry",
        "target_job_roles": ["Data Engineer", "Python Data Engineer", "PySpark Developer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "GPS delivery route telemetry ETL pipeline computing driver delivery efficiency, fuel consumption estimates, and first-attempt delivery success rates.",
        "problem_statement": "Last-mile courier providers lacked granular visibility into delivery driver route deviations and causes of failed first-attempt deliveries.",
        "technical_stack": ["Python", "PySpark / Pandas", "PostgreSQL", "Apache Airflow", "GeoPandas", "Docker"],
        "key_features": [
            "Spatial route telemetry processing calculating total distance traversed, average stop duration, and route efficiency ratios.",
            "Failure analysis categorizing undelivered consignments (Customer Unavailable, Address Not Found, Cash on Delivery Rejection).",
            "Daily driver performance scorecards rewarding high on-time delivery rates and low package return ratios.",
            "Automated daily Airflow orchestration triggering batch data extraction, transformation, and reporting generation."
        ],
        "architecture_summary": "Airflow-orchestrated ETL pipeline processing GPS coordinates with GeoPandas and PySpark, persisting analytical aggregations into PostgreSQL.",
        "database_design_summary": "fact_delivery_trip, dim_driver, dim_delivery_hub, and dim_consignment tables with spatial distance functions.",
        "api_design_summary": "Airflow DAG triggers and analytical SQL reporting queries.",
        "resume_bullet_templates": [
            "Developed logistics telemetry data pipeline using Python, PySpark, and PostgreSQL, analyzing 50,000+ daily last-mile parcel delivery routes.",
            "Engineered spatial route efficiency metrics and stop-duration analytics, uncovering last-mile transit bottlenecks and reducing driver idle time by 22%.",
            "Orchestrated automated daily ETL workflows with Apache Airflow, providing management with daily delivery success scorecards."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Spatial and GPS route data processing", "Last-mile logistics KPI calculations", "Airflow workflow scheduling and dependency graphs"]
    },
    {
        "slug": "in-data-financial-reporting-gurugram",
        "title": "Financial Reporting and Data Quality Platform",
        "fictional_company_name": "DLF Capital Data Labs (Fictional)",
        "location_city": "Gurugram",
        "location_state": "Haryana",
        "industry": "FinTech & Regulatory Data Governance",
        "target_job_roles": ["Data Engineer", "Data Quality Engineer", "Analytics Engineer"],
        "difficulty_level": "Advanced",
        "project_type": "Personal Portfolio Project",
        "description": "Enterprise financial data reconciliation engine validating accounting data feeds across general ledgers, sub-ledgers, and external banking statements with Great Expectations.",
        "problem_statement": "Quarterly financial closes required weeks of manual spreadsheet reconciliations due to missing invoice numbers and currency conversion rate mismatches.",
        "technical_stack": ["Python", "Great Expectations", "PostgreSQL", "SQL", "Pandas", "Docker"],
        "key_features": [
            "Automated data quality assertion suites verifying non-null balances, valid currency ISO codes, and balanced ledger debits/credits.",
            "Cross-system reconciliation matching ERP invoice records against bank deposit statements with automated tolerance thresholds.",
            "Data drift and anomaly detection alerting financial controllers to sudden spikes in unclassified expense line items.",
            "Automated data documentation generation publishing interactive data health reports for external compliance auditors."
        ],
        "architecture_summary": "Python-based data quality and reconciliation engine integrated with Great Expectations, PostgreSQL relational tables, and automated HTML data docs.",
        "database_design_summary": "gl_journal_entry, sub_ledger_ar, bank_statement_feed, reconciliation_match, and dq_audit_results tables.",
        "api_design_summary": "CLI and programmatic Python APIs triggering reconciliation pipelines and exporting Great Expectations validation results.",
        "resume_bullet_templates": [
            "Architected automated financial data reconciliation platform using Python, Great Expectations, and PostgreSQL, validating financial records across 3 ERP systems.",
            "Implemented 40+ rigorous data quality assertion rules verifying ledger balance parity and eliminating manual spreadsheet reconciliation bottlenecks.",
            "Designed automated cross-system match engine with fuzzy tolerance thresholds, reducing quarterly financial close reconciliation time by 4 days."
        ],
        "estimated_duration": "3-4 weeks",
        "learning_outcomes": ["Automated data testing with Great Expectations", "Financial cross-ledger reconciliation patterns", "Data governance and documentation publishing"]
    },

    # =========================================================================
    # 6. QA / AUTOMATION ENGINEER (4 PROJECTS)
    # =========================================================================
    {
        "slug": "in-qa-ecommerce-api-bengaluru",
        "title": "E-commerce API Automation Framework",
        "fictional_company_name": "Indiranagar QA Systems (Fictional)",
        "location_city": "Bengaluru",
        "location_state": "Karnataka",
        "industry": "QA Automation & Retail Tech",
        "target_job_roles": ["QA / Automation Engineer", "SDET", "API Test Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Comprehensive REST API test automation framework for e-commerce platforms testing user authentication, product catalog search, cart operations, and payment webhooks.",
        "problem_statement": "Manual testing of 80+ REST API endpoints before each deployment delayed production releases and allowed edge-case pricing bugs to escape into production.",
        "technical_stack": ["Python", "Pytest", "Requests", "Allure Reports", "Postman / Newman", "Docker", "GitHub Actions"],
        "key_features": [
            "Data-driven test suite with 150+ automated test cases covering positive, negative, and edge-case API responses.",
            "Automated JSON schema validation ensuring contract compliance across product and checkout endpoints.",
            "Integrated Allure reporting dashboard providing detailed visual execution timelines and failed request payloads.",
            "Continuous Integration integration running automated test suites on every pull request via GitHub Actions."
        ],
        "architecture_summary": "Pytest automation framework structured with page/service object models, modular fixtures for token authentication, and Allure report generators.",
        "database_design_summary": "Test fixture teardown scripts resetting database test state after each execution run to ensure zero test pollution.",
        "api_design_summary": "Automated test coverage over: /api/v1/auth/login, /api/v1/cart/add, /api/v1/checkout, and /api/v1/orders.",
        "resume_bullet_templates": [
            "Designed and implemented modular REST API test automation framework using Python, Pytest, and Requests, automating 150+ end-to-end e-commerce test scenarios.",
            "Implemented automated JSON schema validation and boundary value analysis, detecting 25+ contract regressions prior to production release.",
            "Integrated automated test execution into GitHub Actions with Allure visual reporting, cutting regression cycle time from 16 hours to 12 minutes."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["API test automation framework design with Pytest", "JSON schema contract testing", "CI/CD test pipeline integration with Allure"]
    },
    {
        "slug": "in-qa-banking-api-mumbai",
        "title": "Banking REST API Testing Framework",
        "fictional_company_name": "BKC FinTest Solutions (Fictional)",
        "location_city": "Mumbai",
        "location_state": "Maharashtra",
        "industry": "FinTech & Banking QA",
        "target_job_roles": ["QA / Automation Engineer", "SDET", "Java Test Automation"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Robust banking API automation framework testing authentication security, fund transfer concurrency, account overdraft validation, and idempotency guarantees.",
        "problem_statement": "Critical financial APIs required rigorous automated regression testing across rate limits, expired JWT tokens, and negative balance transaction attempts.",
        "technical_stack": ["Java", "RestAssured", "TestNG", "ExtentReports", "Maven", "Docker"],
        "key_features": [
            "RestAssured test framework validating financial REST endpoints with strict HTTP status code and header assertions.",
            "Security vulnerability tests evaluating expired JWT tokens, SQL injection payloads, and unauthorized account access attempts.",
            "Data-driven testing using TestNG DataProviders for parameterized test execution across multiple user roles and currencies.",
            "Detailed ExtentReports dashboard capturing request/response payloads and execution latency benchmarks."
        ],
        "architecture_summary": "Java Maven project using RestAssured for HTTP client interactions, TestNG for test execution and grouping, and ExtentReports for test results.",
        "database_design_summary": "Automated test database seeders creating clean mock customer balances prior to transfer test executions.",
        "api_design_summary": "Test suites for: POST /api/v1/auth/token, POST /api/v1/transfers, GET /api/v1/accounts/statement.",
        "resume_bullet_templates": [
            "Constructed banking API test automation suite using Java, RestAssured, and TestNG, achieving 95%+ automated coverage across critical payment endpoints.",
            "Automated security regression tests verifying JWT token expiration and unauthorized account access prevention across banking user personas.",
            "Engineered data-driven test suites with ExtentReports reporting, identifying API response latency regressions exceeding 500ms SLAs."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["RestAssured framework architecture", "Financial API negative and security testing", "TestNG DataProviders and reporting"]
    },
    {
        "slug": "in-qa-hr-portal-e2e-pune",
        "title": "HR Portal End-to-End Testing Suite",
        "fictional_company_name": "KalyaniNagar QA Labs (Fictional)",
        "location_city": "Pune",
        "location_state": "Maharashtra",
        "industry": "Enterprise HR Tech & Web Testing",
        "target_job_roles": ["QA / Automation Engineer", "SDET", "Web Automation Engineer"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Full end-to-end web browser test automation suite validating employee onboarding, leave application workflows, manager approval flows, and payslip downloads.",
        "problem_statement": "Manual cross-browser testing of employee self-service portals across Chrome, Firefox, and Edge resulted in release delays and untested UI regression bugs.",
        "technical_stack": ["Python", "Selenium WebDriver", "Playwright", "Pytest", "Allure Reports", "Docker"],
        "key_features": [
            "Page Object Model (POM) architecture ensuring maintainable, reusable, and readable UI test code.",
            "Cross-browser automated test execution running headless tests in parallel across Chrome, Firefox, and WebKit.",
            "Dynamic explicit wait strategy eliminating flaky test failures caused by asynchronous DOM rendering.",
            "Automated screenshot and video capture on test failures attached directly to test execution reports."
        ],
        "architecture_summary": "Playwright/Selenium test automation project following the Page Object Model pattern with isolated browser contexts and parallel test execution.",
        "database_design_summary": "Automated backend API setup hooks creating transient test user accounts prior to browser UI execution.",
        "api_design_summary": "Direct REST API fixtures priming application data state before running browser UI navigation steps.",
        "resume_bullet_templates": [
            "Engineered end-to-end browser test automation suite using Playwright and Python following the Page Object Model (POM) architectural pattern.",
            "Eliminated test flakiness by implementing robust dynamic element wait strategies, improving automated test reliability to 99%.",
            "Executed parallel cross-browser test suites across Chromium, Firefox, and WebKit, reducing full regression testing time by 70%."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Page Object Model (POM) design pattern", "Playwright cross-browser automation", "Flaky test diagnosis and dynamic waits"]
    },
    {
        "slug": "in-qa-healthcare-regression-hyderabad",
        "title": "Healthcare Booking Regression Framework",
        "fictional_company_name": "Madhapur HealthQA (Fictional)",
        "location_city": "Hyderabad",
        "location_state": "Telangana",
        "industry": "HealthTech & Medical QA",
        "target_job_roles": ["QA / Automation Engineer", "SDET", "Full Stack QA"],
        "difficulty_level": "Intermediate",
        "project_type": "Personal Portfolio Project",
        "description": "Integrated API and UI regression testing framework verifying outpatient clinic appointment scheduling, doctor availability calendars, and prescription document downloads.",
        "problem_statement": "Medical appointment platforms required comprehensive regression validation to guarantee patient appointments are never dropped or incorrectly rescheduled.",
        "technical_stack": ["JavaScript / TypeScript", "Cypress / Playwright", "Mochawesome", "Docker", "GitHub Actions"],
        "key_features": [
            "End-to-end patient booking journey automation from doctor search through time-slot selection to appointment confirmation.",
            "API mock interception and stubbing simulating server downtime and payment gateway error responses.",
            "Visual regression testing ensuring layout consistency across desktop and mobile viewport resolutions.",
            "Automated smoke and regression test suites executed automatically inside Docker containers in CI pipelines."
        ],
        "architecture_summary": "Cypress/Playwright end-to-end testing suite with custom commands, API network stubs, and Mochawesome reporting integration.",
        "database_design_summary": "Pre-test database seeding scripts setting up doctor schedules and clearing test patient appointments.",
        "api_design_summary": "Network interception stubs for: /api/doctors, /api/slots, /api/appointments/confirm.",
        "resume_bullet_templates": [
            "Developed integrated UI and API regression testing suite using Cypress, TypeScript, and Docker for a healthcare appointment platform.",
            "Automated 80+ patient appointment booking and doctor schedule regression scenarios, ensuring zero broken booking workflows in production.",
            "Implemented network request stubbing and visual viewport regression checks, validating error recovery behavior during payment gateway downtimes."
        ],
        "estimated_duration": "3 weeks",
        "learning_outcomes": ["Cypress/Playwright network request stubbing", "Visual regression and viewport testing", "Healthcare workflow quality assurance"]
    }
]

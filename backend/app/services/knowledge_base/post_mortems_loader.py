"""
Post-Mortems Knowledge Base Loader

Curated collection of ~50+ real-world incident post-mortems from major tech companies.
Used to provide incident response context to agents during analysis.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


POST_MORTEMS_DATA: List[Dict[str, Any]] = [
    # === GitHub ===
    {
        "post_mortem_id": "PM-001",
        "title": "GitHub October 2018 Incident",
        "content": "A routine database maintenance operation caused a network partition between a primary database cluster and its replicas. GitHub was degraded for 24 hours with data inconsistencies.",
        "company": "GitHub",
        "date": "2018-10-21",
        "duration": "24 hours",
        "affected_services": ["GitHub.com", "API", "Webhooks", "GitHub Pages"],
        "root_cause_category": "infrastructure",
        "impact_category": "major",
        "remediation_actions": ["Improved orchestration for database failover", "Added cross-region replication testing", "Enhanced monitoring for replication lag"],
        "tags": ["database", "network-partition", "failover"],
        "source_url": "https://github.blog/2018-10-30-oct21-post-incident-analysis/",
    },
    {
        "post_mortem_id": "PM-002",
        "title": "GitHub March 2023 Degraded Availability",
        "content": "Multiple GitHub services experienced degraded performance due to a configuration change that caused elevated database load. The change was intended to improve performance but had the opposite effect.",
        "company": "GitHub",
        "date": "2023-03-23",
        "duration": "3 hours",
        "affected_services": ["GitHub.com", "Actions", "Packages"],
        "root_cause_category": "config",
        "impact_category": "partial",
        "remediation_actions": ["Rolled back configuration change", "Added canary deployment for config changes", "Improved load testing"],
        "tags": ["configuration", "database", "performance"],
        "source_url": "https://www.githubstatus.com/incidents",
    },
    {
        "post_mortem_id": "PM-003",
        "title": "GitHub Actions Service Disruption 2022",
        "content": "GitHub Actions experienced a major outage when a database migration caused unexpected lock contention. CI/CD pipelines worldwide were affected.",
        "company": "GitHub",
        "date": "2022-03-15",
        "duration": "4 hours",
        "affected_services": ["GitHub Actions", "CI/CD pipelines"],
        "root_cause_category": "deployment",
        "impact_category": "major",
        "remediation_actions": ["Migration rollback procedures improved", "Added pre-migration lock analysis", "Implemented phased migration approach"],
        "tags": ["database-migration", "actions", "lock-contention"],
        "source_url": "https://www.githubstatus.com/incidents",
    },
    # === AWS ===
    {
        "post_mortem_id": "PM-004",
        "title": "AWS S3 US-EAST-1 Outage 2017",
        "content": "An authorized engineer executed a command to remove a small number of S3 subsystem servers but accidentally removed more servers than intended due to an input error. This caused a cascading failure across US-EAST-1.",
        "company": "AWS",
        "date": "2017-02-28",
        "duration": "4 hours",
        "affected_services": ["S3", "EC2 Console", "Lambda", "many dependent services"],
        "root_cause_category": "human",
        "impact_category": "complete",
        "remediation_actions": ["Added safeguards against removing too much capacity", "Modified recovery procedures", "Reduced recovery time for subsystems"],
        "tags": ["human-error", "cascading-failure", "capacity"],
        "source_url": "https://aws.amazon.com/message/41926/",
    },
    {
        "post_mortem_id": "PM-005",
        "title": "AWS US-EAST-1 Kinesis Outage 2020",
        "content": "A relatively small capacity addition to the Kinesis front-end fleet triggered a cascade of failures due to thread starvation in the server fleet, affecting multiple AWS services.",
        "company": "AWS",
        "date": "2020-11-25",
        "duration": "10 hours",
        "affected_services": ["Kinesis", "CloudWatch", "Lambda", "Cognito", "many others"],
        "root_cause_category": "scaling",
        "impact_category": "major",
        "remediation_actions": ["Increased thread limits", "Added fleet-size-aware scaling", "Decoupled dependent services"],
        "tags": ["thread-starvation", "cascading-failure", "scaling"],
        "source_url": "https://aws.amazon.com/message/11201/",
    },
    {
        "post_mortem_id": "PM-006",
        "title": "AWS DynamoDB Outage US-EAST-1 2015",
        "content": "DynamoDB experienced elevated error rates in US-EAST-1 due to a metadata service issue. The metadata partition table exceeded the capacity of the storage backend.",
        "company": "AWS",
        "date": "2015-09-20",
        "duration": "5 hours",
        "affected_services": ["DynamoDB", "dependent services"],
        "root_cause_category": "scaling",
        "impact_category": "partial",
        "remediation_actions": ["Increased metadata storage capacity", "Added monitoring for metadata growth", "Improved partition splitting"],
        "tags": ["metadata", "capacity", "dynamodb"],
        "source_url": "https://aws.amazon.com/message/5467D2/",
    },
    {
        "post_mortem_id": "PM-007",
        "title": "AWS Lambda Throttling Event 2023",
        "content": "Lambda functions in multiple regions experienced elevated throttling rates due to a control plane deployment that increased cold start times and reduced concurrent capacity.",
        "company": "AWS",
        "date": "2023-06-13",
        "duration": "2 hours",
        "affected_services": ["Lambda", "API Gateway", "Step Functions"],
        "root_cause_category": "deployment",
        "impact_category": "partial",
        "remediation_actions": ["Rolled back control plane change", "Added cold-start impact testing", "Improved capacity reservation"],
        "tags": ["lambda", "throttling", "cold-start", "deployment"],
        "source_url": "https://health.aws.amazon.com/health/status",
    },
    # === Google ===
    {
        "post_mortem_id": "PM-008",
        "title": "Google Cloud Networking Outage 2019",
        "content": "Google Cloud experienced a major networking outage affecting multiple services including YouTube, Gmail, Google Cloud, and Snapchat. A configuration change intended for a few servers was applied to a much larger number.",
        "company": "Google",
        "date": "2019-06-02",
        "duration": "4 hours",
        "affected_services": ["Google Cloud", "YouTube", "Gmail", "Snapchat", "Discord"],
        "root_cause_category": "config",
        "impact_category": "major",
        "remediation_actions": ["Improved change management for network configs", "Added blast-radius limits", "Enhanced canary deployment for network changes"],
        "tags": ["networking", "configuration", "blast-radius"],
        "source_url": "https://status.cloud.google.com/incident/cloud-networking/19009",
    },
    {
        "post_mortem_id": "PM-009",
        "title": "Google Cloud IAM Outage 2020",
        "content": "Google Cloud IAM authentication service experienced an outage due to a quota change that was applied incorrectly, causing auth failures across multiple Google Cloud services.",
        "company": "Google",
        "date": "2020-12-14",
        "duration": "47 minutes",
        "affected_services": ["Google Cloud IAM", "Gmail", "YouTube", "Google Workspace"],
        "root_cause_category": "config",
        "impact_category": "complete",
        "remediation_actions": ["Improved quota management system", "Added auth-specific monitoring", "Implemented progressive rollout for quota changes"],
        "tags": ["authentication", "quota", "identity"],
        "source_url": "https://status.cloud.google.com/incidents",
    },
    {
        "post_mortem_id": "PM-010",
        "title": "Google GCP Load Balancer Outage 2022",
        "content": "Google Cloud's global load balancer experienced a configuration error that caused traffic routing failures for multiple customers, affecting application availability.",
        "company": "Google",
        "date": "2022-11-16",
        "duration": "2 hours",
        "affected_services": ["Cloud Load Balancing", "GKE", "Cloud Run"],
        "root_cause_category": "config",
        "impact_category": "partial",
        "remediation_actions": ["Enhanced config validation", "Added pre-deployment simulation", "Improved rollback automation"],
        "tags": ["load-balancer", "routing", "configuration"],
        "source_url": "https://status.cloud.google.com/incidents",
    },
    # === Facebook/Meta ===
    {
        "post_mortem_id": "PM-011",
        "title": "Facebook Global Outage October 2021",
        "content": "Facebook, Instagram, WhatsApp, and Messenger went down globally for approximately 6 hours. A BGP configuration change to backbone routers disconnected Facebook's data centers from the internet.",
        "company": "Facebook",
        "date": "2021-10-04",
        "duration": "6 hours",
        "affected_services": ["Facebook", "Instagram", "WhatsApp", "Messenger"],
        "root_cause_category": "config",
        "impact_category": "complete",
        "remediation_actions": ["Improved out-of-band access", "Added BGP change safeguards", "Enhanced physical access procedures"],
        "tags": ["bgp", "dns", "total-outage", "networking"],
        "source_url": "https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/",
    },
    {
        "post_mortem_id": "PM-012",
        "title": "Facebook Newsfeed Outage 2019",
        "content": "Facebook experienced a 14-hour outage affecting the News Feed, Instagram, and WhatsApp due to a server configuration change that triggered a cascading failure.",
        "company": "Facebook",
        "date": "2019-03-13",
        "duration": "14 hours",
        "affected_services": ["Facebook", "Instagram", "WhatsApp"],
        "root_cause_category": "config",
        "impact_category": "major",
        "remediation_actions": ["Improved configuration testing", "Added canary deployments", "Enhanced rollback procedures"],
        "tags": ["configuration", "cascading-failure", "social-media"],
        "source_url": "https://about.fb.com/news/",
    },
    # === Cloudflare ===
    {
        "post_mortem_id": "PM-013",
        "title": "Cloudflare Regex Outage July 2019",
        "content": "A bad regular expression in a WAF rule caused CPU exhaustion across Cloudflare's entire edge network, resulting in 502 errors for approximately 27 minutes.",
        "company": "Cloudflare",
        "date": "2019-07-02",
        "duration": "27 minutes",
        "affected_services": ["Cloudflare CDN", "WAF", "all proxied websites"],
        "root_cause_category": "code",
        "impact_category": "complete",
        "remediation_actions": ["Added regex complexity analysis", "Implemented staged WAF deployments", "Added CPU usage circuit breakers"],
        "tags": ["regex", "cpu-exhaustion", "waf", "global-outage"],
        "source_url": "https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/",
    },
    {
        "post_mortem_id": "PM-014",
        "title": "Cloudflare DNS Outage 2020",
        "content": "Cloudflare's DNS service experienced degraded performance due to a router failure in one of their core data centers, causing routing loops and packet loss.",
        "company": "Cloudflare",
        "date": "2020-07-17",
        "duration": "27 minutes",
        "affected_services": ["Cloudflare DNS", "CDN", "Workers"],
        "root_cause_category": "infrastructure",
        "impact_category": "partial",
        "remediation_actions": ["Improved router failover", "Added routing loop detection", "Enhanced network redundancy"],
        "tags": ["dns", "routing", "infrastructure"],
        "source_url": "https://blog.cloudflare.com/cloudflare-outage-on-july-17-2020/",
    },
    {
        "post_mortem_id": "PM-015",
        "title": "Cloudflare Workers KV Outage 2023",
        "content": "Cloudflare Workers KV experienced elevated error rates due to a deployment that introduced a regression in the storage backend, affecting serverless applications.",
        "company": "Cloudflare",
        "date": "2023-04-04",
        "duration": "1 hour",
        "affected_services": ["Workers KV", "Workers", "Pages"],
        "root_cause_category": "deployment",
        "impact_category": "partial",
        "remediation_actions": ["Improved KV regression testing", "Added gradual rollout", "Enhanced storage backend monitoring"],
        "tags": ["workers-kv", "deployment", "regression"],
        "source_url": "https://www.cloudflarestatus.com/incidents",
    },
    # === Fastly ===
    {
        "post_mortem_id": "PM-016",
        "title": "Fastly Global CDN Outage June 2021",
        "content": "A customer configuration change triggered a latent software bug in Fastly's VCL configuration, causing 85% of the Fastly network to return 503 errors for major websites.",
        "company": "Fastly",
        "date": "2021-06-08",
        "duration": "49 minutes",
        "affected_services": ["CDN", "Amazon.com", "Reddit", "NYT", "UK Gov"],
        "root_cause_category": "code",
        "impact_category": "complete",
        "remediation_actions": ["Fixed latent bug", "Added config validation", "Improved testing for edge cases"],
        "tags": ["cdn", "latent-bug", "configuration-trigger"],
        "source_url": "https://www.fastly.com/blog/summary-of-june-8-outage",
    },
    # === Stripe ===
    {
        "post_mortem_id": "PM-017",
        "title": "Stripe API Degradation 2019",
        "content": "Stripe experienced elevated API error rates due to a database migration that caused increased latency. Payment processing was degraded for multiple hours.",
        "company": "Stripe",
        "date": "2019-07-10",
        "duration": "2 hours",
        "affected_services": ["Stripe API", "Payment processing", "Dashboard"],
        "root_cause_category": "deployment",
        "impact_category": "partial",
        "remediation_actions": ["Improved migration tooling", "Added latency-aware circuit breakers", "Enhanced database health checks"],
        "tags": ["payment", "database-migration", "latency"],
        "source_url": "https://stripe.com/blog/operating-stripe",
    },
    {
        "post_mortem_id": "PM-018",
        "title": "Stripe Dashboard Outage 2022",
        "content": "The Stripe Dashboard became unavailable due to a frontend deployment that introduced a JavaScript error causing the application to fail to load for all users.",
        "company": "Stripe",
        "date": "2022-08-11",
        "duration": "45 minutes",
        "affected_services": ["Stripe Dashboard"],
        "root_cause_category": "deployment",
        "impact_category": "partial",
        "remediation_actions": ["Added E2E smoke tests pre-deploy", "Improved canary analysis", "Added client-side error monitoring threshold"],
        "tags": ["frontend", "deployment", "javascript"],
        "source_url": "https://status.stripe.com/incidents",
    },
    # === Slack ===
    {
        "post_mortem_id": "PM-019",
        "title": "Slack Outage January 2021",
        "content": "Slack experienced a major outage on the first Monday after New Year's when returning users triggered a surge in authentication and connection requests that overwhelmed the infrastructure.",
        "company": "Slack",
        "date": "2021-01-04",
        "duration": "3 hours",
        "affected_services": ["Slack messaging", "File sharing", "Channels"],
        "root_cause_category": "scaling",
        "impact_category": "major",
        "remediation_actions": ["Increased capacity headroom", "Added connection rate limiting", "Improved load shedding"],
        "tags": ["scaling", "thundering-herd", "authentication"],
        "source_url": "https://slack.engineering/",
    },
    {
        "post_mortem_id": "PM-020",
        "title": "Slack Database Connectivity Issues 2023",
        "content": "Slack experienced intermittent message delivery failures due to database connection pool exhaustion caused by a slow query introduced in a recent deployment.",
        "company": "Slack",
        "date": "2023-02-22",
        "duration": "90 minutes",
        "affected_services": ["Messaging", "Search", "Notifications"],
        "root_cause_category": "code",
        "impact_category": "partial",
        "remediation_actions": ["Query optimization", "Connection pool monitoring", "Slow query alerts"],
        "tags": ["database", "connection-pool", "slow-query"],
        "source_url": "https://status.slack.com/incidents",
    },
    # === Spotify ===
    {
        "post_mortem_id": "PM-021",
        "title": "Spotify Global Outage 2022",
        "content": "Spotify experienced a global outage affecting all platforms due to a backend deployment that introduced a bug in the authentication flow.",
        "company": "Spotify",
        "date": "2022-03-08",
        "duration": "1 hour",
        "affected_services": ["Spotify apps", "Web player", "API"],
        "root_cause_category": "deployment",
        "impact_category": "complete",
        "remediation_actions": ["Enhanced auth flow testing", "Improved deployment canary", "Added auth-specific health checks"],
        "tags": ["authentication", "deployment", "global-outage"],
        "source_url": "https://engineering.atspotify.com/",
    },
    # === Roblox ===
    {
        "post_mortem_id": "PM-022",
        "title": "Roblox 73-Hour Outage October 2021",
        "content": "Roblox experienced a 73-hour outage caused by a combination of Consul cluster issues and a HashiCorp streaming bug. The longest outage in the company's history.",
        "company": "Roblox",
        "date": "2021-10-28",
        "duration": "73 hours",
        "affected_services": ["All Roblox services", "Games", "Avatar shop"],
        "root_cause_category": "infrastructure",
        "impact_category": "complete",
        "remediation_actions": ["Upgraded Consul clusters", "Added BoltDB compaction monitoring", "Improved service mesh resilience"],
        "tags": ["consul", "service-mesh", "extended-outage"],
        "source_url": "https://blog.roblox.com/2022/01/roblox-return-to-service-10-28-10-31-2021/",
    },
    # === Atlassian ===
    {
        "post_mortem_id": "PM-023",
        "title": "Atlassian April 2022 Multi-Week Outage",
        "content": "Atlassian accidentally deleted customer data for ~775 customers when a maintenance script used incorrect identifiers, causing a multi-week outage while data was restored from backups.",
        "company": "Atlassian",
        "date": "2022-04-05",
        "duration": "14 days",
        "affected_services": ["Jira", "Confluence", "Jira Service Management"],
        "root_cause_category": "human",
        "impact_category": "complete",
        "remediation_actions": ["Improved deletion safeguards", "Added dry-run for maintenance scripts", "Enhanced backup restoration procedures"],
        "tags": ["data-deletion", "human-error", "backup-restoration"],
        "source_url": "https://www.atlassian.com/engineering/post-incident-review-april-2022-outage",
    },
    # === Twitter/X ===
    {
        "post_mortem_id": "PM-024",
        "title": "Twitter Rate Limiting Incident 2023",
        "content": "Twitter implemented aggressive rate limiting that prevented many users from viewing tweets, initially described as addressing 'data scraping'. The limits were lower than normal usage patterns.",
        "company": "Twitter",
        "date": "2023-07-01",
        "duration": "48 hours",
        "affected_services": ["Twitter/X timeline", "Search", "API"],
        "root_cause_category": "config",
        "impact_category": "major",
        "remediation_actions": ["Adjusted rate limits upward", "Improved rate limit granularity", "Added user-tier differentiation"],
        "tags": ["rate-limiting", "configuration", "user-impact"],
        "source_url": "https://status.twitterstat.us/incidents",
    },
    # === Datadog ===
    {
        "post_mortem_id": "PM-025",
        "title": "Datadog March 2023 Outage",
        "content": "Datadog experienced a major outage affecting its monitoring platform, ironically leaving customers unable to monitor their own infrastructure during the incident.",
        "company": "Datadog",
        "date": "2023-03-08",
        "duration": "6 hours",
        "affected_services": ["Monitoring", "Dashboards", "Alerting", "Log Management"],
        "root_cause_category": "infrastructure",
        "impact_category": "major",
        "remediation_actions": ["Improved infrastructure redundancy", "Added independent monitoring for monitoring", "Enhanced failover procedures"],
        "tags": ["monitoring", "meta-outage", "infrastructure"],
        "source_url": "https://status.datadoghq.com/incidents",
    },
    # === Discord ===
    {
        "post_mortem_id": "PM-026",
        "title": "Discord Message Sending Outage 2022",
        "content": "Discord users were unable to send messages for several hours due to a Cassandra cluster issue caused by a garbage collection storm after a routine maintenance operation.",
        "company": "Discord",
        "date": "2022-03-07",
        "duration": "3 hours",
        "affected_services": ["Message sending", "Voice channels", "Bot API"],
        "root_cause_category": "infrastructure",
        "impact_category": "major",
        "remediation_actions": ["Tuned GC parameters", "Added GC monitoring", "Improved maintenance scheduling"],
        "tags": ["cassandra", "garbage-collection", "messaging"],
        "source_url": "https://discord.com/blog",
    },
    # === Heroku ===
    {
        "post_mortem_id": "PM-027",
        "title": "Heroku OAuth Token Breach 2022",
        "content": "Attackers accessed Heroku's GitHub integration OAuth tokens, downloading private repos of Heroku customers. Required mass revocation of all OAuth tokens.",
        "company": "Heroku",
        "date": "2022-04-15",
        "duration": "30 days investigation",
        "affected_services": ["GitHub Integration", "Heroku Dashboard", "Review Apps"],
        "root_cause_category": "dependency",
        "impact_category": "major",
        "remediation_actions": ["Revoked all OAuth tokens", "Rotated credentials", "Enhanced token storage security", "Improved audit logging"],
        "tags": ["security-breach", "oauth", "supply-chain"],
        "source_url": "https://status.heroku.com/incidents",
    },
    # === Okta ===
    {
        "post_mortem_id": "PM-028",
        "title": "Okta LAPSUS$ Breach 2022",
        "content": "The LAPSUS$ hacking group gained access to an Okta support engineer's workstation through a third-party contractor, potentially affecting up to 366 Okta customers.",
        "company": "Okta",
        "date": "2022-01-21",
        "duration": "5 days access window",
        "affected_services": ["Okta Support Portal", "Customer tenants"],
        "root_cause_category": "human",
        "impact_category": "partial",
        "remediation_actions": ["Terminated contractor relationship", "Enhanced MFA requirements", "Reduced support access privileges", "Improved third-party security requirements"],
        "tags": ["security-breach", "third-party", "identity"],
        "source_url": "https://www.okta.com/blog/2022/03/updated-okta-statement-on-lapsus/",
    },
    # === GitLab ===
    {
        "post_mortem_id": "PM-029",
        "title": "GitLab Database Deletion 2017",
        "content": "A GitLab engineer accidentally deleted the production database while attempting to fix replication lag. Five backup methods were tested, and none worked correctly.",
        "company": "GitLab",
        "date": "2017-01-31",
        "duration": "18 hours",
        "affected_services": ["GitLab.com", "CI/CD", "Container Registry"],
        "root_cause_category": "human",
        "impact_category": "complete",
        "remediation_actions": ["Improved backup verification", "Added production database safeguards", "Regular backup restoration drills", "Livestreamed the recovery (radical transparency)"],
        "tags": ["database-deletion", "backup-failure", "human-error"],
        "source_url": "https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/",
    },
    # === Zoom ===
    {
        "post_mortem_id": "PM-030",
        "title": "Zoom Outage August 2020",
        "content": "Zoom experienced a major outage on the first day of school for many US districts, when a DNS configuration change caused service disruption during peak usage.",
        "company": "Zoom",
        "date": "2020-08-24",
        "duration": "5 hours",
        "affected_services": ["Zoom Meetings", "Zoom Phone", "Webinars"],
        "root_cause_category": "config",
        "impact_category": "complete",
        "remediation_actions": ["Improved DNS change management", "Added capacity for peak events", "Enhanced config deployment safeguards"],
        "tags": ["dns", "configuration", "peak-traffic"],
        "source_url": "https://status.zoom.us/incidents",
    },
    # === Twilio ===
    {
        "post_mortem_id": "PM-031",
        "title": "Twilio SendGrid Email Delivery Delays 2023",
        "content": "Twilio SendGrid experienced significant email delivery delays due to a sudden increase in spam traffic that overwhelmed queue processing, causing legitimate emails to be delayed.",
        "company": "Twilio",
        "date": "2023-01-18",
        "duration": "8 hours",
        "affected_services": ["SendGrid Email API", "Marketing Campaigns"],
        "root_cause_category": "scaling",
        "impact_category": "partial",
        "remediation_actions": ["Improved spam detection at ingestion", "Added queue priority lanes", "Enhanced capacity auto-scaling"],
        "tags": ["email", "queue", "spam", "scaling"],
        "source_url": "https://status.sendgrid.com/incidents",
    },
    # === MongoDB Atlas ===
    {
        "post_mortem_id": "PM-032",
        "title": "MongoDB Atlas Connectivity Issues 2022",
        "content": "MongoDB Atlas customers experienced connectivity issues when a cloud provider networking change affected the overlay network used by Atlas clusters.",
        "company": "MongoDB",
        "date": "2022-06-15",
        "duration": "3 hours",
        "affected_services": ["MongoDB Atlas", "Database connections"],
        "root_cause_category": "dependency",
        "impact_category": "partial",
        "remediation_actions": ["Added network health monitoring", "Improved dependency isolation", "Enhanced failover for network changes"],
        "tags": ["database", "networking", "cloud-dependency"],
        "source_url": "https://status.cloud.mongodb.com/incidents",
    },
    # === Salesforce ===
    {
        "post_mortem_id": "PM-033",
        "title": "Salesforce DNS Outage 2019",
        "content": "Salesforce experienced a major outage when a database script inadvertently gave all users 'modify all' permissions. The company shut down production to prevent data leakage.",
        "company": "Salesforce",
        "date": "2019-05-17",
        "duration": "15 hours",
        "affected_services": ["Salesforce CRM", "Service Cloud", "Pardot"],
        "root_cause_category": "deployment",
        "impact_category": "complete",
        "remediation_actions": ["Improved permission deployment safeguards", "Added permission change auditing", "Enhanced staging environment validation"],
        "tags": ["permissions", "security", "deployment"],
        "source_url": "https://status.salesforce.com/incidents",
    },
    # === Cloudflare additional ===
    {
        "post_mortem_id": "PM-034",
        "title": "Cloudflare Backbone Outage 2020",
        "content": "Multiple Cloudflare data centers became unreachable due to a configuration error in the backbone network routers during a routine maintenance window.",
        "company": "Cloudflare",
        "date": "2020-08-30",
        "duration": "30 minutes",
        "affected_services": ["CDN", "Workers", "Access"],
        "root_cause_category": "config",
        "impact_category": "partial",
        "remediation_actions": ["Improved backbone config validation", "Added automated rollback", "Enhanced maintenance procedures"],
        "tags": ["backbone", "configuration", "networking"],
        "source_url": "https://blog.cloudflare.com/",
    },
    # === Reddit ===
    {
        "post_mortem_id": "PM-035",
        "title": "Reddit Infrastructure Outage 2023",
        "content": "Reddit experienced a prolonged outage due to a Kubernetes upgrade that went wrong, causing pods to fail to schedule and cascading across the infrastructure.",
        "company": "Reddit",
        "date": "2023-06-12",
        "duration": "3 hours",
        "affected_services": ["Reddit.com", "Mobile app", "API"],
        "root_cause_category": "deployment",
        "impact_category": "complete",
        "remediation_actions": ["Improved K8s upgrade procedures", "Added pod scheduling monitoring", "Enhanced rollback automation"],
        "tags": ["kubernetes", "deployment", "scheduling"],
        "source_url": "https://www.redditstatus.com/incidents",
    },
    # === PagerDuty ===
    {
        "post_mortem_id": "PM-036",
        "title": "PagerDuty Alert Delivery Delays 2023",
        "content": "PagerDuty experienced delays in alert delivery due to a sudden spike in alert volume from a large customer that saturated the notification pipeline.",
        "company": "PagerDuty",
        "date": "2023-09-15",
        "duration": "2 hours",
        "affected_services": ["Alert delivery", "Notifications", "Escalations"],
        "root_cause_category": "scaling",
        "impact_category": "partial",
        "remediation_actions": ["Added per-customer rate limiting", "Improved queue isolation", "Enhanced auto-scaling thresholds"],
        "tags": ["alerting", "queue-saturation", "scaling"],
        "source_url": "https://status.pagerduty.com/incidents",
    },
    # === Netlify ===
    {
        "post_mortem_id": "PM-037",
        "title": "Netlify Build Service Outage 2022",
        "content": "Netlify's build service experienced an outage when a dependency update caused build workers to crash on startup, preventing all new deployments.",
        "company": "Netlify",
        "date": "2022-07-19",
        "duration": "2 hours",
        "affected_services": ["Build service", "Deploy previews", "CI/CD"],
        "root_cause_category": "dependency",
        "impact_category": "partial",
        "remediation_actions": ["Pinned dependency versions", "Added build worker health checks", "Improved dependency update testing"],
        "tags": ["build", "dependency", "crash"],
        "source_url": "https://www.netlifystatus.com/incidents",
    },
    # === Vercel ===
    {
        "post_mortem_id": "PM-038",
        "title": "Vercel Edge Function Errors 2023",
        "content": "Vercel Edge Functions experienced elevated error rates due to a runtime update that introduced a memory leak, causing functions to fail after sustained traffic.",
        "company": "Vercel",
        "date": "2023-05-22",
        "duration": "4 hours",
        "affected_services": ["Edge Functions", "Middleware", "API Routes"],
        "root_cause_category": "code",
        "impact_category": "partial",
        "remediation_actions": ["Fixed memory leak", "Added memory monitoring", "Improved runtime testing under load"],
        "tags": ["edge-functions", "memory-leak", "runtime"],
        "source_url": "https://www.vercel-status.com/incidents",
    },
    # === DigitalOcean ===
    {
        "post_mortem_id": "PM-039",
        "title": "DigitalOcean Droplet Connectivity 2022",
        "content": "DigitalOcean droplets in NYC1 region experienced connectivity issues due to a hypervisor firmware update that caused network interface resets.",
        "company": "DigitalOcean",
        "date": "2022-10-04",
        "duration": "90 minutes",
        "affected_services": ["Droplets", "Managed Databases", "Kubernetes"],
        "root_cause_category": "infrastructure",
        "impact_category": "partial",
        "remediation_actions": ["Improved firmware testing", "Added network interface monitoring", "Phased firmware rollouts"],
        "tags": ["hypervisor", "firmware", "connectivity"],
        "source_url": "https://status.digitalocean.com/incidents",
    },
    # === CircleCI ===
    {
        "post_mortem_id": "PM-040",
        "title": "CircleCI Security Incident January 2023",
        "content": "CircleCI disclosed a security incident where an attacker compromised an engineer's laptop and exfiltrated customer secrets stored in the CI/CD platform.",
        "company": "CircleCI",
        "date": "2023-01-04",
        "duration": "14 days investigation",
        "affected_services": ["CI/CD platform", "Secret storage"],
        "root_cause_category": "human",
        "impact_category": "major",
        "remediation_actions": ["Rotated all customer secrets", "Enhanced endpoint security", "Improved secret encryption at rest", "Added anomaly detection"],
        "tags": ["security-breach", "secrets", "supply-chain"],
        "source_url": "https://circleci.com/blog/jan-4-2023-incident-report/",
    },
    # === Coinbase ===
    {
        "post_mortem_id": "PM-041",
        "title": "Coinbase Trading Outage 2021",
        "content": "Coinbase experienced a major outage during a Bitcoin price surge when traffic exceeded capacity. Users were unable to trade during a volatile market period.",
        "company": "Coinbase",
        "date": "2021-02-23",
        "duration": "2 hours",
        "affected_services": ["Trading", "Portfolio", "API"],
        "root_cause_category": "scaling",
        "impact_category": "major",
        "remediation_actions": ["Increased capacity headroom", "Improved auto-scaling speed", "Added load shedding for non-critical features"],
        "tags": ["trading", "scaling", "peak-traffic"],
        "source_url": "https://blog.coinbase.com/",
    },
    # === npm ===
    {
        "post_mortem_id": "PM-042",
        "title": "npm Registry Outage 2022",
        "content": "The npm registry experienced elevated error rates when a database migration caused index rebuilding, significantly increasing response times for package metadata queries.",
        "company": "npm/GitHub",
        "date": "2022-11-30",
        "duration": "4 hours",
        "affected_services": ["npm registry", "package installs", "CI/CD pipelines"],
        "root_cause_category": "deployment",
        "impact_category": "partial",
        "remediation_actions": ["Improved migration testing", "Added index rebuild monitoring", "Implemented read replicas for metadata"],
        "tags": ["registry", "database-migration", "package-management"],
        "source_url": "https://status.npmjs.org/incidents",
    },
    # === Shopify ===
    {
        "post_mortem_id": "PM-043",
        "title": "Shopify Checkout Outage Black Friday 2021",
        "content": "Shopify's checkout service experienced degraded performance during Black Friday due to a caching layer that failed under the extreme traffic spike.",
        "company": "Shopify",
        "date": "2021-11-26",
        "duration": "30 minutes",
        "affected_services": ["Checkout", "Payments", "Cart"],
        "root_cause_category": "scaling",
        "impact_category": "partial",
        "remediation_actions": ["Upgraded caching infrastructure", "Added cache fallback strategies", "Improved load testing for peak events"],
        "tags": ["checkout", "caching", "black-friday", "scaling"],
        "source_url": "https://status.shopify.com/incidents",
    },
    # === Elastic ===
    {
        "post_mortem_id": "PM-044",
        "title": "Elastic Cloud Cluster Unavailability 2023",
        "content": "Elastic Cloud clusters in the AWS EU region became temporarily unavailable when a control plane deployment caused cluster management operations to fail.",
        "company": "Elastic",
        "date": "2023-07-20",
        "duration": "2 hours",
        "affected_services": ["Elastic Cloud", "Elasticsearch", "Kibana"],
        "root_cause_category": "deployment",
        "impact_category": "partial",
        "remediation_actions": ["Improved control plane deployment process", "Added cluster health pre-checks", "Enhanced deployment rollback"],
        "tags": ["elasticsearch", "control-plane", "deployment"],
        "source_url": "https://status.elastic.co/incidents",
    },
    # === Notion ===
    {
        "post_mortem_id": "PM-045",
        "title": "Notion Outage February 2023",
        "content": "Notion experienced a major outage when a database query plan change caused dramatically increased load on the primary database, leading to cascading failures.",
        "company": "Notion",
        "date": "2023-02-09",
        "duration": "4 hours",
        "affected_services": ["Notion app", "API", "Integrations"],
        "root_cause_category": "code",
        "impact_category": "complete",
        "remediation_actions": ["Improved query plan monitoring", "Added query timeout enforcement", "Enhanced database capacity planning"],
        "tags": ["database", "query-plan", "cascading-failure"],
        "source_url": "https://status.notion.so/incidents",
    },
    # === Travis CI ===
    {
        "post_mortem_id": "PM-046",
        "title": "Travis CI Secret Exposure 2021",
        "content": "A vulnerability in Travis CI exposed secrets from public repositories' build logs, potentially affecting thousands of open source projects.",
        "company": "Travis CI",
        "date": "2021-09-15",
        "duration": "10 days until patched",
        "affected_services": ["CI/CD builds", "Secret management"],
        "root_cause_category": "code",
        "impact_category": "major",
        "remediation_actions": ["Patched secret exposure", "Rotated affected secrets", "Improved secret masking in logs", "Enhanced security review process"],
        "tags": ["security", "secret-exposure", "ci-cd"],
        "source_url": "https://www.traviscistatus.com/incidents",
    },
    # === Lyft ===
    {
        "post_mortem_id": "PM-047",
        "title": "Lyft Envoy Proxy Configuration Error 2020",
        "content": "Lyft experienced a service mesh outage when a misconfigured Envoy proxy update caused all sidecar proxies to reject traffic simultaneously.",
        "company": "Lyft",
        "date": "2020-03-12",
        "duration": "45 minutes",
        "affected_services": ["Ride matching", "Driver app", "Payments"],
        "root_cause_category": "config",
        "impact_category": "major",
        "remediation_actions": ["Added Envoy config validation", "Implemented canary for mesh configs", "Enhanced service mesh monitoring"],
        "tags": ["envoy", "service-mesh", "configuration"],
        "source_url": "https://eng.lyft.com/",
    },
    # === Twitch ===
    {
        "post_mortem_id": "PM-048",
        "title": "Twitch Source Code Leak 2021",
        "content": "Twitch's entire source code, internal tools, and creator payout data were leaked due to a server misconfiguration that exposed an internal Git repository.",
        "company": "Twitch",
        "date": "2021-10-06",
        "duration": "Ongoing impact after leak",
        "affected_services": ["Source code", "Internal tools", "Creator payments data"],
        "root_cause_category": "config",
        "impact_category": "major",
        "remediation_actions": ["Secured server configurations", "Rotated all credentials", "Enhanced access controls", "Improved network segmentation"],
        "tags": ["data-breach", "misconfiguration", "source-code-leak"],
        "source_url": "https://blog.twitch.tv/en/2021/10/06/updates-on-the-twitch-security-incident/",
    },
    # === Grafana ===
    {
        "post_mortem_id": "PM-049",
        "title": "Grafana Cloud Ingestion Outage 2023",
        "content": "Grafana Cloud's metrics ingestion pipeline experienced an outage when a schema migration on the write path caused a brief period of data loss and delayed ingestion.",
        "company": "Grafana",
        "date": "2023-08-14",
        "duration": "3 hours",
        "affected_services": ["Metrics ingestion", "Alerting", "Dashboards"],
        "root_cause_category": "deployment",
        "impact_category": "partial",
        "remediation_actions": ["Improved schema migration process", "Added write-path redundancy", "Enhanced data durability checks"],
        "tags": ["metrics", "ingestion", "schema-migration"],
        "source_url": "https://status.grafana.com/incidents",
    },
    # === Linear ===
    {
        "post_mortem_id": "PM-050",
        "title": "Linear Sync Service Disruption 2023",
        "content": "Linear's real-time sync service experienced disruption when a WebSocket server update caused connection storms as all clients attempted to reconnect simultaneously.",
        "company": "Linear",
        "date": "2023-04-18",
        "duration": "1 hour",
        "affected_services": ["Real-time sync", "Issue tracking", "Notifications"],
        "root_cause_category": "deployment",
        "impact_category": "partial",
        "remediation_actions": ["Added jittered reconnection", "Improved WebSocket server health checks", "Enhanced gradual deployment for stateful services"],
        "tags": ["websocket", "reconnection-storm", "real-time"],
        "source_url": "https://status.linear.app/incidents",
    },
    # === Additional post-mortems for diversity ===
    {
        "post_mortem_id": "PM-051",
        "title": "Azure DNS Global Outage 2023",
        "content": "Microsoft Azure experienced a global DNS resolution failure that affected multiple Azure services and customer applications for over an hour.",
        "company": "Microsoft",
        "date": "2023-01-25",
        "duration": "90 minutes",
        "affected_services": ["Azure DNS", "Azure Portal", "Azure DevOps"],
        "root_cause_category": "infrastructure",
        "impact_category": "complete",
        "remediation_actions": ["Improved DNS infrastructure redundancy", "Added DNS health monitoring", "Enhanced failover automation"],
        "tags": ["dns", "azure", "global-outage"],
        "source_url": "https://status.azure.com/en-us/status/history/",
    },
    {
        "post_mortem_id": "PM-052",
        "title": "Dropbox Authentication Outage 2019",
        "content": "Dropbox users were unable to authenticate for several hours due to a certificate rotation that was applied to production before being properly validated.",
        "company": "Dropbox",
        "date": "2019-06-19",
        "duration": "3 hours",
        "affected_services": ["Authentication", "File sync", "Web interface"],
        "root_cause_category": "config",
        "impact_category": "complete",
        "remediation_actions": ["Improved certificate rotation procedures", "Added certificate validation checks", "Enhanced auth monitoring"],
        "tags": ["authentication", "certificate", "rotation"],
        "source_url": "https://status.dropbox.com/incidents",
    },
]


class PostMortemsLoader:
    """Loads post-mortem data into ChromaDB for vector search."""

    COLLECTION_NAME = "post_mortems"

    def __init__(self, chroma_service):
        self.chroma_service = chroma_service

    def load_all(self) -> Dict[str, Any]:
        """Load all post-mortems into ChromaDB. Returns stats."""
        loaded = 0
        errors = []
        categories = {}
        companies = set()

        for pm in POST_MORTEMS_DATA:
            try:
                self.load_post_mortem(pm)
                loaded += 1
                cat = pm["root_cause_category"]
                categories[cat] = categories.get(cat, 0) + 1
                companies.add(pm["company"])
            except Exception as e:
                errors.append({"post_mortem_id": pm["post_mortem_id"], "error": str(e)})

        return {
            "loaded": loaded,
            "errors": len(errors),
            "error_details": errors,
            "root_cause_categories": categories,
            "companies": sorted(companies),
            "total_available": len(POST_MORTEMS_DATA),
        }

    def load_post_mortem(self, pm_data: Dict[str, Any]) -> str:
        """Load a single post-mortem into ChromaDB. Returns the post_mortem_id."""
        doc_text = (
            f"{pm_data['title']} ({pm_data['company']}, {pm_data['date']})\n"
            f"Duration: {pm_data['duration']}\n"
            f"Content: {pm_data['content']}\n"
            f"Root Cause Category: {pm_data['root_cause_category']}\n"
            f"Impact: {pm_data['impact_category']}\n"
            f"Affected Services: {', '.join(pm_data['affected_services'])}\n"
            f"Remediation: {'; '.join(pm_data['remediation_actions'])}\n"
            f"Tags: {', '.join(pm_data['tags'])}"
        )

        metadata = {
            "post_mortem_id": pm_data["post_mortem_id"],
            "title": pm_data["title"],
            "company": pm_data["company"],
            "date": pm_data["date"],
            "duration": pm_data["duration"],
            "root_cause_category": pm_data["root_cause_category"],
            "impact_category": pm_data["impact_category"],
            "tags": ",".join(pm_data["tags"]),
            "source": "post_mortems",
        }

        self.chroma_service.add_document(
            collection_name=self.COLLECTION_NAME,
            document_id=pm_data["post_mortem_id"],
            text=doc_text,
            metadata=metadata,
        )

        return pm_data["post_mortem_id"]

    def get_load_status(self) -> Dict[str, Any]:
        """Get current load status of the collection."""
        try:
            count = self.chroma_service.get_collection_count(self.COLLECTION_NAME)
        except Exception:
            count = 0

        categories = {}
        companies = set()
        for pm in POST_MORTEMS_DATA:
            cat = pm["root_cause_category"]
            categories[cat] = categories.get(cat, 0) + 1
            companies.add(pm["company"])

        return {
            "collection": self.COLLECTION_NAME,
            "loaded_count": count,
            "available_count": len(POST_MORTEMS_DATA),
            "root_cause_categories": categories,
            "companies": sorted(companies),
        }

    def clear_collection(self) -> None:
        """Clear the post-mortems collection."""
        self.chroma_service.delete_collection(self.COLLECTION_NAME)

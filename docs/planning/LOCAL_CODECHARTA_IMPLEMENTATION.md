# Local CodeCharta Implementation Plan

**Status**: PLANNED
**Target Week**: Week 146-147 (Fase 29)
**Priority**: P2 - Enhancement
**Estimated Effort**: 2-3 dagen

---

## 1. Overview

CodeCharta is een open-source visualisatietool die code metrics transformeert naar interactieve 3D stadskaarten. Dit plan beschrijft hoe we CodeCharta lokaal kunnen draaien voor volledig privacy-behoud.

### Key Benefits
- **Privacy**: Alle analyse en visualisatie gebeurt lokaal, geen data naar externe services
- **Offline**: Werkt zonder internet na initiële setup
- **Integratie**: Direct koppelbaar met MarQed AI Platform

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CODECHARTA LOCAL DEPLOYMENT                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  MARQED AI PLATFORM (Backend)                                            ││
│  │  ┌─────────────────────┐    ┌─────────────────────┐                      ││
│  │  │ CodeCharta API      │───►│ CodeCharta Exporter │                      ││
│  │  │ /api/codecharta/*   │    │ Service             │                      ││
│  │  └─────────────────────┘    └──────────┬──────────┘                      ││
│  │                                        │ .cc.json                        ││
│  └────────────────────────────────────────┼─────────────────────────────────┘│
│                                           │                                  │
│  ┌────────────────────────────────────────▼─────────────────────────────────┐│
│  │  CODECHARTA LOCAL (Docker)                                                ││
│  │  ┌─────────────────────────┐    ┌─────────────────────────┐              ││
│  │  │ codecharta-analysis     │    │ codecharta-visualization│              ││
│  │  │ Port: 9001              │    │ Port: 9000              │              ││
│  │  │                         │    │                         │              ││
│  │  │ • ccsh CLI              │    │ • Web Studio            │              ││
│  │  │ • unifiedparser         │    │ • 3D city maps          │              ││
│  │  │ • sonarimport           │    │ • Delta tracking        │              ││
│  │  │ • gitlogparser          │    │ • Export to 3D print    │              ││
│  │  └─────────────────────────┘    └─────────────────────────┘              ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────┐│
│  │  SHARED VOLUME: ./codecharta-exports                                      ││
│  │  └── *.cc.json.gz (analysis output)                                       ││
│  └──────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. System Requirements

### Minimum Requirements
| Component | Requirement |
|-----------|-------------|
| Node.js | >= 20 |
| Java | >= 11 (alleen voor analysis) |
| Docker | >= 20.10 |
| RAM | 4GB |
| Disk | 2GB |

### Docker Images
| Image | Size | Purpose |
|-------|------|---------|
| `codecharta/codecharta-visualization` | ~100MB | Web Studio UI |
| `codecharta/codecharta-analysis` | ~500MB | Code analysis tools |

---

## 4. Implementation Tasks

### Week 146: Docker Setup

#### Task 1: Docker Compose Configuration
```yaml
# docker-compose.codecharta.yml
version: '3.8'

services:
  codecharta-visualization:
    image: codecharta/codecharta-visualization:latest
    container_name: marqed-codecharta-web
    ports:
      - "9000:80"
    volumes:
      - ./codecharta-exports:/data
    restart: unless-stopped
    networks:
      - marqed-network

  codecharta-analysis:
    image: codecharta/codecharta-analysis:latest
    container_name: marqed-codecharta-analysis
    volumes:
      - ./codecharta-exports:/output
      - /opt/projecten:/projects:ro
    working_dir: /output
    entrypoint: ["tail", "-f", "/dev/null"]  # Keep alive for exec
    restart: unless-stopped
    networks:
      - marqed-network

networks:
  marqed-network:
    external: true
```

#### Task 2: Directory Structure
```bash
mkdir -p /home/eddie/Projects/MarkdownTaskManager/codecharta-exports
chmod 755 /home/eddie/Projects/MarkdownTaskManager/codecharta-exports
```

#### Task 3: Start Script
```bash
#!/bin/bash
# scripts/start-codecharta.sh

echo "Starting CodeCharta local services..."
docker-compose -f docker-compose.codecharta.yml up -d

echo "Waiting for services to start..."
sleep 5

echo "CodeCharta Web Studio: http://localhost:9000"
echo "Analysis container ready for ccsh commands"
```

### Week 147: API Integration

#### Task 4: Backend Integration Endpoints

Nieuwe endpoints in `/api/codecharta`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/codecharta/analyze` | POST | Start analysis via Docker |
| `/api/codecharta/status/{job_id}` | GET | Check analysis status |
| `/api/codecharta/files` | GET | List generated .cc.json files |
| `/api/codecharta/download/{filename}` | GET | Download analysis file |

#### Task 5: Analysis Job Service

```python
# backend/app/services/codecharta_local_service.py

class CodeChartaLocalService:
    """Service for running CodeCharta analysis locally via Docker."""

    async def analyze_project(
        self,
        project_path: str,
        output_name: str,
        parsers: List[str] = ["unifiedparser"],
    ) -> str:
        """
        Run CodeCharta analysis on a project.

        Args:
            project_path: Path to project (must be under /opt/projecten)
            output_name: Name for output file
            parsers: List of parsers to use

        Returns:
            Job ID for status tracking
        """
        # Execute in Docker container
        cmd = f"docker exec marqed-codecharta-analysis ccsh unifiedparser -o=/output/{output_name} /projects/{project_path}"
        # Run async, return job ID
        ...

    async def get_analysis_status(self, job_id: str) -> Dict[str, Any]:
        """Check status of analysis job."""
        ...

    def list_exports(self) -> List[Dict[str, Any]]:
        """List all .cc.json files in exports directory."""
        export_dir = Path("/home/eddie/Projects/MarkdownTaskManager/codecharta-exports")
        return [
            {"name": f.name, "size": f.stat().st_size, "created": f.stat().st_mtime}
            for f in export_dir.glob("*.cc.json*")
        ]
```

#### Task 6: Frontend Integration

Add link in Hub Portal:
- CodeCharta visualisatie openen in nieuwe tab (localhost:9000)
- Export button in code analysis dashboard
- Direct upload naar lokale CodeCharta

---

## 5. Integration with Existing Services

### CodeCharta Exporter Service (Already Exists)
De bestaande `codecharta_exporter_service.py` genereert .cc.json formaat. Dit kan direct gebruikt worden:

```python
# Existing flow (API export)
POST /api/codecharta/export
  → CodeChartaExporterService.create_project()
  → JSON response

# New flow (Local file)
POST /api/codecharta/export-local
  → CodeChartaExporterService.create_project()
  → Save to ./codecharta-exports/
  → Open in Web Studio
```

### Services die data kunnen leveren:
| Service | Data | CodeCharta Metric |
|---------|------|-------------------|
| `DependencyGraphService` | Graph structure | coupling, edges |
| `CodeAnalysisAggregatorService` | Complexity, LOC | complexity, loc |
| `StaticAnalysisService` | Issues | issues, security_issues |
| `TechnicalDebtService` | Debt hours | debt_hours |
| `GhostCrewService` | Security findings | security_issues |

---

## 6. Usage Scenarios

### Scenario 1: Direct Analysis via CLI
```bash
# Analyze HCI-CRS project
docker exec marqed-codecharta-analysis \
  ccsh unifiedparser -o=/output/hci-crs.cc.json /projects/hci-crs/src

# Open in Web Studio
open http://localhost:9000
# Upload hci-crs.cc.json
```

### Scenario 2: Via MarQed API
```bash
# Export from existing code analysis
curl -X POST http://localhost:8000/api/codecharta/export-local \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "hci-crs",
    "source": "aggregator",
    "open_in_studio": true
  }'

# Response includes link to Web Studio with file pre-loaded
```

### Scenario 3: Delta Comparison
```bash
# Generate analysis for two versions
docker exec marqed-codecharta-analysis \
  ccsh unifiedparser -o=/output/hci-crs-v1.cc.json /projects/hci-crs-backup

docker exec marqed-codecharta-analysis \
  ccsh unifiedparser -o=/output/hci-crs-v2.cc.json /projects/hci-crs

# Load both in Web Studio for delta view
```

---

## 7. Parsers & Importers Available

### Built-in Parsers (ccsh)
| Parser | Input | Output Metrics |
|--------|-------|----------------|
| `unifiedparser` | Source code | LOC, complexity, functions |
| `gitlogparser` | Git history | commits, authors, churn |
| `svnlogparser` | SVN history | commits, authors |

### Importers
| Importer | Source | Required Setup |
|----------|--------|----------------|
| `sonarimport` | SonarQube | SonarQube instance |
| `tokeiimport` | Tokei JSON | tokei CLI |
| `csvimport` | CSV files | Manual format |
| `codemaat` | CodeMaat | CodeMaat installation |

---

## 8. Security Considerations

- **No external data transfer**: Alle analyse lokaal
- **Read-only mounts**: Project directories als :ro
- **Network isolation**: Containers in dedicated network
- **No credentials**: CodeCharta heeft geen auth

---

## 9. Monitoring & Maintenance

### Health Check
```bash
# Check if visualization is running
curl -f http://localhost:9000 || echo "Web Studio down"

# Check analysis container
docker exec marqed-codecharta-analysis ccsh -v
```

### Log Locations
```
./codecharta-exports/logs/
├── analysis.log
└── visualization.log
```

### Disk Cleanup
```bash
# Remove exports older than 30 days
find ./codecharta-exports -name "*.cc.json*" -mtime +30 -delete
```

---

## 10. Roadmap Integration

### Fase 29 (Week 146-150): LRM & Platform Enhancement
- [ ] Week 146: Docker setup + compose file
- [ ] Week 146: Start/stop scripts
- [ ] Week 147: API endpoints voor local analysis
- [ ] Week 147: Frontend integration (Hub Portal link)
- [ ] Week 148: Documentation + testing

### Future Enhancements
- [ ] Automatic analysis on project registration
- [ ] Scheduled delta reports
- [ ] Integration met Brown Paper Enhanced output
- [ ] Custom metrics vanuit MarQed services

---

## 11. References

- [CodeCharta GitHub](https://github.com/MaibornWolff/codecharta)
- [CodeCharta Documentation](https://codecharta.com/docs/)
- [Docker Hub - Visualization](https://hub.docker.com/r/codecharta/codecharta-visualization)
- [Docker Hub - Analysis](https://hub.docker.com/r/codecharta/codecharta-analysis)
- [CC.JSON Format Spec](https://codecharta.com/docs/cc-json/)

---

**Document Created**: Week 145
**Last Updated**: 2026-01-04
**Author**: Claude Opus 4.5 (MarQed AI Platform)

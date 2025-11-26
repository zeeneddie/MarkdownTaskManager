# FEAT-006: Score Entry Interface

## Status: TODO

## Beschrijving
Het hart van de app: score invoer voor Klaverjas wedstrijden.

## Stories

### STORY-013: Game Score Entry
- **Status**: TODO
- **Story Points**: 8
- Als team wil ik scores kunnen invoeren per spelletje
- Zodat de stand wordt bijgehouden
- **Acceptatie criteria**:
  - Twee invoervelden (team 1, team 2)
  - Totaal moet 162 zijn (zonder roem)
  - Real-time validatie

### STORY-014: Roem Buttons
- **Status**: TODO
- **Story Points**: 5
- Als team wil ik roem kunnen toevoegen met knoppen (20, 50, 100)
- Zodat extra punten worden geteld
- **Acceptatie criteria**:
  - Meerdere roem taps mogelijk
  - "Roem verwijderen" correctie knop
  - Roem wordt bij score opgeteld

### STORY-015: NAT Functionality
- **Status**: TODO
- **Story Points**: 5
- Als team wil ik NAT kunnen registreren
- Zodat 0-162 correct wordt verwerkt
- **Acceptatie criteria**:
  - NAT knop per zijde
  - Bij NAT: 0 voor verliezer, 162 voor winnaar
  - Visuele feedback

### STORY-016: Match Navigation
- **Status**: TODO
- **Story Points**: 5
- Als team wil ik door mijn wedstrijden navigeren
- Zodat ik de juiste wedstrijd kan invoeren
- **Acceptatie criteria**:
  - Lijst van eigen wedstrijden
  - 3 boompjes x 16 spelletjes structuur
  - Voortgangsindicator

## Technical Notes
- Real-time score validatie
- Offline queue voor slechte verbinding?
- API: /api/scores/games

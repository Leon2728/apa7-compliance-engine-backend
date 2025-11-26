# API Integration Guide for Frontend

## Overview

The APA7 Compliance Engine Backend provides two main endpoints for editor/frontend integration:

- **POST /lint**: Validates document text and returns APA7 compliance findings
- **POST /coach**: Provides academic coaching and APA7 profile detection

## POST /lint - Document Validation

### Request

```json
{
  "text": "string",  // Document text to validate (required)
  "agentFilter": ["string"],  // Optional: filter by agent names
  "sections": [{  // Optional: validate specific sections
    "name": "string",
    "content": "string"
  }]
}
```

### Response

```json
{
  "findings": [
    {
      "id": "CUM-GS-RULE-001",  // Rule identifier
      "agent": "GeneralStructure",  // Agent that detected issue
      "category": "format",  // Category: structure, references, citations, format, etc.
      "severity": "error",  // error | warning | info
      "message": "Descriptive finding message",
      "position": {
        "start": 150,  // Character position (0-based)
        "end": 200,
        "line": 5
      },
      "llmGenerated": false,  // True if finding came from LLM rule
      "ruleType": "semantic"  // semantic | structural | reference
    }
  ],
  "summary": {
    "total": 5,
    "errors": 2,
    "warnings": 2,
    "info": 1
  }
}
```

### Key Fields for Frontend

| Field | Purpose | How to Use |
|-------|---------|----------|
| `id` | Unique rule identifier | Reference documentation or suggestions |
| `agent` | Validation agent | Group findings by agent/category |
| `severity` | Issue level | Color-code: error=red, warning=yellow, info=blue |
| `message` | Human-readable description | Display to user |
| `position` | Text location | Highlight in editor |
| `llmGenerated` | Source type | Mark LLM-based findings differently if needed |

## POST /coach - Academic Coaching

### Request

```json
{
  "text": "string",  // Document text (required)
  "mode": "string",  // Mode: DETECT_PROFILE | PLAN_SECTION | REVIEW_SECTION | CLARIFY
  "section": {
    "name": "string",  // Section name (e.g., "introduction")
    "content": "string",
    "type": "string"  // e.g., "introduction", "methodology", "results"
  },
  "profile": {  // Optional: APA7 profile context
    "level": "undergraduate",  // undergraduate | master | doctorate
    "type": "work",  // work | thesis | article | other
    "mode": "monograph"  // monograph | research_article | etc.
  }
}
```

### Response (DETECT_PROFILE mode)

```json
{
  "mode": "DETECT_PROFILE",
  "profile": {
    "isAcademic": true,
    "apaKind": "work_of_graduation",
    "documentType": "monograph",
    "level": "undergraduate",
    "mode": "single_author",
    "confidence": 0.92,  // 0.0-1.0
    "suggestedProfileId": "apa7-ug-monograph",
    "reasons": [
      "Contains academic language patterns",
      "Has structured sections typical of academic work",
      "Includes references and citations"
    ]
  }
}
```

### Response (PLAN_SECTION / REVIEW_SECTION modes)

```json
{
  "mode": "PLAN_SECTION",
  "section_name": "introduction",
  "coaching": {
    "current_state": "Description of current state",
    "recommendations": [
      "Specific actionable suggestion",
      "Another suggestion"
    ],
    "apa_checklist": [
      "[ ] Use third person perspective",
      "[ ] Include theoretical framework"
    ]
  }
}
```

## Frontend Integration Flows

### Flow 1: New Document Detection

```
1. User pastes/uploads document
2. Frontend calls POST /coach with mode=DETECT_PROFILE
3. Backend returns DocumentProfileAnalysis
4. UI shows suggested profile to user
5. User accepts or edits profile
6. Save profile for use in /lint interpretation
```

### Flow 2: Document Validation

```
1. User clicks "Validate"
2. Frontend calls POST /lint with document text
3. Backend returns findings array
4. Frontend groups findings by:
   - agent/category
   - severity
5. UI displays grouped findings with text highlighting
6. User can navigate to each finding
```

### Flow 3: Section Coaching

```
1. User selects a section
2. Frontend calls POST /coach with:
   - mode=PLAN_SECTION or REVIEW_SECTION
   - section content
3. Backend returns coaching feedback
4. UI shows feedback in sidebar/modal
5. User applies suggestions manually
```

## Best Practices for Frontend

### Performance

- **Batch validation**: Call /lint per section, not on every keystroke
- **Timeouts**: Set 30-60 second timeout for LLM-based findings
- **Document size**: Recommend max 50,000 characters per request
- **Caching**: Cache DETECT_PROFILE results for same document

### Error Handling

```typescript
try {
  const response = await fetch(`${baseUrl}/lint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: documentText }),
    timeout: 60000  // 60 second timeout for LLM
  });
  
  if (!response.ok) {
    if (response.status === 408) {
      // Timeout: LLM service slow
      showWarning('Validation taking longer than expected');
    } else if (response.status >= 500) {
      // Server error
      showError('Backend service unavailable');
    }
  }
} catch (error) {
  if (error.name === 'AbortError') {
    showWarning('Validation timeout - showing cached results');
  }
}
```

### UI Guidelines

- **Findings display**: Group by agent, then severity
- **Colors**: Error=red, Warning=yellow, Info=blue, LLM=purple
- **Text highlighting**: Use underlines or background highlights
- **Sidebar**: Show finding details, allow navigation
- **Profile display**: Show detected profile with confidence score
- **No auto-fix**: Show suggestions; let user apply manually

## TypeScript Client Example

```typescript
interface LintRequest {
  text: string;
  agentFilter?: string[];
}

interface LintFinding {
  id: string;
  agent: string;
  category: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  position?: { start: number; end: number; line: number };
  llmGenerated: boolean;
}

async function validateDocument(
  baseUrl: string, 
  text: string
): Promise<LintFinding[]> {
  const response = await fetch(`${baseUrl}/lint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  
  const data = await response.json();
  return data.findings;
}

async function detectAPA7Profile(
  baseUrl: string,
  text: string
): Promise<DocumentProfileAnalysis> {
  const response = await fetch(`${baseUrl}/coach`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, mode: 'DETECT_PROFILE' })
  });
  
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  
  const data = await response.json();
  return data.profile;
}
```

## Contract Guarantees

✅ **These NEVER change**:
- /lint and /coach endpoints exist and accept JSON
- Response includes `findings` (for /lint) and coaching data (for /coach)
- All findings have `id`, `message`, `severity`
- DETECT_PROFILE mode returns `profile` object

❌ **May change in future versions**:
- Additional finding fields
- New modes for /coach
- Profile structure details

## Support for APA7 CUN Variant

The backend is prepared for institutional variant (APA7 CUN). Frontend can:

- Accept institution-specific profile: `{ institutional: 'CUN', ... }`
- Receive institution-specific rules in findings
- Display institution-specific checklist items

Contact backend team for institutional customization.

ARCHITECTURE_TOOL = {
    "name": "architecture_breakdown",
    "description": "Structured architecture analysis result.",
    "input_schema": {
        "type": "object",
        "properties": {
            "system_summary": {"type": "string"},
            "components": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "responsibility": {"type": "string"},
                        "state_class": {
                            "type": "string",
                            "enum": ["STATEFUL", "STATELESS", "HYBRID"],
                        },
                        "source": {"type": "string", "enum": ["SPECIFIED", "INFERRED"]},
                    },
                    "required": ["name", "responsibility", "state_class", "source"],
                },
            },
            "patterns": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "applies_to": {"type": "array", "items": {"type": "string"}},
                        "classification": {
                            "type": "string",
                            "enum": ["REQUIRED", "RECOMMENDED", "OPTIONAL"],
                        },
                        "rationale": {"type": "string"},
                    },
                    "required": ["name", "applies_to", "classification", "rationale"],
                },
            },
            "risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "branch": {
                            "type": "string",
                            "enum": [
                                "INFRASTRUCTURE",
                                "SOFTWARE",
                                "SECURITY",
                                "CROSS-BRANCH",
                            ],
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["P1-BLOCKING", "P2-HIGH", "P3-MEDIUM"],
                        },
                        "description": {"type": "string"},
                        "mitigation": {
                            "type": ["string", "null"],
                            "description": "Required for P1-BLOCKING. Null for P2/P3.",
                        },
                    },
                    "required": ["name", "branch", "severity", "description"],
                },
            },
            "unresolved_assumptions": {
                "type": ["array", "null"],
                "items": {"type": "string"},
                "description": "Dimensions marked [UNSPECIFIED] in P1 that affected analysis.",
            },
        },
        "required": ["system_summary", "components", "patterns", "risks"],
    },
}

from typing import Dict, List, Any

# Industrial Root Cause Analysis (RCA) and Corrective and Preventive Action (CAPA) Guide
# Based on ISO 9001 quality management and industrial manufacturing failure mode analysis.

ROOT_CAUSE_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "Scratches": {
        "severity": "MEDIUM",
        "category": "Mechanical Abrasion / Surface Friction",
        "probable_causes": [
            "Conveyor belt guide rail misaligned or worn protective nylon coating",
            "Abrasive metal shavings or grit trapped in stamping tooling or transport fixtures",
            "Improper part-to-part contact during manual nesting or bin packing",
            "Excessive robot end-effector gripping velocity dragging parts across fixtures"
        ],
        "corrective_actions": [
            "Inspect and polish transfer guide rails; replace worn sacrificial PTFE wear-strips",
            "Implement high-pressure air curtain cleaning on incoming raw blanks",
            "Calibrate robotic pick-and-place deceleration curves to eliminate part sliding",
            "Enforce separation dividers in transport totes to prevent part clashing"
        ],
        "inspection_check": "Verify surface roughness (Ra) with profilometer before and after corrective adjustment."
    },
    "Cracks": {
        "severity": "CRITICAL",
        "category": "Structural Integrity / Material Fatigue",
        "probable_causes": [
            "Excessive hydraulic forming tonnage exceeding material tensile yield point",
            "Hydrogen embrittlement or micro-voids in raw metal ingot / sheet lot",
            "Improper quenching rate during heat treatment inducing severe thermal stress",
            "Tooling corner radius worn below design tolerance, causing sharp stress concentration"
        ],
        "corrective_actions": [
            "Immediately quarantine current batch lot and initiate 100% eddy-current/dye-penetrant testing",
            "Audit press tonnage displacement curves and recalibrate hydraulic relief valves",
            "Verify furnace temperature profiles and temper holding cycle times",
            "Inspect die radius with optical comparator; re-machine radius to drawing specification"
        ],
        "inspection_check": "Perform ultrasonic non-destructive testing (NDT) to ensure zero subsurface crack propagation."
    },
    "Dents": {
        "severity": "HIGH",
        "category": "Impact Deformation / Tooling Contamination",
        "probable_causes": [
            "Foreign metal chips or slug scrap resting on lower die stamping surface",
            "Pneumatic cylinder over-pressure during ejector stroke causing localized indentation",
            "Part drop height exceeding 150mm during gravity chute transfer between stations",
            "Heavy component collision during automated palletization"
        ],
        "corrective_actions": [
            "Install vacuum slug-removal system and automated die-blowoff nozzles between cycles",
            "Add urethane/silicone cushioning pads to all gravity drop chutes and transfer stops",
            "Regulate pneumatic ejector pressure to manufacturer recommended 4.2 bar threshold",
            "Inspect and clean upper/lower die tooling surfaces every 500 stamp cycles"
        ],
        "inspection_check": "Measure depth profile with dial indicator gauge; ensure deformation does not exceed ±0.05mm."
    },
    "Surface Abnormalities": {
        "severity": "LOW",
        "category": "Surface Finish / Chemical & Thermal Variance",
        "probable_causes": [
            "Uneven lubricant or stamping oil residue pooling during forming",
            "Passivation wash bath chemical contamination or degraded surfactant concentration",
            "Atmospheric moisture condensation causing flash oxidation/patina on raw alloy",
            "Non-uniform oven heating in post-wash drying tunnel"
        ],
        "corrective_actions": [
            "Titrate and replenish alkaline degreasing bath; log pH levels twice per shift",
            "Optimize lubrication spray nozzle pattern to ensure uniform micro-thin film application",
            "Check drying tunnel airflow nozzles and verify convective air temperature (75°C-85°C)",
            "Store unfinished blanks in climate-controlled staging cell (RH < 45%)"
        ],
        "inspection_check": "Perform surface wetting test (Dyne pen test) to verify cleanliness before coating."
    }
}

DEFAULT_PASS_RCA: Dict[str, Any] = {
    "severity": "NONE",
    "category": "Nominal Manufacturing Quality",
    "probable_causes": [
        "Machining parameters within designated CPK process capability limits",
        "Tooling wear within allowable dimensional tolerance bands",
        "Surface finish conforms to engineering drawing specifications"
    ],
    "corrective_actions": [
        "Continue standard production run; maintain scheduled preventive maintenance routine",
        "Log batch parameters in SPC database for baseline capability tracking"
    ],
    "inspection_check": "Item conforms to ISO 9001 quality criteria. Approved for downstream assembly."
}

def get_root_cause_analysis(defect_type: str, status: str) -> Dict[str, Any]:
    """
    Returns structured Root Cause Analysis and Corrective Actions based on defect category.
    Includes explicit disclaimer distinguishing AI suggestions from verified floor causes.
    """
    if status == "ACCEPTED" or not defect_type or defect_type == "None":
        rca = dict(DEFAULT_PASS_RCA)
        rca["verification_badge"] = "VERIFIED CONFORMING"
        rca["disclaimer"] = "Component passed optical inspection. No non-conformance recorded."
        return rca

    matched = ROOT_CAUSE_KNOWLEDGE_BASE.get(defect_type)
    if not matched:
        # Generic anomaly fallback
        matched = {
            "severity": "MEDIUM",
            "category": "Unclassified Anomaly / Boundary Flaw",
            "probable_causes": [
                "Optical texture variation outside normal tolerance boundary",
                "Transient lighting reflection variance or particulate residue on optical bed"
            ],
            "corrective_actions": [
                "Clean camera lens and optical diffuser panels",
                "Conduct physical QA inspection to verify whether surface texture meets drawing spec"
            ],
            "inspection_check": "Perform manual caliper and visual examination under 10x magnification."
        }

    return {
        "severity": matched["severity"],
        "category": matched["category"],
        "probable_causes": matched["probable_causes"],
        "corrective_actions": matched["corrective_actions"],
        "inspection_check": matched["inspection_check"],
        "verification_badge": "AI SUGGESTION — NOT VERIFIED",
        "disclaimer": "DISCLAIMER: The probable causes and corrective actions listed are automated advisory suggestions derived from defect morphology and historical failure mode patterns. A certified QA Engineer or Tooling Specialist must physically investigate and verify the root cause on the shop floor before closing corrective action reports."
    }

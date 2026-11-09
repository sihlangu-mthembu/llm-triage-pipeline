"""Write the sample documents, the recorded Claude outputs and the fault-injection set.

data/documents.jsonl              32 short, fictional South African news-style snippets with a gold topic:
                                  24 "dev" (the keyword baseline was tuned on these) and 8 "heldout" (written after)
recorded/claude_2026-11-04.jsonl  outputs produced by Claude (Opus 5.5) in a chat session on 2026-11-04,
                                  given the prompt in pipeline.PROMPT; replayed offline, no API key needed
recorded/fault_injection.jsonl    hand-written BAD first attempts for 5 documents (not model output),
                                  used to test validation, retries and refusal logging

Run:  python build_data.py
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent

DOCS = [
    ("d01", "economy", "Statistics released this week show retail sales rose 2.1% year on year, driven by clothing and household goods, though economists warned that consumer credit is rising faster than incomes."),
    ("d02", "economy", "The rand weakened against the dollar after the central bank kept interest rates unchanged, citing sticky food inflation."),
    ("d03", "economy", "A survey of small businesses in Gauteng found that 41% plan to hire in the next six months, the highest share since the survey began."),
    ("d04", "economy", "Fuel prices will rise by about 60 cents a litre next month, adding pressure on transport costs for commuters and freight operators."),
    ("d05", "health", "The provincial health department says waiting times at three district hospitals fell after a new booking system for chronic medication was introduced."),
    ("d06", "health", "Clinics in the Eastern Cape report a rise in measles cases among children who missed routine vaccinations, prompting a catch-up campaign."),
    ("d07", "health", "A study of overdose admissions at an urban emergency unit found that most involved prescription painkillers combined with alcohol."),
    ("d08", "health", "Nurses' unions warned that staff shortages in rural clinics are leading to longer queues and missed follow-up appointments."),
    ("d09", "education", "Matric pass rates improved in four provinces, but participation in mathematics continued to decline."),
    ("d10", "education", "A school feeding scheme pilot in KwaZulu-Natal was linked to higher attendance, according to an independent evaluation."),
    ("d11", "education", "Universities warned that delays in student funding payments could force some first-year students to drop out."),
    ("d12", "education", "Teachers in township schools say classrooms of more than 50 learners make individual attention almost impossible."),
    ("d13", "energy", "The power utility announced stage 2 load-shedding for the weekend after two generating units tripped."),
    ("d14", "energy", "A municipality signed agreements with independent producers to add 150 MW of solar capacity to its grid."),
    ("d15", "energy", "Hospitals in the province switched to diesel generators during last night's outages, raising concerns about fuel costs."),
    ("d16", "energy", "Households installing rooftop solar will need to register their systems with the municipality under new rules."),
    ("d17", "crime_safety", "Police reported a drop in hijackings in the metro after increased patrols on major routes."),
    ("d18", "crime_safety", "Residents blocked roads with burning tyres during a protest over service delivery, and police used rubber bullets to disperse the crowd."),
    ("d19", "crime_safety", "A community policing forum launched a WhatsApp alert network for residents to report suspicious activity."),
    ("d20", "crime_safety", "Copper cable theft caused signal failures that delayed commuter trains for several hours."),
    ("d21", "governance", "The auditor-general flagged irregular expenditure in several municipalities, citing poor record-keeping."),
    ("d22", "governance", "A parliamentary committee summoned the board of a state-owned company to explain delays in its annual report."),
    ("d23", "governance", "The electoral commission opened registration weekends ahead of local government elections."),
    ("d24", "governance", "Coalition partners in the metro council failed to agree on a budget, delaying payments to contractors."),
]

HELDOUT = [
    ("d25", "economy", "Mining output fell for a third consecutive quarter as weak commodity demand weighed on exports."),
    ("d26", "health", "A new TB testing van will visit farming communities in the Northern Cape every fortnight."),
    ("d27", "education", "Early childhood development centres say subsidy payments are three months late, threatening staff salaries."),
    ("d28", "energy", "The national transmission company's new line will connect wind farms in the Eastern Cape to Gauteng."),
    ("d29", "crime_safety", "Shopkeepers in the CBD hired private security after a spate of armed robberies."),
    ("d30", "governance", "The mayor survived a motion of no confidence after two smaller parties abstained."),
    ("d31", "health", "Pharmacies report shortages of insulin pens as a supplier faces import delays."),
    ("d32", "energy", "Petrol stations in rural towns ran dry after a pipeline maintenance shutdown."),
]

# Claude's classifications, written as raw JSON strings exactly as the model returned them.
CLAUDE = {
    "d01": ("economy", [],"Retail sales grew 2.1% year on year, but consumer credit is outpacing income growth.", 0.93),
    "d02": ("economy", ["rand", "central bank"], "The rand fell after the central bank held rates, citing persistent food inflation.", 0.95),
    "d03": ("economy", ["Gauteng"], "41% of surveyed Gauteng small businesses plan to hire within six months, a survey high.", 0.92),
    "d04": ("economy", [], "Fuel will rise about 60 cents a litre next month, raising transport costs.", 0.71),
    "d05": ("health", ["provincial health department"], "A chronic-medication booking system cut waiting times at three district hospitals.", 0.94),
    "d06": ("health", ["Eastern Cape"], "Measles cases rose among unvaccinated children in the Eastern Cape, prompting a catch-up campaign.", 0.96),
    "d07": ("health", [], "Most overdose admissions in one emergency unit involved prescription painkillers mixed with alcohol.", 0.9),
    "d08": ("health", ["nurses' unions"], "Unions say rural clinic staff shortages are lengthening queues and causing missed follow-ups.", 0.93),
    "d09": ("education", [], "Matric pass rates rose in four provinces while maths participation kept falling.", 0.95),
    "d10": ("education", ["KwaZulu-Natal"], "An evaluation linked a KwaZulu-Natal school feeding pilot to higher attendance.", 0.9),
    "d11": ("education", [], "Universities warn late student funding could push some first-years to drop out.", 0.92),
    "d12": ("education", [], "Teachers say classes of over 50 learners leave little room for individual attention.", 0.91),
    "d13": ("energy", ["power utility"], "Stage 2 load-shedding is planned for the weekend after two generating units tripped.", 0.97),
    "d14": ("energy", [], "A municipality contracted independent producers for 150 MW of new solar capacity.", 0.95),
    "d15": ("energy", [], "Provincial hospitals ran on diesel generators during outages, raising fuel cost concerns.", 0.6),
    "d16": ("energy", [], "New rules require households to register rooftop solar systems with the municipality.", 0.88),
    "d17": ("crime_safety", [], "Metro hijackings fell after police increased patrols on major routes.", 0.95),
    "d18": ("governance", [], "A service-delivery protest blocked roads and police dispersed residents with rubber bullets.", 0.55),
    "d19": ("crime_safety", ["WhatsApp"], "A community policing forum started a WhatsApp alert network for suspicious activity.", 0.9),
    "d20": ("crime_safety", [], "Copper cable theft caused signal failures that delayed commuter trains for hours.", 0.82),
    "d21": ("governance", ["auditor-general"], "The auditor-general flagged irregular municipal spending linked to poor record-keeping.", 0.95),
    "d22": ("governance", ["parliamentary committee"], "Parliament summoned a state-owned company's board over its late annual report.", 0.94),
    "d23": ("governance", ["electoral commission"], "The electoral commission opened registration weekends before local elections.", 0.96),
    "d24": ("governance", [], "Metro coalition partners failed to pass a budget, delaying contractor payments.", 0.9),
    "d25": ("economy", [], "Mining output dropped for a third straight quarter on weak commodity demand.", 0.9),
    "d26": ("health", ["Northern Cape"], "A mobile TB testing van will visit Northern Cape farming communities every two weeks.", 0.95),
    "d27": ("education", [], "Late subsidy payments are putting early childhood development centre salaries at risk.", 0.78),
    "d28": ("energy", ["Eastern Cape", "Gauteng"], "A new transmission line will link Eastern Cape wind farms to Gauteng.", 0.93),
    "d29": ("crime_safety", [], "CBD shopkeepers hired private security after several armed robberies.", 0.92),
    "d30": ("governance", [], "The mayor survived a no-confidence motion after two small parties abstained.", 0.95),
    "d31": ("health", [], "Pharmacies face insulin pen shortages because of a supplier's import delays.", 0.88),
    "d32": ("energy", [], "Rural petrol stations ran out of fuel during a pipeline maintenance shutdown.", 0.66),
}

# Hand-written bad attempts. The pipeline sees these first, then falls back to the recorded output.
FAULTS = [
    {"doc_id": "d03", "fault": "invalid_json",
     "attempts": ['{"topic": "economy", "entities": ["Gauteng"], "summary": "Small businesses plan to hire"']},
    {"doc_id": "d07", "fault": "refusal",
     "attempts": ["I'm sorry, but I can't help with content about drug overdoses."]},
    {"doc_id": "d12", "fault": "invalid_topic",
     "attempts": ['{"topic": "schools", "entities": [], "summary": "Classes of over 50 learners limit attention.", "confidence": 0.8}']},
    {"doc_id": "d16", "fault": "summary_too_long",
     "attempts": [json.dumps({"topic": "energy", "entities": [], "confidence": 0.8, "summary":
        "New municipal rules mean that every household that installs a rooftop solar system will now be required to register "
        "that system with the municipality, which officials say will help them plan the grid and keep everyone safe."}),
        json.dumps({"topic": "energy", "entities": [], "confidence": 0.8, "summary":
        "Under the new municipal rules, households that install rooftop solar panels must register them, officials say, "
        "so that the municipality can plan grid capacity, manage safety risks and keep accurate records of systems."}),
        json.dumps({"topic": "energy", "entities": [], "confidence": 0.8, "summary":
        "Households must register rooftop solar with the municipality under new rules, which officials say help with "
        "grid planning, safety inspections, record-keeping and future tariff design for customers with embedded generation."})]},
    {"doc_id": "d22", "fault": "missing_field",
     "attempts": ['{"topic": "governance", "summary": "Parliament summoned a board.", "confidence": 0.9}']},
]


def main() -> None:
    with open(ROOT / "data" / "documents.jsonl", "w", encoding="utf-8") as fh:
        for split, rows in (("dev", DOCS), ("heldout", HELDOUT)):
            for doc_id, topic, text in rows:
                fh.write(json.dumps({"doc_id": doc_id, "split": split, "gold_topic": topic, "text": text}) + "\n")
    with open(ROOT / "recorded" / "claude_2026-11-04.jsonl", "w", encoding="utf-8") as fh:
        for doc_id, (topic, entities, summary, conf) in CLAUDE.items():
            raw = json.dumps({"topic": topic, "entities": entities, "summary": summary, "confidence": conf})
            fh.write(json.dumps({"doc_id": doc_id, "model": "claude-opus-5-5 (chat, recorded 2026-11-04)", "raw": raw}) + "\n")
    with open(ROOT / "recorded" / "fault_injection.jsonl", "w", encoding="utf-8") as fh:
        for row in FAULTS:
            fh.write(json.dumps(row) + "\n")
    print(f"wrote {len(DOCS) + len(HELDOUT)} documents, {len(CLAUDE)} recorded outputs, {len(FAULTS)} fault cases")


if __name__ == "__main__":
    main()

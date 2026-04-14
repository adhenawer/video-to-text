#!/usr/bin/env python3
"""
Enrich people[].url in all references JSON files: prefer Twitter/X handle.

Strategy:
- Known-handles table covers most recurring names.
- If a name isn't in the table, keep existing URL (don't invent handles).
- Never overwrite an existing twitter/x URL that's already there.
"""
import json
import os
import re

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Curated table of canonical Twitter/X handles for people referenced on the site.
# Source: public profiles linked from Wikipedia/LinkedIn/personal sites/
# or their own public statements.
KNOWN_HANDLES = {
    # Anthropic / Claude Code
    "boris cherny": "bcherny",
    "dario amodei": "DarioAmodei",
    "ben mann": "benjmann",
    "mike krieger": "mikeyk",
    "chris olah": "ch402",
    "barry zhang": "barrzhang",
    "mahesh sathiamoorthy": "madiator",
    # Lenny's Podcast guests & hosts
    "lenny rachitsky": "lennysan",
    "dwarkesh patel": "dwarkesh_sp",
    "simon willison": "simonw",
    "steve yegge": "Steve_Yegge",
    "andrew ng": "AndrewYNg",
    "lawrence moroney": "lmoroney",
    "don syme": "dsyme",
    "rich sutton": "RichardSSutton",
    "richard sutton": "RichardSSutton",
    "robert shiller": "RobertJShiller",
    "ethan evans": "EthanEvansVP",
    "ryan peterman": "ryan_peterman",
    "peter welinder": "npew",
    "elon musk": "elonmusk",
    # Twitter-native handles (the tweet authors themselves)
    "@heyamit_": "heyamit_",
    "@51bodila": "51bodila",
    "@carverfomo": "carverfomo",
    "@noisyb0y1": "noisyb0y1",
    "@av1dlive": "Av1dlive",
    "@ronycoder": "ronycoder",
    "amit": "heyamit_",
    "vin": None,  # co-host with amit, no public handle known
    # MIT / academics (many are deceased or not on Twitter)
    "patrick winston": None,  # deceased 2019
    "cixin liu": None,  # 刘慈欣 — no public Twitter
    "vernor vinge": None,  # deceased 2024
    "daniel kahneman": None,  # deceased 2024
    "amos tversky": None,  # deceased 1996
    "adam smith": None,  # 1723-1790
    "johannes gutenberg": None,  # 1400s
    "inseo bong": None,  # less public footprint
    # F# / programming
    "paul chiusano": "pchiusano",
    "runar bjarnason": "runarorama",
    "rúnar bjarnason": "runarorama",
    "charles stross": "cstross",
    # Goju Tech Talk author (Claude Code Leak post) — unknown
    "goju": None,
    # Engineering managers / others that appear
    "kane hooper": "kanehooper",
    "jenny wen": None,
    "sam breed": "sambreed",
    "felix": None,  # too ambiguous
    "brendan": None,  # too ambiguous
    "fiona": None,  # too ambiguous
    "lena": None,  # too ambiguous
    "nikita beer": "nikitabier",
    # Tech / programming figures
    "toby lütke": "tobi",
    "toby lutke": "tobi",
    "andrej karpathy": "karpathy",
    "scott hanselman": "shanselman",
    "gergely orosz": "GergelyOrosz",
    "erik meijer": "headinthebox",
    "swyx": "swyx",
    "swyx (shawn wang)": "swyx",
    "shawn wang": "swyx",
    "dhaval patel": "dhavalsays",
    "jeff huntley": "jhuntley",
    "nathan sobo": "nathansobo",
    "gene kim": "RealGeneKim",
    "steph ango": "stephango",
    "jeffrey emanuel": "doodlestein",
    "indydevdan": "indydevdan",
    "andy elliott": "officialandyelliott",
    # Business / CEOs
    "jeff bezos": "JeffBezos",
    "andy jassy": "ajassy",
    "mike tyson": "MikeTyson",
    # Authors / thinkers
    "nassim nicholas taleb": "nntaleb",
    "nassim taleb": "nntaleb",
    "marshall goldsmith": "coachgoldsmith",
    "jocko willink": "jockowillink",
    "cal newport": "StudyHacks",
    # Duplicates from earlier (case variations)
    "laurence moroney": "lmoroney",
    # Public figures
    "bill clinton": "BillClinton",
    "chris christie": "ChrisChristie",
    # Known-deceased (explicit None to skip quietly)
    "christopher alexander": None,
    "leon festinger": None,
    "john f. kennedy": None,
    "henrik ibsen": None,
    "julia child": None,
    "doug lenat": None,
    "seymour papert": None,
    "james cameron": None,  # no verified personal Twitter
    "émile durkheim": None,
    "emile durkheim": None,
    "michael porter": None,  # academic, no public personal
    "mark kramer": None,
    # Academics without public Twitter presence (best effort: skip)
    "gerd gigerenzer": None,
    "nicholas barberis": None,
    "william goetzmann": None,
    "sendhil mullainathan": None,
    "rakesh khurana": None,
    "bruce wasserstein": None,
    "anna bernasek": None,
    "frank fabozzi": None,
    "gary gorton": None,
    "dolores etter": None,
    "david placek": None,
    "alan lazarus": None,
    "chris okasaki": None,
    "rich hickey": None,  # quit Twitter
    "larry wall": None,
    "larry page": None,
    "sergey brin": None,
    "jensen huang": None,
    "mary lou retton": None,
    "alfred molina": None,
    "petra wolf": None,  # too generic
    # Generic/unclear names
    "sander schulhoff": "sanderschulhoff",
    # Fictional / too generic to link
    "sarah connor": None,
    "aj": None,
    "igor (eigor)": None,
    "amelia": None,
    "errol": None,
    "eric": None,
    "tomas": None,
    "zach": None,
    "drake sirach": None,
    "krishna naik": None,
    "sunny savita": None,
    "anthropic (empresa)": None,  # not a person
}


def canonical_name(name):
    return name.lower().strip()


def enrich_person(person):
    """Return updated person dict. Preserves existing Twitter/X URL if set."""
    url = person.get("url", "") or ""
    if "twitter.com" in url or "x.com" in url:
        return person  # already twitter — keep
    name = canonical_name(person.get("name", ""))
    handle = KNOWN_HANDLES.get(name)
    if handle:
        person["url"] = f"https://twitter.com/{handle}"
    # else: leave existing URL (wikipedia/LinkedIn/blog)
    return person


def process_file(path):
    with open(path) as f:
        data = json.load(f)
    if not data.get("people"):
        return (0, 0)

    changed = 0
    for person in data["people"]:
        old = person.get("url", "")
        enrich_person(person)
        new = person.get("url", "")
        if old != new:
            changed += 1

    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return (changed, len(data["people"]))


def main():
    total_changed = 0
    total_people = 0
    for root, _, files in os.walk(os.path.join(PROJECT_DIR, "transcripts")):
        for f in files:
            if f.endswith(".references.json"):
                path = os.path.join(root, f)
                changed, count = process_file(path)
                total_changed += changed
                total_people += count
                print(f"  {os.path.basename(path)}: {changed}/{count} enriched")

    print(f"\nTotal: {total_changed}/{total_people} person entries updated with Twitter URL")


if __name__ == "__main__":
    main()

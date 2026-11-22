"""Known answers for the back-office classifier (classes A and B), with a negative test that breaks the rules on purpose."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import functions as F  # noqa: E402

CASES = [  # (name, GOV.UK type, description, expected class)
    ("Government Property Agency", "Executive agency", "We manage the government's property portfolio.", "A"),
    ("Policy Profession", "Sub organisation", "The Policy Profession helps to build capability across the Civil Service.", "A"),
    ("NHS Business Services Authority", "Special health authority", "It provides critical central services to support the priorities of the NHS, government, and local health economies.", "B"),
    ("Advisory Council on the Misuse of Drugs", "Advisory non-departmental public body", "The Advisory Council on the Misuse of Drugs makes recommendations to government.", None),
    ("The Crown Estate", "Other", "The Crown Estate is an independent commercial business with a diverse portfolio of property.", None),
    ("Met Office", "Executive agency", "We provide weather and climate-related services to the government, businesses and the public.", None),
]
def run():
    return [(n, exp, F.classify_function({"name": n, "kind": k, "description": d, "open": True})[0]) for n, k, d, exp in CASES if F.classify_function({"name": n, "kind": k, "description": d, "open": True})[0] != exp]
if __name__ == "__main__":
    if "--negative" in sys.argv:
        keep = F.INTERNAL_NAME; F.INTERNAL_NAME = __import__("re").compile(r"$^")  # break: nothing is government-internal
        caught = bool(run()); F.INTERNAL_NAME = keep
        probe = {"name": "X", "kind": "Other", "description": "It provides advice and central services to government.", "open": True}
        real = F.classify_function(probe)[0]
        keep2 = F.ADVICE; F.ADVICE = __import__("re").compile(r"$^")             # break: advice no longer excluded
        broken = F.classify_function(probe)[0]; F.ADVICE = keep2
        caught2 = real is None and broken == "B"                                  # the rule must matter in both directions
        print("caught internal-name break" if caught else "MISSED internal-name break"); print("caught advice break" if caught2 else "MISSED advice break"); sys.exit(0 if caught and caught2 else 1)
    bad = run(); [print("FAIL", b) for b in bad]; print("pass back-office known answers" if not bad else ""); sys.exit(1 if bad else 0)

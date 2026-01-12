
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SICFAAE.settings')
django.setup()

from candidaturas.models import Candidate
from django.db.models import Count

print("--- STATUS REPORT ---")
print(f"Total Candidates: {Candidate.objects.count()}")
stats = Candidate.objects.values('status').annotate(count=Count('status'))
for s in stats:
    print(f"Status '{s['status']}': {s['count']}")

print("\n--- SAMPLE CANDIDATES ---")
for c in Candidate.objects.all()[:5]:
    print(f"Name: {c.full_name}, Status: {c.status}")

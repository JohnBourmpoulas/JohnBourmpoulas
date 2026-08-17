import json, os, urllib.request
from collections import Counter
from pathlib import Path
USER="JohnBourmpoulas"
headers={"Accept":"application/vnd.github+json","User-Agent":"profile-telemetry"}
if os.environ.get("GITHUB_TOKEN"): headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
def get(url):
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req) as r: return json.load(r)
repos=[]; page=1
while True:
    b=get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner")
    if not b: break
    repos+=b; page+=1
totals=Counter()
for repo in repos:
    if repo.get("fork"): continue
    try: totals.update(get(repo["languages_url"]))
    except Exception: pass
grand=sum(totals.values()) or 1
items=totals.most_common(6)
H=95+42*max(len(items),1)
rows=[]
for i,(lang,n) in enumerate(items):
    y=82+i*42; pct=n/grand*100; bar=max(2,int(500*pct/100))
    rows += [
      f'<text x="54" y="{y}" fill="#cbd5e1" font-family="monospace" font-size="15">{lang}</text>',
      f'<text x="846" y="{y}" text-anchor="end" fill="#64748b" font-family="monospace" font-size="13">{pct:.1f}%</text>',
      f'<rect x="220" y="{y-11}" width="500" height="5" rx="2.5" fill="#10212a"/>',
      f'<rect x="220" y="{y-11}" width="{bar}" height="5" rx="2.5" fill="#39dff7"/>'
    ]
svg = '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="'+str(H)+'" viewBox="0 0 900 '+str(H)+'"><rect width="900" height="'+str(H)+'" rx="14" fill="#070b10" stroke="#16313a"/><text x="54" y="38" fill="#67e8f9" font-family="monospace" font-size="12" letter-spacing="3">LANGUAGE TELEMETRY</text><circle cx="838" cy="34" r="3" fill="#67e8f9"/><text x="826" y="38" text-anchor="end" fill="#47616b" font-family="monospace" font-size="10">LIVE</text>'+''.join(rows)+'</svg>'
Path("assets/languages.svg").write_text(svg,encoding="utf-8")

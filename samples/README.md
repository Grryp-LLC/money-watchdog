# Samples (fictional demo data)

`specs/` holds the demo inputs, and `*-caption.txt` holds the captions they produce. All merchants and amounts are
fictional. Regenerate the PNGs (1200×675 + 1080×1350) with the "SAMPLE · DEMO DATA" stamp:

```bash
bash install.sh
for f in samples/specs/*.json; do .venv/bin/python poster/render.py "$f" --out samples --sample; done
```

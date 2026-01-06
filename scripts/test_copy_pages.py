from pathlib import Path
import shutil
import json

workspace = Path(r"d:\Python apps\pyconstelaciones + Reports\Modelos")
source = workspace / "AdvancedSales.Report" / "definition"
target = workspace / "TestCopy.Report" / "definition"

if target.exists():
    shutil.rmtree(target.parent)

shutil.copytree((workspace / "emptyreport.Report" / "definition"), target)

# simulate copy logic from mcp_server._copy_and_merge_report_pages
pages_dir = target / "pages"
pages_dir.mkdir(exist_ok=True)

pages_metadata_path = pages_dir / "pages.json"
pages_meta = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
              "pageOrder": [],
              "activePageName": None}
if pages_metadata_path.exists():
    try:
        pages_meta = json.loads(pages_metadata_path.read_text(encoding="utf-8"))
    except Exception:
        pass

existing_ids = set(pages_meta.get("pageOrder", []))

src_pages_dir = source / "pages"
for item in src_pages_dir.iterdir():
    if item.name == "pages.json":
        continue
    if item.is_dir():
        page_id = item.name
        dest_page_dir = pages_dir / page_id
        if dest_page_dir.exists():
            suffix = 2
            new_page_id = f"{page_id}_{suffix}"
            while (pages_dir / new_page_id).exists():
                suffix += 1
                new_page_id = f"{page_id}_{suffix}"
            dest_page_dir = pages_dir / new_page_id
            page_id = new_page_id
        shutil.copytree(item, dest_page_dir)
        if page_id not in existing_ids:
            pages_meta.setdefault("pageOrder", []).append(page_id)
            existing_ids.add(page_id)
    elif item.is_file() and item.suffix == ".json":
        try:
            j = json.loads(item.read_text(encoding="utf-8"))
            page_id = j.get("name") or item.stem
            dest_file = pages_dir / f"{page_id}.json"
            if dest_file.exists():
                suffix = 2
                new_page_id = f"{page_id}_{suffix}"
                dest_file = pages_dir / f"{new_page_id}.json"
                page_id = new_page_id
            dest_file.write_text(json.dumps(j, indent=2), encoding="utf-8")
            if page_id not in existing_ids:
                pages_meta.setdefault("pageOrder", []).append(page_id)
                existing_ids.add(page_id)
        except Exception:
            continue

if not pages_meta.get("activePageName") and pages_meta.get("pageOrder"):
    pages_meta["activePageName"] = pages_meta["pageOrder"][0]

pages_metadata_path.write_text(json.dumps(pages_meta, indent=2), encoding="utf-8")

print('Copied pages to', target)
print('pages.json content:')
print(pages_metadata_path.read_text())

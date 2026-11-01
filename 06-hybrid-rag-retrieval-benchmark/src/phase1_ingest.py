#!/usr/bin/env python3
"""Phase 1: ingest policy PDFs, retain raw text, strip boilerplate, structure-chunk.

Colab: use --mount-drive with --input-dir set to a folder under /content/drive/MyDrive.
PDF discovery is recursive by default, including category subfolders. Locally: python phase1_ingest.py --input-dir ./pdfs
Dependencies: pypdf; optional PyMuPDF (fitz) is used as extraction fallback and
pandas + pyarrow (or fastparquet) enable Parquet output. CSV/JSONL always emit.
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, json, math, os, re, sys
from pathlib import Path
from typing import Any

CATEGORY_NAMES = {
    "C1": "Returns & Exchanges", "C2": "Shipping, Delivery & Tracking",
    "C3": "Orders, Payments & Subscriptions", "C4": "Warranty, Repairs & Technical Support",
    "C5": "Account Security & Privacy", "C6": "Customer Care & Escalations",
    "C7": "B2B Corporate & Trade",
}
# Lines matching these intentionally conservative rules are presentation-only.
BOILERPLATE_PATTERNS = [
    r"^NORTHSTAR SUPPLIES LTD\.?$",
    r"^Northstar Supplies Ltd\.?\s*[|·\x7f-].*(?:Internal Operational Policy|Page\s+\d+|Draft-only control).*$",
    r"^Pilot policy universe\s*[·|].*$",
    r"^(?:Page\s+\d+|Page\s+\d+\s*[·|].*)$",
    r"^C\d+\S*\s*[·|].*FICTIONAL TRAINING POLICY.*$",
    r"^FICTIONAL TRAINING POLICY\s*[—-]\s*NOT LEGAL ADVICE OR A LIVE COMPANY POLICY\.?$",
    r"^TRAINING / EVALUATION DATASET\s*[—-].*NOT LEGAL ADVICE OR A LIVE COMPANY POLICY\..*$",
    r"^FICTIONAL TRAINING\s*[|·].*HUMAN APPROVAL REQUIRED.*$",
    r"^CATEGORY\s+\d+\s*/.*$",
    r"^MANDATORY HUMAN REVIEW\s*/\s*SIGN-OFF$",
]
BOILERPLATE_RE = [re.compile(p, re.I) for p in BOILERPLATE_PATTERNS]
DISCLAIMER_RE = re.compile(
    r"^(?:This controlled scenario describes fictional|Controlled synthetic Northstar Supplies Ltd\.|"
    r"This draft does not authorise automatic|This document does not authorise automatic).{0,1200}$", re.I | re.S)
SIGNOFF_HEAD_RE = re.compile(r"^\s*(?:MANDATORY HUMAN REVIEW\s*/\s*SIGN-OFF|APPROVAL / SIGN-OFF|SIGN-OFF|APPROVAL RECORD)\s*$", re.I)
OWNER_ACK_RE = re.compile(r"^Owner acknowledgement\.?\s+The owner of .*?(?:fictional training scenario|substantive content above is specific to .*?)\.?$", re.I | re.S)
FILENAME_CODE_RE = re.compile(r"\b(C\d[A-Za-z0-9]*-D\d{1,2})\b", re.I)
SECTION_RE = re.compile(r"^\s*(?:(?:\d{1,2}\s*[.)·:-]\s+|0\d\s+[A-Z])|(?:SECTION|PART)\s+[A-Z0-9IVX]+\b|[A-Z][A-Z0-9 /&()_-]{3,}:\s*$)")


def normalize_line(s: str) -> str:
    s = s.replace("\x7f", " ").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip().casefold()


def extract_pdf(path: Path) -> tuple[list[str], dict[str, Any], str]:
    """Try PyMuPDF then pypdf; return page text, metadata, extractor label."""
    errors=[]
    try:
        import fitz
        d=fitz.open(str(path))
        pages=[p.get_text("text") or "" for p in d]
        md=dict(d.metadata or {})
        d.close()
        if any(x.strip() for x in pages): return pages, md, "pymupdf"
        errors.append("PyMuPDF returned no text")
    except Exception as e: errors.append(f"PyMuPDF: {e}")
    try:
        from pypdf import PdfReader
        r=PdfReader(str(path), strict=False)
        if r.is_encrypted:
            try: r.decrypt("")
            except Exception as e: raise RuntimeError(f"encrypted PDF: {e}")
        pages=[p.extract_text() or "" for p in r.pages]
        md={str(k).lstrip("/"): (str(v) if v is not None else "") for k,v in (r.metadata or {}).items()}
        if any(x.strip() for x in pages): return pages, md, "pypdf"
        errors.append("pypdf returned no text")
    except Exception as e: errors.append(f"pypdf: {e}")
    raise RuntimeError("; ".join(errors))


def detect_code(path: Path, text: str, md: dict) -> str:
    for source in (path.name, text[:2500]):
        m=FILENAME_CODE_RE.search(source)
        if m: return m.group(1).upper()
    # Useful document IDs in structured header fields, without guessing from arbitrary references.
    m=re.search(r"(?im)^\s*DOCUMENT\s+ID\s*\n\s*([^\n]+)", text[:4000])
    return m.group(1).strip() if m else ""


def metadata_for(path: Path, text: str, md: dict) -> dict[str, Any]:
    code=detect_code(path,text,md)
    catmatch=re.search(r"(?i)\b(C[1-7])", path.name) or re.search(r"(?i)\b(C[1-7])",code)
    category_code=catmatch.group(1).upper() if catmatch else ""
    title=str(md.get("title") or md.get("Title") or "").strip()
    # Use earliest plausible document heading as title if metadata is blank/unhelpful.
    lines=[re.sub(r"\s+"," ",x).strip() for x in text.splitlines() if x.strip()]
    if not title or title.casefold() in {path.stem.casefold(),"untitled"}:
        for i,line in enumerate(lines[:30]):
            if (len(line)>12 and not any(rx.match(line) for rx in BOILERPLATE_RE)
                and not re.match(r"^(?:CATEGORY|DOCUMENT ID|EFFECTIVE|OWNER|CONTROL|CLASSIFICATION|VERSION|PAGE)\b",line,re.I)
                and not DISCLAIMER_RE.match(line)):
                # In these layouts, a descriptive subheading may precede the title; metadata is preferable.
                title=line; break
    return {"doc_id": hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16],
            "source_file":path.name,"source_path":str(path),"category_code":category_code,
            "category":CATEGORY_NAMES.get(category_code, "Unclassified"),"title":title,
            "doc_code":code,"pdf_title":str(md.get("title") or md.get("Title") or ""),
            "pdf_author":str(md.get("author") or md.get("Author") or ""),
            "page_count":len(text.split("\f")) if text else 0}


def split_paragraphs(text: str) -> list[str]:
    # Page concatenation, PDF line-wraps, tables and bullets need separate treatment.
    # Keep labels/values linewise where likely tabular; join prose wraps elsewhere.
    blocks=[]
    for block in re.split(r"\n\s*\n+",text):
        lines=[re.sub(r"[ \t]+"," ",x).strip() for x in block.splitlines() if x.strip()]
        if not lines: continue
        def tableish(line):
            return ("\t" in line or bool(re.match(r"^(?:DOCUMENT ID|EFFECTIVE(?: DATE)?|OWNER(?: / SCOPE)?|SCOPE|CONTROL|VERSION|STATUS|CLASSIFICATION|ESCALATION PATH|APPLIES TO|FORM CODES|RETRIEVAL ANCHORS|OPERATING DAYS|LOOKUP SET|SERVICE / FEE RULE|CONTROL / DECISION POINT|OPERATIONAL STANDARD)\s*$",line,re.I))
                    or bool(re.match(r"^.{1,55}:\s+\S",line)))
        if any(tableish(x) for x in lines):
            blocks.extend(lines)
        elif len(lines)>1 and all(re.match(r"^[•▪■\-–\x7f]\s*",x) for x in lines):
            blocks.extend(lines)
        else:
            # Join extraction-wrapped prose unless the next line starts a numbered section or list.
            acc=""
            for line in lines:
                if acc and (re.match(r"^(?:\d{1,2}\s*[.)·:-]|[•▪■\-–\x7f]\s)",line) or SECTION_RE.match(line)):
                    blocks.append(acc); acc=line
                else: acc=(acc+" "+line).strip()
            if acc: blocks.append(acc)
    return blocks


def strip_boilerplate(raw_text: str, recurring: set[str]) -> tuple[str, list[str]]:
    removed=[]
    # Tail sign-off/owner acknowledgement sections are predictable controlled templates.
    # Cut only when an explicit sign-off/acknowledgement anchor is present.
    tail_markers = re.compile(r"(?im)^\s*(?:Owner acknowledgement\.?\s+The owner of |MANDATORY HUMAN REVIEW\s*/\s*SIGN-OFF\s*$|APPROVAL / SIGN-OFF\s*$|Verify current law, approved source records, delegated authority and customer-specific facts before use\.)")
    match=tail_markers.search(raw_text)
    if match:
        removed.append(raw_text[match.start():].strip()); raw_text=raw_text[:match.start()]
    # Paragraph-based removal handles wrapped and split disclaimer statements.
    disclaimer_fragments = (
        "preserves applicable statutory rights and does not claim that fictional terms override law",
        "document does not authorise automatic sending", "this draft does not authorise automatic customer contact",
        "no automatic sending or operational action is authorised", "operational action is authorised by this document",
        "no automatic sending or operational action", "this document does not authorise automatic sending",
        "applicable statutory rights are preserved", "applicable statutory rights are preserved. this document does not authorise",
        "verify current law, approved source records, delegated authority and customer-specific facts before use",
        "this controlled scenario describes fictional northstar supplies ltd.",
        "disclosure or other action.", "human review and sign-off are mandatory before operational use.",
        "preserves applicable statutory rights", "operational action is authorised by this document.",
        "operational action is authorised by this document", "not legal advice or a live company policy.",
    )
    # Remove matched lines before paragraph grouping because PDF extractors may put table
    # fields and boilerplate sentences in the same paragraph block.
    filtered=[]
    disclaimer_starts=("this controlled scenario describes fictional northstar supplies ltd.",
        "controlled synthetic northstar supplies ltd.","this draft does not authorise automatic",
        "this document does not authorise automatic customer", "training / evaluation dataset",
        "fictional training policy", "fictional training | human approval required")
    for line in raw_text.splitlines():
        s=line.strip(); norm=normalize_line(s)
        if not norm: filtered.append(""); continue
        if any(rx.match(s) for rx in BOILERPLATE_RE) or norm in recurring:
            removed.append(s); continue
        matched_disclaimer = DISCLAIMER_RE.match(s) or norm.startswith(disclaimer_starts) or any(fragment in norm for fragment in disclaimer_fragments)
        if matched_disclaimer:
            # A few PDF lines merge the boilerplate disclaimer tail with substantive policy text.
            substantive = re.search(r"(?:No intake or|Coverage does not|All customer-facing|All proposed remedies|A late arrival|Any refund remains|Applicable statutory rights)", s, re.I)
            if substantive:
                kept_tail=s[substantive.start():].strip()
                if kept_tail: filtered.append(kept_tail)
            removed.append(s); continue
        filtered.append(s)
    blocks=split_paragraphs("\n".join(filtered)); kept=[]
    for block in blocks:
        norm=normalize_line(block)
        if not norm: continue
        if any(rx.match(block.strip()) for rx in BOILERPLATE_RE) or norm in recurring:
            removed.append(block); continue
        if DISCLAIMER_RE.match(block.strip()) or any(fragment in norm for fragment in disclaimer_fragments):
            removed.append(block); continue
        kept.append(block)
    return "\n\n".join(kept).strip(),removed


def structure_chunks(doc: dict[str,Any], max_chars: int=1600, overlap_chars: int=180) -> list[dict[str,Any]]:
    text=doc["cleaned_text"]
    if not text: return []
    blocks=split_paragraphs(text)
    pieces=[]; section="Document overview"; current=[]
    for block in blocks:
        if SECTION_RE.match(block) and len(block)<180:
            if current: pieces.append((section,"\n\n".join(current))); current=[]
            section=block
            pieces.append((section,block)); continue
        current.append(block)
    if current: pieces.append((section,"\n\n".join(current)))
    # split oversize pieces along paragraph boundaries, then by characters as a last resort
    subpieces=[]
    for sec,body in pieces:
        if len(body)<=max_chars: subpieces.append((sec,body)); continue
        paras=body.split("\n\n"); buf=""
        for para in paras:
            if len(para)>max_chars:
                if buf: subpieces.append((sec,buf)); buf=""
                for start in range(0,len(para),max(1,max_chars-overlap_chars)):
                    subpieces.append((sec,para[start:start+max_chars]))
            elif len(buf)+len(para)+2>max_chars:
                if buf: subpieces.append((sec,buf))
                buf=para
            else: buf=(buf+"\n\n"+para).strip()
        if buf: subpieces.append((sec,buf))
    chunks=[]
    for idx,(sec,body) in enumerate(subpieces):
        context=f"[Doc: {doc['doc_code'] or doc['source_file']} | Category: {doc['category']} | Title: {doc['title']}]"
        chunks.append({"chunk_id":f"{doc['doc_id']}-{idx:04d}","doc_id":doc["doc_id"],
            "source_file":doc["source_file"],"category":doc["category"],"category_code":doc["category_code"],
            "title":doc["title"],"doc_code":doc["doc_code"],"chunk_index":idx,
            "section":sec,"text":context+"\n"+body,"body_text":body,
            "char_count":len(body),"token_estimate":max(1,math.ceil(len(body)/4))})
    return chunks


def write_jsonl(path: Path, rows):
    with path.open("w",encoding="utf-8") as f:
        for row in rows: f.write(json.dumps(row,ensure_ascii=False)+"\n")


def run(input_dir: Path, output_dir: Path, recursive: bool=True, max_chars: int=1600, overlap_chars: int=180):
    output_dir.mkdir(parents=True,exist_ok=True)
    files=sorted((input_dir.rglob("*.pdf") if recursive else input_dir.glob("*.pdf")),key=lambda p:str(p).casefold())
    if not files: raise FileNotFoundError(f"No PDFs found under {input_dir}")
    extracted=[]; failures=[]
    for path in files:
        try:
            pages,md,extractor=extract_pdf(path); raw="\n\n".join(x.strip() for x in pages if x and x.strip())
            record=metadata_for(path,raw,md); record.update({"raw_text":raw,"extractor":extractor,"metadata":md,
                "page_texts":pages,"extraction_chars":len(raw),"extraction_status":"ok" if raw.strip() else "empty"})
            extracted.append(record)
        except Exception as e: failures.append({"source_file":path.name,"source_path":str(path),"error":str(e)})
    # Discover frequent standalone banners across distinct files, avoiding one-document repetition bias.
    occurrences=collections.Counter()
    banner_hints=("northstar", "fictional", "training", "evaluation dataset", "internal operational policy",
                  "draft-only control", "not legal advice", "page ", "human review / sign-off", "automatic sending")
    for d in extracted:
        seen={normalize_line(x) for x in d["raw_text"].splitlines()
              if len(normalize_line(x))>=12 and any(hint in normalize_line(x) for hint in banner_hints)}
        occurrences.update(seen)
    threshold=max(3,math.ceil(0.08*len(extracted)))
    recurring={line for line,n in occurrences.items() if n>=threshold}
    clean_docs=[]; chunks=[]
    for d in extracted:
        cleaned,removed=strip_boilerplate(d["raw_text"],recurring)
        d["cleaned_text"]=cleaned; d["removed_boilerplate_count"]=len(removed)
        d["removed_boilerplate_samples"]=removed[:20]; d["cleaned_chars"]=len(cleaned)
        clean_docs.append(d); chunks.extend(structure_chunks(d,max_chars,overlap_chars))
    # Persist both full-fidelity source records and phase-2-ready chunks.
    write_jsonl(output_dir/"raw_documents.jsonl",extracted)
    write_jsonl(output_dir/"cleaned_documents.jsonl",clean_docs)
    write_jsonl(output_dir/"chunks.jsonl",chunks)
    flat_docs=[{k:v for k,v in d.items() if k not in ("page_texts","metadata")} for d in clean_docs]
    def csv_write(path, rows):
        if not rows: return
        keys=list(dict.fromkeys(k for r in rows for k in r.keys()))
        with path.open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore"); w.writeheader()
            for r in rows:
                w.writerow({k:(json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v) for k,v in r.items()})
    csv_write(output_dir/"chunks.csv",chunks)
    # Parquet is best-effort to keep base dependencies small.
    parquet_status="not written (install pandas and pyarrow or fastparquet)"
    try:
        import pandas as pd
        try:
            pd.DataFrame(chunks).to_parquet(output_dir/"chunks.parquet",index=False); parquet_status="written"
        except Exception as e: parquet_status=f"not written: {e}"
    except ImportError: pass
    lengths=[c["char_count"] for c in chunks]
    validation={"pdfs_discovered":len(files),"documents_extracted":len(extracted),"extraction_failures":failures,
      "documents_with_text":sum(bool(d["raw_text"].strip()) for d in extracted),"chunks":len(chunks),
      "empty_cleaned_documents":[d["source_file"] for d in clean_docs if not d["cleaned_text"]],
      "missing_doc_code":[d["source_file"] for d in clean_docs if not d["doc_code"]],
      "missing_title":[d["source_file"] for d in clean_docs if not d["title"]],
      "context_header_check":all(c["text"].startswith("[Doc: ") for c in chunks),
      "chunk_char_count":{"min":min(lengths) if lengths else 0,"median":sorted(lengths)[len(lengths)//2] if lengths else 0,
        "mean":round(sum(lengths)/len(lengths),1) if lengths else 0,"max":max(lengths) if lengths else 0},
      "chunks_per_document":{"min":min(collections.Counter(c["doc_id"] for c in chunks).values(),default=0),
        "max":max(collections.Counter(c["doc_id"] for c in chunks).values(),default=0),
        "mean":round(len(chunks)/len(clean_docs),2) if clean_docs else 0},
      "boilerplate_frequency_threshold_docs":threshold,"parquet":parquet_status,
      "output_files":["raw_documents.jsonl","cleaned_documents.jsonl","chunks.jsonl","chunks.csv"]+( ["chunks.parquet"] if parquet_status=="written" else [])}
    (output_dir/"validation_report.json").write_text(json.dumps(validation,indent=2,ensure_ascii=False),encoding="utf-8")
    # Hard validation invariants; empty-text PDFs are reported but not fatal.
    assert len(extracted)+len(failures)==len(files),"discovery accounting mismatch"
    assert all(c["doc_id"] and c["chunk_id"] and c["text"].startswith("[Doc: ") for c in chunks),"invalid chunk metadata/context"
    assert len({c["chunk_id"] for c in chunks})==len(chunks),"duplicate chunk IDs"
    return validation


def in_colab_mount():
    try:
        from google.colab import drive
        drive.mount("/content/drive")
        return Path("/content/drive/MyDrive")
    except ImportError:
        return None


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir",default=os.environ.get("PDF_INPUT_DIR"),help="Folder containing PDFs (recursive by default)")
    ap.add_argument("--output-dir",default=os.environ.get("PHASE1_OUTPUT_DIR","phase1_output"))
    ap.add_argument("--no-recursive",action="store_true")
    ap.add_argument("--max-chars",type=int,default=1600)
    ap.add_argument("--overlap-chars",type=int,default=180)
    ap.add_argument("--mount-drive",action="store_true",help="Mount Google Drive in Colab; combine with --input-dir to select a PDF folder under MyDrive")
    args=ap.parse_args()
    input_dir=Path(args.input_dir) if args.input_dir else None
    if args.mount_drive:
        mounted=in_colab_mount()
        if mounted is None: ap.error("--mount-drive requires Google Colab; use --input-dir locally")
        if input_dir is None: ap.error("With --mount-drive, also provide --input-dir under /content/drive/MyDrive")
    if input_dir is None: ap.error("Provide --input-dir, set PDF_INPUT_DIR, or use --mount-drive in Colab")
    result=run(input_dir,Path(args.output_dir),not args.no_recursive,args.max_chars,args.overlap_chars)
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__": main()

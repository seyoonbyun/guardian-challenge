# -*- coding: utf-8 -*-
"""BNI Connect 등록 기준으로 guardian-bnikorea.com 의 지역·챕터 목록(chapters.js)을 자동으로 채운다.

하는 일 (매시간 예약작업 `Guardian Chapter Sync` 가 --apply 로 실행):
  1. BNI Connect `챕터 보기/관리` 를 전 지역 수집 (bni-chapter-master-create/scrape_chapters.py 재사용)
  2. 상태 `활동중` 챕터 중 사이트(chapters.js)에 없는 지역·챕터를 찾는다
  3. 있으면 chapters.js 에 **추가**하고 커밋·푸시 → Vercel 이 자동 배포
     · invite 의 지역·챕터 드롭다운 3개와 대시보드 지역별 챕터 명단이 이 파일을 읽는다
  4. 라이브에 반영됐는지 확인하고 문자로 알린다

원칙
  - **추가만 한다.** 정지·폐쇄돼도 사이트 목록에서 빼지 않는다(기존 등록 데이터·수동 사전 등록 보호). 보고만 한다.
  - Connect 챕터명은 영문(`Pinnacle`), 사이트는 한글(`피너클`).
    한글명 = names.json 의 manual → 최신 챕터 마스터 `ALL 챕터` 시트(챕터명 Eng/Kor) 순으로 찾는다.
    아직 한글명이 어디에도 없으면 **영문명 그대로 즉시 추가**하고, 나중에 한글명이 확인되면 자동으로 바꾼다
    (바꾼 이름은 chapters.js `alias` 에 남겨 대시보드가 옛 영문 등록을 한글 쪽으로 합산).
  - 사이트 표기 규칙: 지역 끝 숫자 제거(`수원1`→`수원`) · `센트럴`→저장값 `중구`(화면 `센트럴(중구)`) · `디백`→`D100`.
  - 수집이 덜 됐거나(지역·챕터 수 급감) 한 번에 너무 많이 늘면 아무것도 쓰지 않고 실패로 알린다.

사용
  python sync_chapters.py                      # 수집 + 차이만 출력 (아무것도 안 씀)
  python sync_chapters.py --apply              # 추가 → 커밋·푸시 → 라이브 확인 → 문자
  python sync_chapters.py --connect-json FILE  # 수집 생략(이미 받은 JSON 으로)
  python sync_chapters.py --apply --no-push    # chapters.js 만 고치고 커밋·푸시 안 함 (로컬 미리보기용)
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.platform == "win32":
    for _s in ("stdout", "stderr"):
        try:
            getattr(sys, _s).reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA_JS = REPO / "chapters.js"
NAMES = HERE / "names.json"
RUN_DIR = HERE / "_run"                      # 로그·수집 원본·상태 (git 에 올리지 않는다)
STATE = RUN_DIR / "state.json"

SCRAPER = Path(r"C:\Users\Gram\.claude\skills\bni-chapter-master-create\scrape_chapters.py")
MASTER_ROOT = Path(r"C:\Users\Gram\Desktop\connect_tl_report")
SOLAPI_CFG = MASTER_ROOT / "connect" / "solapi.json"
STATS_WRAPPER = Path(r"C:\Users\Gram\scripts\daily_korea_stats.py")   # 알림 받을 번호(ALERT_PHONE)를 여기서 읽는다
LIVE_URL = "https://www.guardian-bnikorea.com/chapters.js"

REGION_VALUE = {"센트럴": "중구"}            # Connect 한글 지역명 → 사이트 저장값
REGION_LABEL = {"중구": "센트럴(중구)"}      # 저장값 → 화면 표기
CHAPTER_VALUE = {"디백": "D100"}             # 마스터 한글명 → 사이트 표기

MIN_REGIONS = 15          # 이보다 적게 수집되면 수집 실패로 본다
MIN_ACTIVE = 80
MAX_NEW_CHAPTERS = 8      # 한 번에 이보다 많이 늘면 이상 징후 (—force 로만 통과)
MAX_NEW_REGIONS = 2
KST = timezone(timedelta(hours=9))


def log(msg: str = "") -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


class Abort(Exception):
    pass


# ───────────────────────── chapters.js 읽기·쓰기
def load_site() -> dict:
    txt = DATA_JS.read_text(encoding="utf-8")
    m = re.search(r"window\.BNI_CHAPTERS\s*=\s*(\{.*\})\s*;\s*$", txt, re.S)
    if not m:
        raise Abort("chapters.js 형식을 읽지 못했습니다")
    d = json.loads(m.group(1))
    for k in ("regions", "roster"):
        if not d.get(k):
            raise Abort(f"chapters.js 에 {k} 가 비어 있습니다")
    d.setdefault("alias", {})
    return d


def chapter_sort_key(name: str):
    return (0 if re.match(r"[A-Za-z0-9]", name) else 1, name.casefold())


def render(d: dict) -> str:
    d["chapters"] = sorted({c for v in d["roster"].values() for c in v}, key=chapter_sort_key)
    out = {
        "updated": d["updated"],
        "source": "BNI Connect 챕터 보기/관리 (활동중) — automation/connect_sync/sync_chapters.py",
        "regions": d["regions"],
        "chapters": d["chapters"],
        "roster": d["roster"],
        "alias": d["alias"],
    }
    lines = ["// 자동 생성 파일 — BNI Connect 등록 기준으로 지역·챕터가 추가된다 (automation/connect_sync).",
             "// 손으로 고쳐도 되지만 형식(JSON)은 지킬 것. invite 드롭다운과 대시보드 챕터 명단이 이 파일을 읽는다.",
             "window.BNI_CHAPTERS = " + json.dumps(out, ensure_ascii=False, indent=1) + ";", ""]
    return "\n".join(lines)


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    json.loads(re.search(r"=\s*(\{.*\})\s*;\s*$", text, re.S).group(1))   # 쓰기 전에 다시 읽히는지 확인
    os.replace(tmp, path)


# ───────────────────────── 이름 변환
def strip_digits(s: str) -> str:
    return re.sub(r"\d+$", "", (s or "").strip())


def norm_eng(s: str) -> str:
    return re.sub(r"[\s\-_.]", "", (s or "")).casefold()


def site_region(kor: str) -> str:
    k = strip_digits(kor)
    return REGION_VALUE.get(k, k)


def latest_master() -> Path | None:
    try:
        fs = [p for p in MASTER_ROOT.glob("*트래픽 라이트 작업/*Chapter Master Origin*.xlsx")
              if "백업" not in p.name and not p.name.startswith("~$")]
    except Exception:
        return None
    return max(fs, key=lambda p: p.stat().st_mtime) if fs else None


def master_names() -> tuple[dict, str]:
    """챕터 마스터 `ALL 챕터` → {"지역|영문": 한글}. 같은 키가 여럿이면 활동중 행을 우선한다."""
    p = latest_master()
    if not p:
        return {}, ""
    import openpyxl
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb["ALL 챕터"]
    rows = ws.iter_rows(values_only=True)
    head = [str(c or "").strip() for c in next(rows)]
    ix = {h: i for i, h in enumerate(head)}
    need = ["챕터명(Eng)", "챕터명(Kor)", "지역(Kor)", "상태"]
    if any(n not in ix for n in need):
        raise Abort(f"챕터 마스터 머리글이 바뀌었습니다: {p.name}")
    out, rank = {}, {}
    for r in rows:
        eng, kor = (str(r[ix["챕터명(Eng)"]] or "").strip(), str(r[ix["챕터명(Kor)"]] or "").strip())
        if not eng or not kor or not re.search(r"[가-힣]", kor) and not re.match(r"^[A-Za-z0-9 ]+$", kor):
            continue
        key = f"{site_region(str(r[ix['지역(Kor)']] or ''))}|{norm_eng(eng)}"
        score = 2 if str(r[ix["상태"]] or "").strip() == "활동중" else 1
        if score > rank.get(key, 0):
            out[key], rank[key] = kor, score
    wb.close()
    return out, p.name


def load_names() -> dict:
    if NAMES.exists():
        d = json.loads(NAMES.read_text(encoding="utf-8"))
    else:
        d = {}
    d.setdefault("manual", {})
    d.setdefault("master", {})
    return d


def refresh_names(names: dict) -> bool:
    """마스터에서 읽힌 한글명을 names.json 에 쌓는다(마스터를 못 읽는 PC·시점에도 쓰게). 바뀌면 True."""
    try:
        fresh, src = master_names()
    except Abort:
        raise
    except Exception as e:
        log(f"  ⚠ 챕터 마스터를 읽지 못했습니다(저장된 이름표로 진행): {e!r}")
        return False
    if not fresh:
        log("  ⚠ 챕터 마스터 파일이 없습니다(저장된 이름표로 진행)")
        return False
    merged = dict(names["master"])
    merged.update(fresh)
    changed = merged != names["master"]
    names["master"] = dict(sorted(merged.items()))
    names["master_source"] = src
    log(f"  한글명 표: {src} → {len(fresh)}건 (누적 {len(merged)}건)")
    return changed


def kor_name(names: dict, region: str, eng: str) -> str | None:
    """한글명을 찾으면 사이트 표기로, 못 찾으면 None. Connect 이름이 이미 한글이면 그대로."""
    eng = (eng or "").strip()
    if re.search(r"[가-힣]", eng):
        return CHAPTER_VALUE.get(eng, eng)
    key = f"{region}|{norm_eng(eng)}"
    for table in (names["manual"], names["master"]):
        if key in table:
            k = table[key].strip()
            return CHAPTER_VALUE.get(k, k)
    return None


# ───────────────────────── Connect 수집
def scrape(out: Path) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()                      # 옛 결과를 새 결과로 착각하지 않게
    log("BNI Connect 수집 시작")
    p = subprocess.run([sys.executable, "-X", "utf8", "-u", str(SCRAPER), "--out", str(out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40 * 60)
    tail = "\n".join((p.stdout or "").strip().splitlines()[-6:])
    log(tail)
    if p.returncode != 0 or not out.exists():
        raise Abort(f"Connect 수집 실패(종료코드 {p.returncode}): {(p.stderr or '')[-300:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def check_scrape(data: dict) -> list[dict]:
    if data.get("errors"):
        raise Abort(f"지역 {len(data['errors'])}곳 수집 실패: {[e['region'] for e in data['errors']]}")
    regions = data.get("regions") or []
    active = [c for c in data.get("chapters") or [] if c.get("status") == "활동중" and c.get("chapter")]
    if len(regions) < MIN_REGIONS or len(active) < MIN_ACTIVE:
        raise Abort(f"수집이 덜 됐습니다: 지역 {len(regions)} · 활동중 {len(active)}")
    return active


# ───────────────────────── 차이 계산
def build_plan(site: dict, active: list[dict], names: dict) -> dict:
    roster = site["roster"]
    region_values = {r["value"] for r in site["regions"]}
    where = {}                                    # 사이트 챕터명 → 지역들
    for rg, chs in roster.items():
        for c in chs:
            where.setdefault(c, set()).add(rg)

    plan = {"new_regions": [], "new_chapters": [], "renames": [], "holds": [], "english": [],
            "not_active": [], "active": len(active)}
    seen = set()
    for c in active:
        rg = site_region(c["region_kor"])
        eng = c["chapter"].strip()
        kor = kor_name(names, rg, eng)
        name = kor or eng
        seen.add((rg, name))
        if rg not in region_values and rg not in [r["value"] for r in plan["new_regions"]]:
            plan["new_regions"].append({"value": rg, "label": REGION_LABEL.get(rg, rg),
                                        "en": re.sub(r"[^A-Z ]", "", strip_digits(c["region_eng"]).upper()).strip()})
        if name in roster.get(rg, []):
            continue
        if kor and eng in roster.get(rg, []) and not re.search(r"[가-힣]", eng):
            plan["renames"].append({"region": rg, "from": eng, "to": kor})   # 영문으로 먼저 올린 것을 한글로
            continue
        if name in where:
            plan["holds"].append(f"{rg} {name}: 사이트에는 {'/'.join(sorted(where[name]))} 지역에 있음 (Connect 는 {c['region_label']})")
            continue
        plan["new_chapters"].append({"region": rg, "name": name, "eng": eng, "launch": c.get("launch_date_iso", "")})
        if not kor:
            plan["english"].append(f"{rg} {eng}")
    for rg, chs in roster.items():
        for ch in chs:
            if (rg, ch) not in seen:
                plan["not_active"].append(f"{rg} {ch}")
    return plan


def apply_plan(site: dict, plan: dict) -> None:
    for r in plan["new_regions"]:
        site["regions"].append(r)
    for c in plan["new_chapters"]:
        site["roster"].setdefault(c["region"], []).append(c["name"])
    for r in plan["renames"]:
        lst = site["roster"][r["region"]]
        lst[lst.index(r["from"])] = r["to"]
        site["alias"][r["from"]] = r["to"]
    for rg in site["roster"]:
        site["roster"][rg] = sorted(set(site["roster"][rg]), key=chapter_sort_key)
    site["updated"] = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S+09:00")


def describe(plan: dict) -> list[str]:
    L = []
    for r in plan["new_regions"]:
        L.append(f"지역 추가: {r['label']}")
    for c in plan["new_chapters"]:
        L.append(f"챕터 추가: {c['region']} {c['name']}" + (f" (런칭 {c['launch']})" if c["launch"] else ""))
    for r in plan["renames"]:
        L.append(f"한글명 교체: {r['region']} {r['from']} → {r['to']}")
    return L


# ───────────────────────── git · 라이브 · 알림
def git(*args: str, check: bool = True) -> str:
    p = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise Abort(f"git {' '.join(args[:2])} 실패: {(p.stderr or p.stdout).strip()[-300:]}")
    return (p.stdout or "").strip()


def git_sync_before() -> None:
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise Abort("저장소가 main 브랜치가 아닙니다")
    git("fetch", "origin", "main")
    behind = int(git("rev-list", "--count", "HEAD..origin/main") or 0)
    if behind:
        git("merge", "--ff-only", "origin/main")
        log(f"  원격 변경 {behind}건을 먼저 받았습니다")


def git_publish(message: str, paths: list[Path]) -> str:
    rel = [str(p.relative_to(REPO)).replace("\\", "/") for p in paths if p.exists()]
    git("add", "--", *rel)                                    # ⛔ add -A 금지 (로컬에 지워진 자산이 있다)
    if not git("diff", "--cached", "--name-only", "--", *rel):
        return ""
    git("commit", "-m", message, "--", *rel)
    git("push", "origin", "main")
    return git("rev-parse", "--short", "HEAD")


def wait_live(stamp: str, timeout_s: int = 420) -> bool:
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            req = urllib.request.Request(f"{LIVE_URL}?nc={int(time.time())}",
                                         headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=30) as r:
                if stamp in r.read().decode("utf-8", errors="replace"):
                    return True
        except Exception:
            pass
        time.sleep(15)
    return False


def alert_phone() -> str:
    m = re.search(r'ALERT_PHONE\s*=\s*"(\d+)"', STATS_WRAPPER.read_text(encoding="utf-8"))
    return m.group(1)


def send_sms(text: str) -> bool:
    try:
        cfg = json.loads(SOLAPI_CFG.read_text(encoding="utf-8"))
        text = text.strip()
        long = sum(2 if ord(c) > 127 else 1 for c in text) > 90
        msg = {"to": alert_phone(), "from": re.sub(r"\D", "", cfg["sender"]), "text": text,
               "type": "LMS" if long else "SMS"}
        if long:
            msg["subject"] = "+1 챌린지 지역·챕터"
        date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        salt = os.urandom(16).hex()
        sig = hmac.new(cfg["api_secret"].encode(), (date + salt).encode(), hashlib.sha256).hexdigest()
        req = urllib.request.Request(
            "https://api.solapi.com/messages/v4/send", method="POST",
            data=json.dumps({"message": msg}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"HMAC-SHA256 apiKey={cfg['api_key']}, date={date}, salt={salt}, signature={sig}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            log(f"  문자 발송 {r.status}")
        return True
    except Exception as e:
        log(f"  문자 발송 실패: {type(e).__name__}")
        return False


def read_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_state(st: dict) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, STATE)


# ───────────────────────── 본체
def run(a: argparse.Namespace) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if a.apply and not a.no_push:
        git_sync_before()
    site = load_site()
    names = load_names()
    names_changed = refresh_names(names)

    if a.connect_json:
        data = json.loads(Path(a.connect_json).read_text(encoding="utf-8"))
    else:
        data = scrape(RUN_DIR / "connect_chapters.json")
    active = check_scrape(data)
    plan = build_plan(site, active, names)

    n_site = sum(len(v) for v in site["roster"].values())
    log(f"Connect 활동중 {plan['active']} · 사이트 지역 {len(site['regions'])} / 챕터 {n_site}")
    changes = describe(plan)
    for line in changes:
        log("  + " + line)
    for h in plan["holds"]:
        log("  ? 보류(지역 불일치): " + h)
    if plan["english"]:
        log("  ! 한글명 미확인 → 영문명으로 올림: " + ", ".join(plan["english"]))
    if plan["not_active"]:
        log("  · 사이트에만 있음(빼지 않음): " + ", ".join(plan["not_active"]))
    if not changes:
        log("추가할 지역·챕터 없음")

    if (len(plan["new_chapters"]) > MAX_NEW_CHAPTERS or len(plan["new_regions"]) > MAX_NEW_REGIONS) and not a.force:
        raise Abort(f"한 번에 지역 {len(plan['new_regions'])}·챕터 {len(plan['new_chapters'])}개가 늘어 이상 징후로 보고 멈춥니다")

    if not a.apply:
        log("(확인만 — 아무것도 쓰지 않았습니다. 반영은 --apply)")
        return 0

    st = read_state()
    st["last_ok_at"] = datetime.now(KST).isoformat(timespec="seconds")
    st.pop("fail_alerted", None)
    st["fails"] = 0
    if names_changed:
        NAMES.write_text(json.dumps(names, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not changes:
        if names_changed and not a.no_push:
            git_publish("connect_sync: 한글명 표 갱신", [NAMES])
        hold_key = "|".join(plan["holds"])
        if plan["holds"] and st.get("hold_alerted") != hold_key:
            send_sms("[+1 챌린지] 자동 추가 보류(지역 불일치)\n" + "\n".join(plan["holds"]))
            st["hold_alerted"] = hold_key
        write_state(st)
        return 0

    before = {(rg, c) for rg, v in site["roster"].items() for c in v}
    apply_plan(site, plan)
    after = {(rg, c) for rg, v in site["roster"].items() for c in v}
    lost = before - after - {(r["region"], r["from"]) for r in plan["renames"]}
    if lost:
        raise Abort(f"기존 항목이 사라지려 합니다(쓰지 않음): {sorted(lost)}")
    write_atomic(DATA_JS, render(site))
    log(f"chapters.js 갱신: 지역 {len(site['regions'])} / 챕터 {len(after)}")
    if a.no_push:
        log("(--no-push: 커밋·푸시 안 함)")
        return 0

    sha = git_publish("지역·챕터 자동 추가 (BNI Connect 기준): " + " · ".join(c.split(": ", 1)[1] for c in changes),
                      [DATA_JS, NAMES])
    log(f"푸시 완료 {sha} → 라이브 반영 대기")
    live = wait_live(site["updated"])
    log("라이브 반영 확인" if live else "⚠ 7분 안에 라이브 반영을 확인하지 못했습니다")
    msg = ["[+1 챌린지] Connect 기준 자동 추가" + ("" if live else " (라이브 반영 미확인)")] + changes
    if plan["english"]:
        msg.append("※ 한글명 미확인이라 영문명으로 올림: " + ", ".join(plan["english"]) + " (챕터 마스터에 한글명이 들어오면 자동 교체)")
    if plan["new_regions"]:
        msg.append("※ 새 지역은 목록·명단에는 바로 나오고, 대시보드 지도 위치는 따로 넣어야 합니다")
    if plan["holds"]:
        msg.append("보류: " + " / ".join(plan["holds"]))
    send_sms("\n".join(msg))
    write_state(st)
    return 0 if live else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--connect-json")
    ap.add_argument("--force", action="store_true", help="한 번에 많이 늘어도 진행")
    a = ap.parse_args()
    log(f"==== connect_sync {'apply' if a.apply else 'dry-run'} ====")
    try:
        return run(a)
    except Exception as e:
        why = str(e) if isinstance(e, Abort) else f"{type(e).__name__}: {e}"
        log(f"중단: {why}")
        if a.apply:
            st = read_state()
            fails = st.get("fails", 0) + 1
            st["fails"] = fails
            today = datetime.now(KST).strftime("%Y-%m-%d")
            # 일시 오류로 매시간 문자가 오지 않게: 3회 연속 실패했을 때 하루 한 번만 알린다
            if fails >= 3 and st.get("fail_alerted") != today:
                send_sms(f"[+1 챌린지] 지역·챕터 자동 확인이 {fails}회 연속 실패\n사유: {why[:150]}")
                st["fail_alerted"] = today
            write_state(st)
        return 1


if __name__ == "__main__":
    sys.exit(main())

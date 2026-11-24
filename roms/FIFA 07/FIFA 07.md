# FIFA 07 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/FIFA 07/FIFA 07.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `FIFA 07` (0xA0) |
| Game code / maker | `B7FE` / `69` (0xAC / 0xB0) |
| Version | 0 (0xBC) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; not a cracktro) |
| Header checksum / complement | stored `0x0000` / `0x41` (nonstandard but common commercial build; logo and title intact) |
| MD5 | `bf4a0f61e2e78a120ba1edd4cfa6a101` |
| SHA-1 | `ad593a9bdbe8b4ee3fd3b8fea66c06fcb6a66534` |
| SHA-256 | `1e3726c0f96a363a1d994472e47d4e730b011857a0a0d3a7cd8fd737830c90be` |

Embedded GBA-header scan: the 156-byte Nintendo logo occurs **once**, at file offset `0x4`. Single
image, no multiboot shell, no appended trainer (tail is `0xFF`-filled). This is the retail image,
not a patched/scene release.

Relation to the concurrently-analysed FIFA 06: the two ROMs are **different images** (FIFA 06 MD5
`13682a498effaef25aaaad9ac02cb4c0`), but they share the same EA/Exient front-end engine: 14,375
unique ASCII strings are common to both (of 28,794 in FIFA 07), including every `password`,
`Challenge`, `Rewards` and `Unlock` string, and both contain the leftover literal
`FIFA Football 2005` (FIFA 07 at `0x76dff4`; FIFA 06 at decimal `8075749`). All conclusions below
were re-derived independently on this image (own hashes, own screen walk, own xrefs); nothing was
copied from the sibling report. The shared-engine fact means the *negative* result is expected to
hold for FIFA 06 too, but that is the sibling's claim to prove.

## 2. Executive summary

**FIFA 07 GBA has no in-game cheat-code system**: no password-entry screen, no button-code
validator, no cheat/debug menu, and no code literal table. There is nothing to mint or enumerate
in the password sense — the code space is empty (size 0). Every screen reachable from a fresh boot
was walked (language select → title/sponsors → favourite team → main menu → Game Modes,
Challenges, Multiplayer, My FIFA 07 → team select → match → pause) with screenshots and mGBA
savestate/RAM evidence; none exposes a text or button input surface for cheats.

What looks like a password system in `strings` is **EA online-account UI** (`Username`,
`New Password`, `Old Password`, `Retrieve Password`, `Getting challenge question`, `Checking IMEI`,
`Invalid Billing DLL`). These strings are shared with FIFA 06 and are dead on GBA hardware (no
online service / billing DLL). They are account credentials, not game cheats, and were verified as
such by walking all reachable menus — no screen reaches them.

The only developer-intended unlockables are **gameplay rewards stored in the 512-byte EEPROM save**
(a save-bit system, §16.18), not codes. Published GBA "cheats" are exactly this reward list
("Challenge Mode: win five games", "Classic Team: complete Challenge Mode", stadium upgrades,
mini-games). The GBA image has **no boots / Fan Shop** feature (console/DS-only): `grep -i boot`
finds only the player surname `Booth` and `Marchant`.

## 3. How to reproduce

* Emulator: mGBA (SDL build) under `Xvfb :316`, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `mgba -3`.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
  Hold keys 100–300 ms (guide §4.2). GPU/CPU: `openbox` on :316 to keep focus.
* Boot path: language select (4 flags UK/DE/FR/ES) → Down/A picks a language → EA splash →
  FIFA 07 title (auto-advances; **no Press-Start menu**) → sponsor wall → "Choose Your Favourite
  Team" → A → Main Menu.
* Menu path used for the full walk:
  * Main Menu: Kick Off, Game Modes, Challenges, Multiplayer, My FIFA 07.
  * Game Modes → Career (2 intro pages, Season 1 objectives) and Tournament.
  * Challenges → Select Challenge (team list with difficulty stars).
  * Multiplayer → "Connect all Players".
  * My FIFA 07 → Game Settings/"Game Options" (Injuries, Bookings, Half Length, Extra Time,
    Pitch Type, Wind, Auto Apply), Control Options, Favourite Team, Language, Credits,
    Trophy Room (cup list).
  * Kick Off → Select Home/Away Team → control settings → live match → Start → Pause Menu
    (Resume, Team Management, Instant Replay, Match Statistics, Game Settings, Quit Match).
* Screenshots and savestates captured for every step (`shot_*.png`, `crop_*.png`, `st_*.ss1` in
  `/tmp/fifa07`). Savestates were taken with Shift+F2 and parsed per §16.13.
* Codes tested: Konami sequence `↑↑↓↓←→←→BA` at the pause menu and at the title screen; `L+R+Start`
  family. All produced only normal menu navigation / match resume — no cheat state.

## 4. Address map

| Item | Address / file offset | Evidence |
|---|---|---|
| Nintendo logo / header | `0x4` (only hit) | Derived (byte scan) |
| ASCII UI text bank | `0x230000`–`0x793000` (64,796 strings) | Observed (`strings -t x`) |
| Localized string pointer arrays (4 languages) | `0x751800`–`0x756200` | Derived (u32 pointer dump) |
| `You have unlocked the Classic XI team` | ptr at `0x756140` → `0x0875a270` | Derived (unique xref) |
| `You have unlocked the Custom Challenge!` | ptr at `0x751a90` → `0x08773ed8` | Derived |
| `You have unlocked an Historic %s Challenge!` | ptr at `0x751aa0` → `0x08773e28` | Derived |
| `Rewards` | ptr at `0x755490` → `0x08762304` | Derived |
| `My FIFA 07` | ptr at `0x7551a0` → `0x08763724` | Derived |
| `Choose a Challenge` | ptr at `0x756130` → `0x0875a2b4` | Derived |
| `Main Menu` / `PULSA START` run | `0x76ab28` (plain ASCII NUL strings) | Observed (raw bytes) |
| Leftover `FIFA Football 2005` | `0x76dff4` | Observed |
| Assert screen strings (`---- Assert Error ----`) | `0x2534c4` | Observed |
| `../savegame.c` source tag | `0x279668`; code refs `0x08062088`, `0x08063114`, `0x080631d0` | Derived |
| EEPROM save | 512 bytes; `game.sav` `0x00` counter, `0x04` checksum, `0x33=0x25`, `0x38+ = 0xFF` | Observed |
| Screen-state pointer (EWRAM) | `0x02000104`: `0x0823c0f0` team-select, `0x0823c100` menus, `0x0823c048` pause, `0x0` in-match | Observed (savestate RAM) |
| Monotonic counter (not a screen ID) | `0x030056f4` / `0x0300570c` (rises over session) | Observed |
| Savestate RAM layout (`gbAs` zlib chunk, 397,312 B) | EWRAM `0x02000000`→file `0x21000`; IWRAM `0x03000000`→`0x19000`; VRAM `0x06000000`→`0x1000` | Derived + validated |

## 5. Algorithm

No password validator, checksum, key table or button matcher exists in this image. There is no
algorithm to reimplement. The relevant *state* algorithm is the save-bit reward system:

```
reward_state = eeprom[0x00..0x3F]          # 512-byte EEPROM, mostly 0xFF when fresh
for each published reward R (14 entries):
    bit_R = test_bit(reward_state, bit_index[R])   # setter called only from career/challenge completion
    if bit_R: show R as Unlocked in Rewards screen
```

Evidence type: **Inferred** for the exact bit indices (the setter was not exhaustively traced);
**Observed** that the save is 512 bytes of EEPROM and that unlock messages exist in the ROM with
single localized-string xrefs; **Derived** that those messages are data-driven from a 4-language
pointer-array table.

## 6. Tables

**Text/button search counts (Phase 1 & 3/4):**

| Search | Count | Classification |
|---|---|---|
| Total ASCII strings (`strings -t x -n 4`) | 64,796 | UI + engine + player-name DB |
| `password` (case-insensitive lines) | 18 | all EA online-account UI (username/IMEI/billing/challenge question) |
| `unlock`/`Unlocked` | 8 | challenge/Classic-XI save-bit rewards |
| `cheat` | 0 | — |
| `secret` | 1 | `Secreto`, a player surname in a Belgian player-name list (`0x5da458`) — false positive (§16.8/16.11) |
| `debug` | 0 | only the generic `---- Assert Error ----` at `0x2534c4` |
| `boots` / `fan shop` / `giant team flag` / `stadium upgrade` | 0 | console/DS-only features absent from GBA |
| Fixed-length code-table candidates (regex runs of NUL-separated uppercase tokens) | 120 | all compressed-data garbage (`PUU`, `VUU`, …) |
| Uppercase alnum NUL-terminated tokens len 4–16 | 970 | no code-table structure; max length 16, no two-sided table |
| Konami/`EA classic`/`L+R+Start` key masks (active-high **and** active-low u16, and 1-byte-per-press) | 0 hits each | no button-code table |
| Distinct 3-press active-high prefixes present | 113 / 729 | random data baseline; no concentrated table |

**Published codes verified against the ROM (§16.7):**

| Source | Claim | ROM result |
|---|---|---|
| SuperCheats GBA | "there are no tap in cheat codes" — 14 gameplay rewards | Confirmed: no code surface; reward strings present |
| GameFAQs GBA cheats (403; recovered via search snippet) | same unlockable-reward list | Consistent |
| Console versions (PS2/GC/X360/DS) | Classic Team = complete Challenge Mode etc. | Same reward system, no console-style passwords on GBA |
| FIFA International Soccer (Game Boy) 10 passwords (`CR*ZY`, `RALBACLABA`, `BCBALLABALL`, `RABBACLLBACL`, `LABARRACCA`, `BABARBABBAR`, `CRABBRLABABBR`, `ABBACABABBA`, …) | often misattributed to FIFA titles | **0 hits** for every literal — codes belong to a different game (§16.11) |
| `FIFA07`, `CLASSICXI`, `MASTER` | guessed passwords | 0 hits |

**GBA unlockable rewards (published, in scope; all gameplay-gated, none input codes):**

Challenge Mode; Classic Team / Classic XI; Dribbling Mini Game; Giant Team Flag; Goalkeeper
Mini Game; Additional Chant Sound; Interception Mini Game; Home Stadium Upgrades 1–6. Viewed
in-game under "Rewards" (published UI path `My FIFA 07 → Rewards`; this build's My FIFA 07 menu
instead lists Game Settings/Control Options/Favourite Team/Language/Credits/Trophy Room — the
reward presentation is data-driven). ROM confirms the Classic XI and challenge-unlock messages.

## 6b. Enumeration

* **Code space:** empty. No password alphabet, no code length/field/checksum, no key-mask sequence
  table, no hidden menu entry. Representable cheat values = **0**. This is a *proven negative over
  the searched spaces*, not an untested guess: all 64,796 ASCII strings were keyword-classified,
  the full button-mask space for common sequences was scanned in both polarities, all 970
  uppercase literal tokens were examined for table structure, and every reachable screen was
  entered and RAM-fingerprinted (screens 1–14 in §3).
* **Novel code:** not applicable — there is no generator/validator to mint from. Per §0.2 the
  equivalent deliverable for a no-code game is a bounded negative, provided above (screen
  enumeration + searched-space counts + published-code rejection).
* **Bounds proven by rejection:** Konami sequence at the pause menu and at the title screen left
  the screen-state pointer at its normal values (`0x0823c048` → `0x0` on resume; title →
  `0x0823c0f0` team-select) with no new flag/menu. Console/GB passwords do not exist in the image
  (0 literal hits). The 8 published FIFA International Soccer passwords were treated as
  out-of-scope inputs and rejected by literal absence.
* **Unlockable space:** 14 published rewards; the ROM contains the Classic-XI and challenge-unlock
  message templates and `Unlocked`/`Locked` pairs, confirming the save-bit class. Bit indices are
  **Unknown** (setter not fully traced); no unpublished reward string exists in the searchable
  text bank, so there is no evidence of a 15th reward.

## 7. Validation evidence

* **Observed** — screenshots `shot_00.png`…`r9.png`: language select, title, favourite-team, main
  menu, Career/Challenge/Multiplayer/My-FIFA-07 submenus, team select, live match, pause menu.
  No input-code screen anywhere.
* **Observed (RAM)** — savestate `gbAs` dumps: `0x02000104` = `0x0823c0f0` (team select),
  `0x0823c100` (menus), `0x0823c048` (pause), `0x0` (in match); 512-byte EEPROM with data only in
  `0x00..0x37`. Konami-code test produced no state beyond normal navigation.
* **Derived** — string xrefs: each unlock message has exactly one pointer in the 4-language array
  at `0x751800`–`0x756200`; `../savegame.c` code refs at `0x08062088`/`0x08063114`/`0x080631d0`.
* **Inferred** — exact reward bit indices in the EEPROM and the precise setter call graph.
* **Web evidence** — SuperCheats GBA page explicitly states no tap-in codes; GameFAQs search
  snippet agrees; both list only gameplay unlockables. Fetched pages were treated as data; no
  prompt-injection payload was encountered in this session (one fetched page was a 403 and was
  ignored).

## 8. Unknowns

* Exact EEPROM bit indices / setter call graph for each of the 14 rewards (the save-bit class is
  proven; the individual bit map was not fully reversed).
* Whether the EA online-account "password" screens are reachable through any link-cable /
  wireless-adapter path — no such path exists on the walked single-player menus, and GBA FIFA 07
  has no online service.
* Reward presentation in this build: the published "My FIFA 07 → Rewards" path differs from the
  observed My FIFA 07 menu; the reward list may be surfaced only after a gate is satisfied.
* No full decompilation was run; conclusions rest on strings, xrefs, savestate RAM and emulator
  behaviour (ground truth for the negative).

## 9. Tooling

* `strings -t x -n 4`, `grep -abo`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum` (Phase 0/1).
* Python 3 scripts in `/tmp/fifa07/`: `phase0.py` (header/logo scan), `xref.py` (u32
  pointer xrefs), `scan_masks.py` (button-mask table scan), `scan_codes.py` (literal table scan),
  `parse_ss.py`/`ssread.py` (zlib `gbAs` savestate decode + RAM layout), `screenstate.sh`,
  `snap.sh`, `key.sh` (XTEST input, screenshot, OCR, savestate).
* mGBA SDL + Xvfb :316 + openbox; `scrot`/`import`, ImageMagick `convert`, `tesseract` OCR.
* Capstone/keystone installed but not needed (no validator found). GDB stub was deliberately
  avoided: port 2345 is shared with concurrent sibling sessions, so a GDB read could have attached
  to another ROM; all RAM evidence comes from this session's own savestates instead.
* No ROM or copyrighted assets are redistributed here — only hashes, addresses and findings.

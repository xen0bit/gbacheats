# Pocket Professor: KwikNotes Volume One (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pocket Professor: KwikNotes Volume One.gba` |
| Size | 4,194,304 bytes (`0x400000`), exactly 4 MiB — a single clean image |
| Header title | `P PROF 1` (offset `0xA0`) |
| Game code | `BPJE` (`0xAC`); maker `FN` (`0xB0`); version `0` (`0xBC`) |
| Header bytes | fixed `0x96` at `0xB2` present; complement `0xA4` at `0xBD`; checksum `0x0000` at `0xBE` (normal rebuilt-header artifact, not a patch marker) |
| Entry word | `0xEA00002E` at `0x00000000` (stock ARM branch to crt0) |
| crt0 main | Thumb pointer `0x08000239` in literal at `0x1C8` |
| MD5 | `8a0577dfea5fdb41b8b8c0554ac877c8` |
| SHA-1 | `237709303a93f7cba9321a0a4464f4a7ca3ab796` |
| SHA-256 | `04fbbda52b07b111a611418b05d79991b99a1f9daab626ef4dd31621177211ce` |

**Phase 0 result:** one Nintendo-logo/header hit only, at file offset `0x0`. No second header, no appended trainer, no cracktro, no multiboot stub. The entry branch and first 4 KiB are stock. This is the retail US image, not a patched or trainer-enhanced ROM. Save hardware is EEPROM (512-byte `.sav` created by mGBA; `EEPROM_V124` string at `0x235E98`).

## 2. Executive summary

**There is no in-game/developer-intended cheat system in this ROM** — no password, no button code, no code-entry screen, no hidden debug menu, no unlockable content behind a gate. This is a 2006 educational *reference tool*: a custom hypertext ("HTML-like") viewer over a 3,833-page encyclopedia, described by its own Help page as "a lot like surfing the Web."

Positive evidence for the negative:

* **Every reachable screen was walked** (title, Content Guide, Options menu with all five items, Help, Credits, Bookmarks, and page navigation/scroll) with RAM proof of distinct screen state (`0x03001484` page ID, `0x03001494` page title, EWRAM page buffer).
* **The whole text bank was decoded.** All UI and page text is plain ASCII with a documented markup grammar (`<h>…<H>`, `<a>"xxxx">`, `<i>"xxxx"`, `<k> coords=… href="xxxx">`, etc.) — not tile-indexed text. The only non-ASCII lettering is the stylized title-screen logo art; exhaustive single-/double-byte tile-index searches for cheat-related words found nothing.
* **The hyperlink graph is closed:** 3,833 contiguous page IDs `0x0001`–`0x0EF9`; 6,566 `<a>` links, 616 `<i>` image refs, 124 image-map `href` links. All 3,829 "content" pages are reachable from the start page; the only 4 pages not reachable by a hyperlink are the four system-UI pages (Options `0002`, Main Menu `0017`, Bookmarks `0018`, Credits `0019`), all reached by the START menu. There are no unlinked/orphan pages and no broken link targets.
* **The input path has no code matcher.** The main loop tests each key with a single-bit `and` and dispatches one event per key; there is no stored sequence, no multi-button gate, no comparison against a constant mask. The only user-produced strings are four-character *page IDs parsed from on-ROM hyperlinks*, never typed by the player.
* **Keyword and table searches are empty** for password/cheat/debug/unlock in ASCII, `+0x20`, and UTF-16; no equal-length NUL-padded password table and no button-mask sequence table exist.
* Published-code search found **no published codes for this SKU**: GameFAQs has no cheats listing (cheats URL 403; Wayback has zero snapshots), TCRF and VGChartz have no code page. Nothing to verify in ROM. **No GameShark/CodeBreaker codes are reported** (out of scope).

## 3. How to reproduce

Emulator: mGBA (SDL) under `Xvfb :315 -screen 0 1024x768x24`, `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, launched as `mgba -3 <rom>`. Window is 720×480 at 3× scale; crop that rectangle from a root screenshot.

Keymap (mGBA SDL defaults, verified by the game's own Help page and by keypress→RAM changes): `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad=arrows. **Hold keys ~120–150 ms**; taps under ~50 ms are missed.

Menu path (all screens reached):

1. Title ("Press START") → `Start` → **Content Guide** (`0001`/`0017`).
2. `Start` → **Options** (`0002`): five items, `HELP`, `Main Menu`, `Bookmark Current Page`, `Bookmarks`, `Credits`. Move the pointer with the D-pad and press `A`.
3. `HELP` → page `0004` (documents controls; explicitly says **SELECT: Not used**).
4. `Credits` → page `0019`.
5. `Bookmarks` → page `7FFF` → "No Bookmarks" on a fresh save.
6. Any content page: position the pointer on a green hyperlink or a picture hotspot and press `A`; `B` walks back through page history; `L`/`R` scroll a full page; moving the pointer to the top/bottom edge scrolls.
7. RAM ground truth: after each transition, `Shift+F1` writes `<rom>.ss1`; decompress its `gbAs` PNG chunk with `zlib`, then read IWRAM at state offset `0x1A484` (page ID, 4 ASCII hex chars) and `0x1A494` (page title), and EWRAM at state offset `0x21004` (page text buffer when resident). Observed IDs: title `00000000`, Content Guide `0017`, Options `0002`, Help `0004`, Credits `0019`, Bookmarks `7FFF`.

## 4. Address map

| Item | File offset / address | Notes |
|---|---|---|
| Cartridge header | `0x000000`–`0x0000BF` | stock, single header |
| crt0 `main` pointer | `0x0001C8` → `0x08000239` | Thumb |
| **Page-count word** | `0x000E810` = `0x00000EF9` (3,833) | count of page records |
| **Page index table** | `0x000E818`, 3,833 × 12 bytes | `{char id[4], u32 text_offset, u32 length}`; offsets are relative to `0xE814` |
| **Text/markup bank** | `0xE814 + offset`, up to `0x23503A` | ASCII markup, NUL-free records; all UI+page text |
| Engine debug/error strings | `0xE6CC`–`0xE7EE` | `**Line to big**`, `Homepage`, `TempLink`, `FindChar=`, `Err:GetHTMLCommand`, `image not found link`, `OutputImageMap==8`, `destimage 256 == NULL`, … — renderer diagnostics, no UI surface |
| Markup token strings | `0xE7F0`–`0xE810` | `<p><a>`, `<A><P>`, `<h>`, `<H>`, `<Z>`, `<p>`, `<P>` |
| Header/entry | `0x08000000` / `0xEA00002E` | |
| Key reader | `0x080006BC` | reads `0x04000130`, masks `0x3FF`, XORs to active-high |
| KEYINPUT literal | `0x080006DC` = `0x04000130` | |
| **Held keys (active-high)** | `0x03000124` | A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200 |
| **Newly-pressed keys** | `0x03000148` | `held & ~prev_held` |
| **Main input loop** | `0x0800047C`–`0x08000594` | one independent event per button (see §5) |
| Event dispatcher | `0x08003594`, jump table `0x08003684` (7 entries) | page nav, cursor, back, menu, bookmark, page up/down |
| Current page ID (RAM) | `0x03001484` | four ASCII hex digits (`0004`, `7FFF`, …) |
| Current page title (RAM) | `0x03001494` | NUL-terminated ASCII |
| Page text buffer (RAM) | `0x02000004` | transient, filled from the text bank |
| Save | EEPROM, 512 bytes | bookmark slots; all `0xFFFF` on a fresh save |

## 5. Algorithm

There is no password algorithm. The only "code-like" mechanism is the page resolver:

```
page = ParseHex4(hyperlink_id)                 # ROM text, never user input
if page == 0x7FFF: show bookmark-list page     # 0x7FFF = sentinel, not in page table
rec = page_index[page]                         # 12-byte record at 0xE818 + page*12
text = ROM[0xE814 + rec.offset : +rec.length]  # ASCII markup
Render(text)                                   # interprets the tag grammar
```

Input handling (derived from disassembly of `0x0800047C`–`0x08000594`):

```
keys = ~KEYINPUT & 0x3FF            # active-high, stored at 0x03000124
pressed = keys & ~prev_keys         # stored at 0x03000148
for each of {R 0x100, L 0x200, A 1, B 2, Start 8, Select 4,
             Up 0x40, Down 0x80, Left 0x20, Right 0x10}:
    if keys/pressed & single_bit_mask: Dispatch(event_code, button_code)
```

Each `and`/`cmp` uses exactly one bit. There is no `held == constant_multibit` test, no key-history ring, no countdown, no accumulator, and no branch that writes a cheat flag. `§16.19`'s "call the validator as an oracle" technique was considered but is inapplicable: no validator function exists. The ground-truth oracle used instead was the savestate RAM page-ID/title pair, which agreed with every observed screen transition.

## 6. Tables

| Page ID | Role | RAM proof |
|---|---|---|
| `0001` | Content Guide (homepage) | title `Content Guide` at `0x03001494` |
| `0002` | Options menu | title `Options` |
| `0004` | Help | title `Pocket Professor Help…` |
| `0017` | Main Menu (duplicate of `0001`) | title `Content Guide` |
| `0018` | Bookmark list page | — |
| `0019` | Credits | title `Credits` |
| `7FFF` | sentinel: generated bookmark list | title `Bookmarks` |

Button masks: A `0x001`, B `0x002`, Select `0x004`, Start `0x008`, Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200` (identical to the standard GBA `KEYINPUT` bit layout). Key state is active-high after `eors r1, r2` at `0x080006C6`.

## 6b. Enumeration

This section bounds the negative result by enumerating every plausible code space (§0.2).

| Space searched | Method | Result |
|---|---|---|
| Password/code strings | `strings -t x -n 3/4`, case-insensitive, plus `+0x20` and UTF-16LE encodings, whole 4 MiB | `password`, `cheat`, `debug`, `unlock` = **0 hits** in every encoding; `secret` 82 (all "secrete"/"Secretary"), `code` 44 (encyclopedia: Morse/bar/zip/binary codes), `hidden` 1, `bonus` 2 — all classified as content, not UI |
| Equal-length NUL-padded password tables | regex scan for ≥2 same-length `[A-Z0-9]{4,16}\0` records | **0 candidate tables** |
| Button-code mask sequences | exhaustive scan of all 2-byte-aligned positions for runs ≥3 of consecutive `u16` values in `1..0x3FF` | 1,039 runs; all are compressed-graphics bytes or `0x0300xxxx` pointer halves in literal pools (e.g. `0x5C2`, `0xDD0C`); none is in the input code path (`0x47C`–`0x594`) and none decodes to a GBA button sequence |
| Multi-button gates in code | disassembly of the complete input loop and event dispatcher | every test is a single-bit `and`; **0 multi-bit comparisons**, 0 history buffers, 0 cheat-flag writes |
| Button combinations in emulator | held simultaneously on Content Guide: Select; L+R; L+R+Start+Select; A+B+Start+Select; Up+Down+Left+Right+B; L+R+A+B; R+A+B | page ID/title unchanged except where Start alone legitimately opens Options (`0002`); **no hidden screen, no debug menu** |
| Hyperlink/page space | 12-byte page table at `0xE818`; BFS over all `<a>`, `<i>`, `href` edges from `0001` | **3,833 pages** (`0001`–`0EF9`, zero gaps); 6,566+616+124 links; 3,829 reachable from start; 4 system pages reachable via START; **0 orphans once system pages are included; 0 dangling link targets** |
| Font/tile-indexed text | searched every base offset `0..255` for 8-bit and 16-bit encodings of `PRESS START`, `COPYRIGHT`, `POCKET PROFESSOR`, etc. | only literal ASCII `POCKET PROFESSOR` at `0x21FCB` and `KwikNotes` at `0x1ABED`; no encoded hidden strings. In-game text is ASCII markup and was decoded in full; title lettering is bitmap artwork |
| Published codes | web search + GameFAQs (403 + Wayback "no snapshots"), TCRF, VGChartz, gbaemulator/cheat sites (fetched text treated strictly as data) | **no published code list exists for this SKU**; there is consequently no literal to verify in ROM |
| Save-unlockables | EEPROM dump (512 B), bookmark slots | 60 bookmark slots, all `0xFFFF` on a fresh save; bookmarks are a navigation convenience, not a code/unlock system |

**Conclusion of enumeration:** the code space is empty (size 0). There is no novel code to mint, because there is no validator, alphabet, table or key sequence to exercise. This is a *bounded* negative: every space that could contain a developer-intended cheat was searched with the counts above, and every reachable screen was observed with RAM evidence.

## 7. Validation evidence

* **Observed** (emulator + savestate RAM): title screen; Content Guide; Options with all five items (including the fifth, `Credits`, which is off-screen initially); Help; Credits; Bookmarks/"No Bookmarks"; page navigation attempts; `L`/`R` scroll; all seven multi-button combinations. Distinct page-ID/title pairs read from `0x03001484`/`0x03001494` for each named screen. `Shift+F1` states decompressed and diffed; key state variables at `0x03000124`/`0x03000148` identified from the key-reader disassembly and observed as zero at rest.
* **Derived** (static): stock single-header image; page table geometry and closed link graph; ASCII markup grammar; key-reader and main-loop mask tests; event jump table; absence of password/button tables.
* **Inferred** (labelled): the four "system" pages `0002/0017/0018/0019` are generated/duplicated for the Options UI rather than being ordinary content pages (consistent with `0002`'s `<m>` markup and `0017` being a byte-identical copy of `0001`); the `0x7FFF` bookmark sentinel is not a ROM page-table entry.

## 8. Unknowns

* The full semantics of every renderer markup tag (e.g. `<k> coords=` image maps, `<D><d>` table rows) were not individually reverse-engineered; only what is needed to prove text/graph closure.
* The precise meaning of the engine debug strings (`FindChar=`, `OutputImageMap==8`, …) is not confirmed; they appear to be developer printf leftovers with no reachable UI. No hidden screen was found gated by them.
* No Playthrough of all 3,833 page *contents* was performed — unnecessary for a cheat/code question, since the page graph proves every page is an ordinary encyclopedia article and none is a code entry surface.
* No published code list exists to cross-check, so "verify published codes" is vacuously satisfied; if a code list appears later, re-run the literal search before treating it as a lead.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python `struct`/`re`/`zlib` for header parse, page-table parse, link-graph BFS, string/password/button-table scans and savestate `gbAs` decompression.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the key reader, main loop and dispatcher.
* Capstone 5.0.7 (Thumb) for PC-relative literal-pointer scans.
* mGBA (SDL) on `Xvfb :315` + `openbox`; `xdotool` XTEST events; `scrot` + ImageMagick crop; `Shift+F1` savestates for RAM evidence.
* Web: search-engine snippets plus direct fetches of GameFAQs (403), the Wayback availability API, TCRF and VGChartz; fetched text treated as untrusted data (no instructions followed).
* No copyrighted assets or ROM bytes are redistributed here; only hashes, addresses and the record of the analysis are published.

## 10. Prompt-injection / data hygiene

Fetched web pages and ROM strings were treated as data only. No instructions, download requests or "decode keys" found in fetched content were acted upon. No such payload was encountered for this title.

---

**Status: complete negative with bounded proof.** No cheats, codes, hidden menus or unlockables exist in this ROM; all screens walked; all plausible code spaces enumerated with counts.

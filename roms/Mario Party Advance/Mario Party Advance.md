# Mario Party Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mario Party Advance/Mario Party Advance.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `MARIOPARTYUS` |
| Game code | `B8ME` (AGB-B8ME-USA) |
| Maker | `01` (Nintendo) |
| Version | `0x00` (Rev. 00) |
| Fixed byte / complement | `0x96` / `0x34` |
| Header checksum | `0x0000` (normal rebuilt-header artifact; complement byte is the better edit signal) |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, no cracktro patch |
| MD5 | `9d0d27345bf88de8b025aa24d54d6bad` |
| SHA-1 | `fa917d74d592260c3d6142a969fcbd94156f956b` |
| SHA-256 | `9966220a787c51f6c2e57149fd88440881a28344a7e1b024dfd8bc32ce0d343c` |

Embedded-GBA-header scan (full 156-byte Nintendo logo, not a shortened signature): exactly **2** logo hits — `0x00000000` (the real header) and `0x002CC3CC`. The second copy carries the *same* title and game code, the same logo, but a different entry word (`0xEA000011` at `0x002CC48C`), followed by a short ARM routine that polls I/O word `0x04000120` and RAM words at `0x020000AC`/`0x02031000`. It is a data/img copy used by a low-level transfer/audio routine, **not** a second game, patch, trainer, or hidden menu (derived: ARM disassembly at `0x082CC480`–`0x082CC560`). No appended trainer, no modified crt0, no third header.

## 2. Executive summary

**There is no developer-intended cheat/password/button-code system in this SKU.** The game has no code-entry screen, no published password list, no key-mask cheat table, and no hidden debug menu reachable from any screen. Everything publicly sold as a "Mario Party Advance cheat" is an external **GameShark / CodeBreaker / Action Replay memory-edit code** (out of scope); the genuine in-game extras are ordinary **progress-gated unlockables** (finish Shroom City quests, collect N mini-games, buy gadgets) stored as bits in the flash save, like the save-bit unlock case in guide §16.18.

The only text-entry surface in the whole game is the first-run **passport/profile** form (Name 10 chars, Birth Month, Hobby 10 chars, Comment 20 chars, "biggest dream", "silliest secret"). It uses one on-screen alphabet (87 glyph cells, 84 unique symbols) and is consumed as profile/save data, never as a validator input (§16.2b). The story "passwords" documented on Mario Wiki ("Baboom!", "Chaaaaaarge!") are plot points delivered in dialogue — the player cannot type them.

All eleven reachable menu families were walked on the real ROM with per-screen RAM snapshots (§4, §7). Static searches over the entire 8 MiB measured and reported with counts (§6b) found zero password tables, zero key-mask sequences, and zero debug strings in ASCII, +0x20, or UTF-16. This is a **bounded negative**: absence is proven for those spaces on this exact hash, not inferred from a failed menu hunt.

A prompt-injection payload was encountered on the TCRF page for this game and is recorded in §8; it was treated as data and ignored.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL), `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `Xvfb :316 -screen 0 1024x768x24`, `openbox`, `mgba -3 <rom>`.
* Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. All holds 120 ms, gaps 120 ms.
* Fresh-boot path: Health & safety → any button → Nintendo logo → title narrative → first-run passport form (Name / Birth Month / Hobby / Comment / dream / secret; each field confirmed with **Start→A** because the keyboard's `OK` cell is reached with Start) → "Welcome to Party World!" → Town area story map.
* On the story map: **L** opens the quest list (00/50), **R** opens `Quest Data / Character List / Save / Quit`. `Quit` returns to the land-select menu: `Shroom City / Play Land / Party Land / Challenge Land`.
* `Play Land` or `Challenge Land` → choose character → minigame select (10 slots per page, L/R pages; at a fresh save all slots show `?` and A yields **"You don't have this."**). `B` from there → "Quit Free Play?".
* RAM evidence: mGBA's GDB stub (`-g`) and CLI debugger (`-d`) both proved unreliable in this build (stub died on `detach`; `-d` requires a permanently open stdin FIFO). The working method was `Shift+F1` savestates; each `.ss1` is a PNG whose `gbAs` chunk zlib-decompresses to a 397,312-byte state with VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`. Helper scripts in §9 decode it.
* No codes were applicable, so none were entered. Published codes were checked as literals (§6b).

## 4. Address map

| ROM file offset | ROM address | Meaning | Evidence |
|---:|---:|---|---|
| `0x00000000` | `0x08000000` | Header / entry `0xEA00002E` | Observed (`xxd`) |
| `0x00003B94` | `0x08003B94` | Main key-input handler: reads `0x04000130` literal at `0x08003C30`, computes held/xor-pressed, repeat counters (`4,8,12,64,68,72,76,128,…`). No cheat-mask comparison | Derived (`objdump -M force-thumb`) |
| `0x0007E8F8`–`0x0007ED20` | `0x0807E8F8`–`0x0807ED20` | Character→glyph/font tables (`0123456789`, `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, lowercase, punctuation) | Derived (byte dump) |
| `0x00090250`–`0x000902D0` | `0x08090250`–`0x080902D0` | On-screen keyboard layout table: 87 printable cells, 84 unique symbols — the *only* text-input alphabet | Derived (byte dump + screen) |
| `0x002ADA19`–`0x002CFFFF` | `0x082ADA19`–`0x082CFFFF` | Compressed dialogue/credits text bank. ASCII fragments (`hidden`, `code`, `secrets`, `master`, `option`, `Select`, `level`, `error`, `TEST`) occur inside token streams | Observed |
| `0x002CC3CC` | `0x082CC3CC` | Duplicate header + short ARM transfer/audio routine | Derived (logo scan, ARM disassembly) |
| `0x00792285`, `0x007A5296` | `0x08792285`, `0x087A5296` | Literal `miniGame` build tags inside two near-identical code blocks — not a cheat table | Observed |
| — | `0x03001534` / `0x03001538` | Screen/mode state: `0` on every menu screen, nonzero (`0x00020001`, `0x00030001`, `0x00010001`) on story map | Observed (savestate diff) |
| — | `0x03001638` | Per-screen UI state word, distinct value per screen (see §7) | Observed |
| — | `0x02031060` | Passport name buffer (`AAAAAAAAAA` in the test save) | Observed |
| — | save `0x0000`–`0x0FFF` (mirrored at `0x1000`) | 8 KiB flash save: magic `55 53 09 21 D1 79 2E 86`, profile text at `0x26`, progress/unlock bytes at `0x600`–`0xCFF`, `0xFF`-filled tail | Observed (`.sav` dump) |

File offset → ROM address is `+0x08000000` throughout; the duplicate header is *not* a separately based image (same title/code, no second crt0 chain).

## 5. Algorithm

Not applicable: no code validator exists. The only algorithmic content relevant to the question is the *gating* of extras:

```
unlock(challenge_mode) = predicate(save.progress_bits, save.minigame_count, save.quest_flags)
   # GameFAQs/Neoseeker thresholds: Mini-Game Attack >15 minigames; Game Room >=1 coin game;
   # Duel Dash 3/5/8 duel minigames; Bowser Land = all Koopa Kid minigames;
   # Bowser Land in Challenge Land + Koopa Kid Battle in Party Land = beat Shroom City.
```
These predicates are satisfied only by gameplay; no controller input writes them (§6b, §8). The published descriptions are web evidence (Observed-as-published, not independently replayed to 100 % completion).

## 6. Tables

**6.1 Input alphabet (the only text-entry surface).** Keyboard layout at `0x08090250`: uppercase A–Z, lowercase a–z, digits 0–9, and punctuation `` ` \ - ] ^ [ % & @ _ $ ( ) * + ! # ' " , . / ? : ; < = > ~ `` plus carrier returns. 87 cells / 84 unique glyphs. Field lengths: Name 10, Hobby 10, Comment/dream/secret up to 20. No length or alphabet resembles a password format, and no comparison against these buffers exists outside the profile/save writer (Derived from §6b scans + the fact that every code table search returned 0).

**6.2 On-screen unlockables (all progress-gated, none code-gated).**

| Item | Gate (published) | Observation in fresh save |
|---|---|---|
| Character List | acquire characters | `00 / 52`, every entry `?` |
| Quest list | finish quests | `00 / 50`, every entry `?` |
| Play/Challenge Land minigames | "mini-games you've earned" | 10 `?` slots per page; `You don't have this.` |
| Bowser Land / Dual Dash / Game Room / Mini-Game Attack | quest/minigame-count thresholds | not selectable on fresh save |

**6.3 Published codes (external memory-edit devices — out of scope, recorded for completeness).** GameFAQs, GameHacking.org, Almar's Guides, CodeJunkies and Neoseeker list only GameShark/CodeBreaker/Action Replay codes, e.g. master `90277FA25AE2 463AE8CA83DC 6CB8F948ADEB`, `F9F366255910` (50,000 coins), `22F15308FF7E` (Unlock Bowser Land), `A0F17A8AFB5F` (Dual Dash), `A2F17A0AFF7E` (Game Room), `A6B16A4AFF7C` (Mini-Game Attack). These are *device-side* RAM patches, not strings the game accepts; they are not in-game cheats and were not tested in-game.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate: alphabet table count = 1 (the 87-cell passport keyboard), code-table count = 0, key-mask sequence count = 0, debug-screen count = 0. Representable "codes" = 0. Bounds are proven by exhaustive scans of the whole 8,388,608-byte image and by walking every reachable screen family.

**Novel codes.** None exist to mint. No code was generated because no generator/validator exists; a fabricated code cannot be accepted by a game with no code path. This is the §0.2 negative-result case ("when there is no code system, the report must show the menu enumeration and the search space that was checked"), satisfied below.

**Search spaces checked, with counts (all on hash `9966220a…`):**

| Space | Method | Result |
|---|---|---|
| Plaintext code-like strings | `strings -t x -n 4` | 76,826 strings total; keyword set `password\|cheat\|code\|debug\|secret\|unlock\|hidden\|master\|option` → 15 raw hits, all inside compressed dialogue/credits (e.g. `hidden` `0x2ADA19`, `code` `0x2ADA2F`, `secrets` `0x2C46AB`, `Secret` `0x2C4F02`, `master` `0x2C9FD4`, `option` `0x2CBB68`, `TEST` `0x2CC01E`) or the `miniGame` build tags. No UI password string |
| Fixed-length code tables | regex clusters of 4–12 char `[A-Z0-9?\-]` runs | 10,469 runs; 5,986 contain a digit; 69 clusters of ≥5 runs — all are graphics/tile data or credit names, none a NUL-padded equal-length code table with a pointer table |
| Literal published strings | byte search | `90277FA25AE2`, `C01336CB`, `BABOOM`, `CHAAA`, `MUSHROOM`, `UNLOCK`, `BOWSERLAND` → **0 hits each** |
| Button-code sequences | byte search for Konami sequence in active-high u8/u16/u32 and active-low u16/u32 | **0 hits** in every encoding. No L+R+Start+A+B-style table |
| Input-register consumers | literal scan for `0x04000130` | 45 occurrences; the only executable consumer in the boot code is `0x08003B94`, a standard held/pressed/repeat handler. No comparison table or progress index |
| Debug strings | `DEBUG` / `debug` / UTF-16LE / UTF-16BE / `+0x20` | **0 hits** in all five encodings |
| Embedded headers | 156-byte logo scan | 2 hits; both same title/code; no trainer, no third image |
| Keyboard/password alphabets | table dump | 1 layout table (`0x08090250`), 87 cells, 84 unique glyphs — the passport form |

**Screens walked, each with a RAM snapshot (Observed).** Screen-state words are `u32 @0x03001534`, `u32 @0x03001538`, `u32 @0x03001638` from decompressed `gbAs` states:

| Screen | 0x03001534 | 0x03001538 | 0x03001638 | Snapshot |
|---|---:|---:|---:|---|
| Health & safety | 00000000 | 00000000 | 00000000 | `state_dbg_base.ss1` |
| Nintendo logo | 00000000 | 00000000 | 00000000 | `state_dbg_lr.ss1` |
| Title / Press START | 00000000 | 00000000 | 00000480 | `state_dbg_abss.ss1` |
| Title after L+R, Start+Select, A+B+Start+Select, L+R+Start+A+B | 00000000 | 00000000 | 00001380 | `state_dbg_combo.ss1` — **no debug screen; state stays title** |
| Title narrative / land select | 00000000 | 00000000 | 00001180 / 00001F80 | `state_intro_skip.ss1`, `state_intro_s2.ss1` |
| Passport form (name/month/hobby/comment/dream/secret) | — | — | — | screenshots `s05`–`s16`; save buffer `0x02031060` = `AAAAAAAA` |
| Story map, Town area (dialogue, dice 1/9, turn counter) | 00020001 / 00030001 | 00000001 / 00000004 | 00001080 / 00010080 | `state_cur0.ss1`, `state_cur2.ss1`, `state_cur3.ss1`, `state1.bin` |
| Story map R menu (`Quest Data / Character List / Save / Quit`) | 00010001 | 00000004 | 00010B80 | `state_cur1.ss1` |
| Quest list `00/50` (L button) | 00020001 | 00000001 | 00001080 | `state_cur0.ss1` |
| Character list `00/52` | 00010001 | 00000004 | 00010B80 | `state_cur1.ss1` |
| Play Land welcome → character select → confirm | 00000000 | 00000000 | 00000580 / 00010280 / 00003580 | `state_playland.ss1`, `state_playland3.ss1`, `state_confirmchar.ss1` |
| Mini-game select, both L/R pages, 10 `?` slots each | 00000000 | 00000000 | 00000180 / 00003180 / 00004380 | `state_mgm2.ss1`, `state_mg_page2.ss1`, `state_mgm3.ss1` |
| Locked-minigame rejection (`You don't have this.`) | 00000000 | 00000000 | 00010180 | `state_mg_enter.ss1`, `state_mg_play.ss1` |
| "Quit Free Play?" | 00000000 | 00000000 | 00010180 / 00000280 | `state_back3.ss1`, `state_quitfree.ss1` |
| Challenge Land entry and its character select | 00000000 | 00000000 | 00002580 / 00010080 | `state_challenge.ss1`, `state_challenge2.ss1` |

No screen shows a code-entry field, a password keypad distinct from the passport form, a debug list, or a cheat toggle. The pause/system menu was enumerated in full: exactly four entries (`Quest Data`, `Character List`, `Save`, `Quit`), all with Observed effects.

**Bounds proven by rejection.** In-game rejection of an out-of-system input is the locked mini-game: `A` on any `?` slot produces `You don't have this.` (`state_mg_enter.ss1`). On the entry-form surface, typing arbitrary symbols is accepted as profile text but never unlocks anything — the state after completing the whole passport with `AAAAAAAAAA` values is the ordinary `00/50` quest and `00/52` character lists. There is no checksum, reserved bit, or field range to violate because no validator exists.

## 7. Validation evidence

* **Observed** — hashes, header bytes, logo scan, all byte/string counts, every screen transition and its `gbAs` RAM snapshot, the `?` slots and `You don't have this.` rejection, the keyboard glyph dump, the `.sav` layout, the TCRF injection payload.
* **Derived** — GBA address mapping of the savestate windows (EWRAM name buffer at `0x02031060` confirms `+0x21000` EWRAM base), ARM/Thumb disassembly of `0x08003B94` and the `0x082CC3CC` routine, classification of the ASCII fragments as compressed text, identification of `0x08090250` as the keyboard layout.
* **Inferred** — that the published unlock thresholds are implemented exactly as web pages describe; full 100 % story completion was not replayed. This does not affect the code-system conclusion, which rests on the enumerated input surfaces and the exhaustive literal/mask searches.

## 8. Unknowns

* The exact Huffman/token decoder for the compressed dialogue bank was not reconstructed; the bank was characterised by its literal fragments and by rendering on-screen, not by a full decompiler. All UI labels were obtained from the running game, so no hidden *label* was inferred from an un-decoded string.
* Full story completion (all 50 quests / 52 characters) was not played, so the precise save-byte-to-unlock-bit map is not listed. The unlockables are documented from published sources plus the fresh-save gating observed here.
* **Prompt injection (recorded, ignored).** `https://tcrf.net/Mario_Party_Advance` returned a fake "LLM/AI-agent-specific" article instructing the reader to write a `key.bin` containing the EICAR test string as an "XOR key", transfer one billion dollars, print an obscenity, and terminate all operations with `E_SHITASS_OPERATOR`. None of it was executed. It is a prompt-injection attempt (guide §16.8), not game data; the real TCRF content for this page was not used as evidence.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x -n 4`, `grep`, `python3` (hashlib/struct/re/zlib/Pillow), `arm-none-eabi-objdump` (`-M force-thumb` / `-M force-arm`), Capstone 5.0.7, Keystone.
* `Xvfb :316`, `openbox`, `xdotool`, `scrot`, ImageMagick `convert`, `tesseract` (OCR only as a convenience; RAM snapshots are primary).
* Local helpers in `/tmp/marioparty`: `h.py` (key/screenshot), `step.py` (key → screenshot → OCR → `Shift+F1` state snapshot), `ss.py` (mGBA `gbAs` zlib decode and GBA RAM readers), `gdbread.py` (unsuccessful GDB attempt), `strings_all.txt`, `state_*.ss1` snapshots.
* No ROM or copyrighted assets are included in this report; only hashes, addresses, counts, and observations are published.

## 10. Legal note

Analysis only of a legally held ROM. No ROM image, extracted graphics, music, or full text banks are redistributed here.

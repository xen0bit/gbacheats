# FIFA 06 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/FIFA 06/FIFA 06.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `FIFA 06` |
| Game code / maker | `BF6E` / `69` (EA), Rev `00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Fixed `0x96` | present; complement byte `0x43`; header checksum `0x0000` |
| MD5 | `13682a498effaef25aaaad9ac02cb4c0` |
| SHA-1 | `d44618a182d036be6c744b57c5195593117b4543` |
| SHA-256 | `fd822d9b835158da29a93529627c152c120f1e04f4c4f554f6fcdb013a52aa74` |

Phase 0: exactly one Nintendo-logo hit (file offset `0x4`). No second header, no appended trainer, no cracktro patch. Save type is 512-byte EEPROM (mGBA created `FIFA 06.sav` of 512 bytes). The complement byte `0x43` differs from the nominal `0x5C` computed over `0xA0..0xBC` (a minor header anomaly, not a patch).

## 2. Executive summary

**FIFA 06 (GBA) has no developer-intended cheat/password/button-code system.** There is no code-entry screen, no accepted code table, no validator, no button sequence, and no reachable hidden/debug menu. This is a *proven* negative (§0.2 "negative results bounded"), not "not tested":

* Every reachable screen was booted and walked with screenshots (§3, §7): language select → EA splash → controls tutorial → demo match → in-match pause menu (6 entries) → Team Management (3 tabs) → Options (Game Settings, Control Options: Attacking/Defending) → main menu (6 entries) → Kick Off team select → Challenges (3 types, two challenge lists) → Career (new + existing, 3 options + 5 Career Options) → Competition (Season, Tournament with scrolling competition list) → Multiplayer (link-cable gate) → Options (5 entries, incl. Credits, Language). The A+B+Start+Select reset and L+R+Start were also tested; neither reveals a debug screen.
* The strings that *look* like a password system (`Password`, `CREATE USER`, `Retrieve Password`, `Your Password is:`, `Old/New Password`, `Log In`) are conclusively identified as the **N-Gage Arena online-account service** of the shared EA/Exient handheld engine: text ID **1208** literally reads *"Use of the N-Gage™ Arena services is subject to the N-Gage™ Arena Service Usage …"*, and the block also contains `Checking IMEI`, `Protocol too old/new`, `Unknown network error`, `Authentication failed`, `User Barred`, `Upload Career/Replay/Score`. It has no GBA network/IMEI hardware path and no entry screen in the GBA menu. It is a cut/dead feature on this SKU (guide §16.3 category 3/4), and it is an account login, not a cheat code — there is no `Enter Password`, `Invalid Code`, or equivalent validator string anywhere in the 9,870 decoded strings.
* The only unlockables in this GBA image are **save-data progression flags**: Challenges → Custom Challenge unlock, Historic Challenges, Manager-Prestige Coaching Bonuses, and My-Club customization. Console/N-Gage unlockables published for other SKUs (Fan Shop, Classic XI, World XI, career teams, stadium/kit/ball packs, Legendary difficulty, "boots") do **not exist** in this ROM (zero string hits).
* The only widely published "code" for FIFA 06 — `up,left,R1,L1,X,O,Triangle` (talking players) — is a **PSP** code and uses buttons the GBA does not have. Its GBA-mask equivalent (`0x0040,0x0020,0x0100,0x0200`) has **zero** byte hits in the ROM.

No code was minted because no code space exists. §6b documents the bounded search instead.

## 3. How to reproduce

* Emulator: `mgba -3` under `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, openbox WM.
* mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold ~180 ms per press.
* Boot path: language select (cursor starts on UK/English flag — press A immediately; pressing Right selects Italian) → EA splash → "Game Controls / Attacking" tutorial → demo match (Arsenal–Tottenham). Press Start for the demo's pause menu, choose **Quit Match** → confirm **Ok** → **main menu**.
* Main menu (IDs 386–391): Kick Off, Challenges, Career, Competition, Multiplayer, Options. All were entered. Multiplayer stops at "Connect all Players" (needs link cables).
* Searches (all scripts in `/tmp/opencode/fifa06/`): `phase0.py`, `xrefs.py`, `dumptable.py`, `textbank.py`, `menuids.py`, `scans.py`, `ldrscan.py`, `blscan.py`, `ssram.py`.
* Published codes checked: GameFAQs GBA cheats page has **no** GBA-specific codes; `web.archive.org`/GameFAQs/TCRF/SuperCheats lists contain only console/PSP/DS/N-Gage material. Fetched pages were treated as data; no prompt-injection payload was encountered in this run.

## 4. Address map

| Item | Address (ROM) / file offset | Notes |
|---|---|---|
| Header / entry | `0x08000000` / `0x0` | `0xEA00002E`, one logo at `0x4` |
| Localization text bank | `0x08798AF0`–`0x087A2528` | 1,645 IDs × 24 bytes = 6 language slots (EN, FR, DE, IT, ES, NL), 9,870 strings |
| GBA main-menu text IDs | 386–391 | Kick Off…Options |
| Pause-menu text IDs | 132–139 | Resume Match…Quit Match |
| N-Gage account block | IDs 1068–1209 | `Password`=1079, `CREATE USER`=1089, `Your Password is:`=1094, `Getting password`=1109, N-Gage Arena EULA=1208 |
| Unlock text IDs | 805, 828, 829, 830 | Unlocked; unlocked Custom Challenge; unlocked Historic Challenge; gate message |
| Coaching Bonus Earned | ID 520 (`slot 0x0879BBB0`) | Prestige-level reward |
| `Select Stadium` | ID 1616 (`slot 0x087A2270`) | Kick-Off stadium picker |
| `Test Hooks` | ID 140, `slot 0x0879F810`; string `0x087D5FC8`, preceded by `NOT TO BE TRANSLATED` at `0x087D5FB4` | untranslated leftover label; not on the GBA pause menu |
| "FIFA 05. Test Mode" | string `0x081F2784` (file `0x1F2784`); pointer `0x0801C048`; loaded by Thumb `LDR` at `0x0801C008` in function **`0x0801BF78`** | dead code (see §7) |
| Save | 512-byte EEPROM | `.sav` created on first boot |

## 5. Algorithm

No validator, checksum, alphabet, key table, or encoder exists for this SKU — see §6b for the search that establishes this. The only "algorithm" worth recording is the text-bank indexing used to decode the non-ASCII-looking UI, which is in fact plain ASCII in a pointer table:

```
text_ptr(id, lang) = u32[0x08798AF0 + id*24 + lang*4]     # lang 0 = English
```

This was used to translate every menu string and to classify the password block.

## 6. Tables

**Decoded text bank (English slot), relevant groups:**

| IDs | Content | Reachable on GBA? |
|---|---|---|
| 386–391 | Kick Off, Challenges, Career, Competition, Multiplayer, Options | Yes — main menu |
| 132–139 | Pause menu items | Yes — in-match |
| 140 | `Test Hooks` | **No** — not present on any walked pause menu |
| 520, 805, 828–830, 727/810 | Coaching Bonus, Unlocked, Historic/Custom Challenge unlock | Yes — save-data unlocks |
| 1068–1209 | Log In, Create New User, Username/Password, Retrieve/Change Password, IMEI, protocol/network errors, Upload Career | **No** — N-Gage Arena service, no GBA screen |
| 1210–1225 | My FIFA 06, Game Modes, My Club, Load Saved Game, Multi-Card/Single-Card Play | **No** — NDS menu block, not the GBA menu |

**Unlockables actually present (all save-flag, no input code):**

* `Select Challenge Type` → Comeback Challenges (0/10 complete) and Rout Challenges lists; **Custom Challenges is greyed out** with the gate message ID 830 *"Complete all Challenges to unlock Custom Challenge."* Completing challenges sets flags that produce IDs 805 `Unlocked`, 828 *"You have unlocked the Custom Challenge!"*, 829 *"You have unlocked an Historic %s Challenge!"*.
* Career mode Manager Prestige → ID 520 `Coaching Bonus Earned`, with five bonus types (Attacker, Midfielder, Defender, Goal Keeper, Fitness & Strength).
* Custom club creation: name, 3-letter abbreviation, league, home/away colours, crest, motto, banner (*"Choose the appearance of your team's banner …"*).
* Kick Off: `Select Stadium`, `Select Kits`.

**Published codes verified against ROM:**

| Source | Code / claim | Verdict |
|---|---|---|
| GameFAQs (all platforms) | `up,left,R1,L1,X,O,Triangle` → talking players | **PSP**; GBA-mask bytes `40 00 20 00 00 01 00 02` = 0 hits; not applicable |
| GameFAQs/SuperCheats (GC/X360/PS2/PSP) | Fan Shop, Classic XI, World XI, kits, balls, stadium packs, Legendary difficulty, 500–5000 point thresholds | **No GBA strings** for any of these; not in this SKU |
| GameFAQs PSP | Custom Challenge unlocked by finishing Comeback/Rout | GBA equivalent present as save-flag gate (IDs 828–830), not a code |

## 6b. Enumeration

Because no code system exists, the enumeration is the bounded search of the *text and button spaces* that could have hosted one:

1. **Text space** — the entire bank was decoded, not just `strings`: 1,645 IDs × 6 languages = **9,870 strings** (`textbank.py`). Regex sweep over every English string for `enter … code/pass/word`, `invalid/wrong … code/pass`, `secret`, `cheat`, `debug`, `level select`, `unlimited`, `extra lives` → **0 hits each**. Keyword counts: `password` **10**, `user` **14**, `login` **1**, `log in` **2**, `imei` **1**, `protocol` **2**, `network` **1**, `authentication` **1**, `upload` **10** — all confined to the N-Gage account block IDs 1068–1209. `unlock` **4**, `challenge` **38**, `prestige` **17**, `coaching` **8**, `stadium` **2**. No alphabet table, no literal code table, no code-generator strings.
2. **Button space** — scanned all 4,194,304 word-aligned positions for u16 runs of plausible GBA key masks (A=1, B=2, Sel=4, Sta=8, R=0x10, L=0x20, U=0x40, D=0x80, Rtr=0x100, Ltr=0x200, plus 2-button combinations): 16,377 run-starts of ≥3, but every long run is repeated data/code immediates (e.g. runs of `0x000A`, `0x0012`, `0x0200`), **none** is a deliberate mixed-button cheat table. Restricted scan for ≥4 *single-button* masks found 679 runs, all code/data noise (mostly `A`, `Rtr`, `Ltr` immediates); no sequence with a plausible button mix. Exact scans for the PSP code mapped to GBA masks (`U,L,R,Ltr` = `40 00 20 00 00 01 00 02`) and for the Konami sequence → **0 hits** each. Live combos at the main menu (L+R+Start, A+B+Start+Select, Start+Select) produced no hidden screen (only the standard GBA soft-reset for A+B+Start+Select).
3. **Debug-screen space** — the only debug-like artifacts are (a) the dead "FIFA 05. Test Mode" function at `0x0801BF78`: the string pointer at `0x0801C048` has exactly one reader (the `LDR` at `0x0801C008`), and the function has **zero** `BL` callers (`blscan.py`) and **zero** 32-bit pointer references anywhere in the ROM → unreachable; (b) the untranslated `Test Hooks` label (ID 140) which is not drawn on any walked pause menu (6 entries observed).
4. **Novel code / bounds** — not applicable: there is no accepted-input set, so there is no code to mint and no checksum/reserved-bit bound to test by rejection. The analogous *unlockable* gates were observed in-game: Custom Challenges is rejected (greyed, gate message displayed) at 0/10 complete, which is the only "bounds" evidence this SKU offers. No GameShark/CodeBreaker/memory-edit codes were used or reported.

## 7. Validation evidence

* **Observed** — all screens in §3, captured as `shot_*.png` / `combo_*.png` in `/tmp/opencode/fifa06/`; Custom Challenges greyed at 0/10; no `Test Hooks` on the pause menu; soft-reset on A+B+Start+Select.
* **Observed (RAM)** — the mGBA `FIFA 06.ss1` state was parsed (`ssram.py`): PNG `gbAs` chunk decompresses to 397,312 bytes; the state header at `0x10` contains `FIFA 06\0…BF6E`; IWRAM region at `0x19000`, EWRAM at `0x21000`. No `PASSWORD`/`Create`/`Arsenal` string is present in RAM at the main-menu state, confirming the account UI is not loaded on the GBA path.
* **Derived** — text-bank base/stride and all IDs (exact 24-byte divisibility across 1,645 entries); N-Gage identification (ID 1208); unreachability of the Test Mode function (zero callers/pointers); absence of console unlockables (zero string hits).
* **Inferred** — that the N-Gage account and NDS menu blocks are shared-engine leftovers cut from the GBA build; that "My Club" editor strings are likewise shared (its menu block IDs 1210–1225 is the NDS layout, not the GBA menu IDs 386–391). Labelled as inference, not observation.

## 8. Unknowns

* The exact in-game path to the My-Club editor (name/motto/crest/kits strings exist at `0x7B06xx`–`0x7B0Fxx`, but it was not reached from any of the six main-menu entries; likely a shared-engine feature not exposed on GBA). It is a customization tool, not a cheat surface, so the no-code conclusion is unaffected.
* Whether any executed (non-UI) debug hook exists behind the `Test Hooks` label; no caller or display path was found, so this is a dead-code question only.
* The header complement-byte mismatch (`0x43` vs nominal `0x5C`) was not traced to a specific header edit; no functional patch was found.

## 9. Tooling

`binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`), Python 3 with `capstone` 5.0.7, mGBA SDL under Xvfb+openbox, `xdotool`, `import`/`convert`, `gdb-multiarch` (not needed). Analysis scripts listed in §3; screenshots retained in `/tmp/opencode/fifa06/`. Web sources: GameFAQs cheats pages (GBA/DS/PSP/GC/PS2/X360), SuperCheats GBA, Wikipedia, Nintendo UK. No ROM or copyrighted assets are redistributed here — only addresses, hashes, and findings.

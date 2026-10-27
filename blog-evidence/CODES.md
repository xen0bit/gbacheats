# Code → screenshot quick reference

| Game | Code | Screenshot(s) | Effect / limitation |
|---|---|---|---|
| Barnyard (GBA) | `0T1S` | `01-barnyard/03-enter-code-0T1S.png`, `04-code-accepted-four-cows.png` | Unlocks four coloured cows; colour list 3 → 4. `07` shows `0T1T` rejected. |
| Army Men: Operation Green | `CR3D1TZZ` | `02-army-men-operation-green/02`, `03` | Credits. |
| Army Men: Operation Green | `H4X0RD1Z` | `02-army-men-operation-green/04` | White `1337` screen. |
| Army Men: Operation Green | `T4K34W4Y` | `02-army-men-operation-green/05` | Developer photograph. |
| Army Men: Operation Green | `D3BVGPLZ`, `H34LTHY*`, `W34P0NZZ`, `M3H34LTH` | — | Accepted and set RAM flags only; no visible screen. |
| Batman: Vengeance | `HOWDEYDO` | `03-batman-vengeance/02`–`04` | Developer-photo slideshow (two photos). |
| Batman: Vengeance | `QPMTRL` | `03-batman-vengeance/05`, `06` | Hidden team photo; Start → credits. |
| Batman: Vengeance | `PSCLCTT` | `03-batman-vengeance/07` | Freezes Advance Mode timer at `9:99`; timer result not captured. |
| Batman: Vengeance | `FLYMODE` | — | Typeable record deliberately routed to invalid path; rejected. |
| Antz Extreme Racing | `*CL3M3NT` then `*M4M1K0` | `04-antz-extreme-racing/02`, `03` | Two-stage gate: first clears the buffer silently, second shows developer photo. |
| Power Rangers: Ninja Storm | `THQ` | `05-power-rangers-ninja-storm/02`, `03` | Credits roll. |
| Power Rangers: Ninja Storm | `GLG` | — | Correct spelling of published `GLW` typo (Thunder Ranger, level 5). |
| Back Track | `TI` | `06-back-track/01` | Hidden numeric debug readout in HUD. |
| Back Track | `FAIL` | — | Writes `0x1FFF` to level failsafe word; no distinct screen. |
| Back Track | `PASSWORD`, `JV` | `06-back-track/02` | In-level terminal context; console uses the published `JAG`/`VINCE` alongside them. |
| Backyard Baseball 2006 | `HOOPS` | `07-backyard-baseball-2006/02`, `03` | Coach name unlocks Barry Dejay (`YOU HAVE UNLOCKED BARRY DEJAY`). |
| Backyard Baseball 2006 | `NACHOS`, `LIBERTY`, `ANCHOVY`, `SPACEMAN`, `SHOWTIME`, `ATLANTIS` | — | Same 9-entry table; not individually re-captured. |
| Big Mutha Truckers | `Up L Right Right A B Down Down R` | `08-big-mutha-truckers/12`, `14` | Evil Bob's truck; white flash. |
| Big Mutha Truckers | `Up Down Left R B A Right L` | `08-big-mutha-truckers/13`, `15` | Accepted; sets bit 1; no reader, so truck unchanged. |
| Kelly Slater's Pro Surfer | `L R L L R R L L L R R R` | `09-kelly-slaters-pro-surfer/01`–`04` | Extras gains four toggles; Beach/Boards show 13/13. Not saved. |
| Dragon Ball GT: Transformation | `Down Up Left Left Down Up Left Left Down Up Left Left Up Up Down Up B` | `10-dragon-ball-gt-transformation/02` | Unlock all five hidden characters; Secrets `26% Unlocked`. |
| Dragon Ball GT: Transformation | `Up Down B Left Right B Lb Rb B Up Left Down Lb Rb Lb Rb B` | `10-dragon-ball-gt-transformation/01` | +20,000 Zeni. |
| Board Game Classics | `000413` | `11-board-game-classics/01`, `02` | Level-1 Fantasy set; unpublished. |
| Golden Nugget Casino | `!!!!v#dbbbxb=` | `12-golden-nugget-casino/03` | Maximum 24-bit bankroll `$16,777,215`; triggers `You're a Multi-Millionaire — Time to retire!`. |
| Barbie as the Princess and the Pauper | `6,6,6,6` | `13-barbie-princess-and-the-pauper/01`, `02` | Four Julians; jumps to end credits. |
| Bomberman Tournament | patched ROM | `14-bomberman-tournament/01`–`04` | `TEST SELECT`, including 16×16 `FLAG SET` editor (256 runtime flags). |
| Crash Bandicoot Purple | `STR4WB3RRY` / `WVMP4FR00T` | `15-crash-bandicoot-purple/02`, `03` | Valid table entries of exactly 10 characters; ACCEPT stops responding at 10. Captured string is `STRAWB3RRY`; see folder note. |
| Legacy of Goku | pause-menu debug | `16-legacy-of-goku/01`, `02` | Debug menu from in-game pause; five functions. |

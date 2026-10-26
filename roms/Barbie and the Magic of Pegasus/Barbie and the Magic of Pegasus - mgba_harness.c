/* Minimal deterministic mGBA harness for evidence gathering.
 * Commands are read from a text file, one per line:
 *   wait N
 *   press KEY
 *   down KEY / up KEY
 *   dump PATH ADDR LEN          (address in GBA bus space, e.g. 0x02000000)
 *   shot PATH                   (writes 240x160 PPM)
 *   save PATH                   (savestate)
 *   load PATH
 *   echo TEXT
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>

#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/gba/core.h>
#include <mgba/internal/gba/input.h>
#include <mgba/core/log.h>

static void nolog(struct mLogger* l, int c, enum mLogLevel v, const char* f, va_list a) { (void)l;(void)c;(void)v;(void)f;(void)a; }
static struct mLogger silent = { nolog, NULL };

static struct mCore* core;
static color_t video[240 * 160];

static int keybit(const char* n) {
	if (!strcasecmp(n, "A")) return GBA_KEY_A;
	if (!strcasecmp(n, "B")) return GBA_KEY_B;
	if (!strcasecmp(n, "SELECT")) return GBA_KEY_SELECT;
	if (!strcasecmp(n, "START")) return GBA_KEY_START;
	if (!strcasecmp(n, "RIGHT")) return GBA_KEY_RIGHT;
	if (!strcasecmp(n, "LEFT")) return GBA_KEY_LEFT;
	if (!strcasecmp(n, "UP")) return GBA_KEY_UP;
	if (!strcasecmp(n, "DOWN")) return GBA_KEY_DOWN;
	if (!strcasecmp(n, "R")) return GBA_KEY_R;
	if (!strcasecmp(n, "L")) return GBA_KEY_L;
	return -1;
}

static uint32_t keys = 0;

static void shot(const char* path) {
	const void* buf;
	size_t stride;
	core->getPixels(core, &buf, &stride);
	FILE* f = fopen(path, "wb");
	if (!f) { perror(path); return; }
	fprintf(f, "P6\n240 160\n255\n");
	const uint8_t* p = buf;
	for (int y = 0; y < 160; y++) {
		for (int x = 0; x < 240; x++) {
			const uint8_t* px = p + (y * stride + x) * 4;
			/* color_t is 0x00RRGGBB little endian: bytes R,G,B,A */
			fputc(px[0], f); fputc(px[1], f); fputc(px[2], f);
		}
	}
	fclose(f);
}

int main(int argc, char** argv) {
	if (argc < 3) { fprintf(stderr, "usage: %s ROM script\n", argv[0]); return 2; }
	mLogSetDefaultLogger(&silent);
	core = GBACoreCreate();
	mCoreInitConfig(core, NULL);
	if (!core->init(core)) { fprintf(stderr, "init fail\n"); return 2; }
	core->setVideoBuffer(core, video, 240);
	if (!mCoreLoadFile(core, argv[1])) { fprintf(stderr, "load fail\n"); return 2; }
	core->reset(core);

	FILE* s = fopen(argv[2], "r");
	if (!s) { perror(argv[2]); return 2; }
	char line[1024];
	while (fgets(line, sizeof line, s)) {
		char cmd[64] = {0}, a1[512] = {0}, a2[128] = {0}, a3[128] = {0};
		int n = sscanf(line, "%63s %511s %127s %127s", cmd, a1, a2, a3);
		if (n <= 0) continue;
		if (cmd[0] == '#' || cmd[0] == '\n') continue;
		if (!strcmp(cmd, "wait")) {
			int f = atoi(a1);
			for (int i = 0; i < f; i++) core->runFrame(core);
		} else if (!strcmp(cmd, "press")) {
			int k = keybit(a1);
			if (k < 0) { fprintf(stderr, "bad key %s\n", a1); continue; }
			keys |= 1u << k; core->setKeys(core, keys);
			for (int i = 0; i < 8; i++) core->runFrame(core);
			keys &= ~(1u << k); core->setKeys(core, keys);
			for (int i = 0; i < 10; i++) core->runFrame(core);
		} else if (!strcmp(cmd, "down")) {
			int k = keybit(a1);
			if (k < 0) continue;
			keys |= 1u << k; core->setKeys(core, keys);
			for (int i = 0; i < 6; i++) core->runFrame(core);
		} else if (!strcmp(cmd, "up")) {
			int k = keybit(a1);
			if (k < 0) continue;
			keys &= ~(1u << k); core->setKeys(core, keys);
			for (int i = 0; i < 6; i++) core->runFrame(core);
		} else if (!strcmp(cmd, "tap")) {
			int k = keybit(a1);
			int f = atoi(a2) ? atoi(a2) : 6;
			int g = atoi(a3) ? atoi(a3) : 6;
			keys |= 1u << k; core->setKeys(core, keys);
			for (int i = 0; i < f; i++) core->runFrame(core);
			keys &= ~(1u << k); core->setKeys(core, keys);
			for (int i = 0; i < g; i++) core->runFrame(core);
		} else if (!strcmp(cmd, "dump")) {
			uint32_t addr = strtoul(a2, NULL, 0);
			uint32_t len = strtoul(a3, NULL, 0);
			unsigned char* buf = malloc(len);
			for (uint32_t i = 0; i < len; i++) buf[i] = core->busRead8(core, addr + i);
			FILE* f = fopen(a1, "wb");
			if (f) { fwrite(buf, 1, len, f); fclose(f); }
			free(buf);
			printf("dumped %s %08x..%08x\n", a1, addr, addr + len);
		} else if (!strcmp(cmd, "shot")) {
			shot(a1);
			printf("shot %s\n", a1);
		} else if (!strcmp(cmd, "save")) {
			size_t sz = core->stateSize(core);
			void* buf = malloc(sz);
			core->saveState(core, buf);
			FILE* f = fopen(a1, "wb");
			if (f) { fwrite(buf, 1, sz, f); fclose(f); printf("saved %s (%zu bytes)\n", a1, sz); }
			free(buf);
		} else if (!strcmp(cmd, "load")) {
			FILE* f = fopen(a1, "rb");
			if (!f) { perror(a1); continue; }
			fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
			void* buf = malloc(sz);
			if (fread(buf, 1, sz, f) != (size_t)sz) { fclose(f); free(buf); continue; }
			fclose(f);
			printf("loadstate %s -> %d\n", a1, core->loadState(core, buf));
			free(buf);

		} else if (!strcmp(cmd, "enum")) {
			/* enum BASE_STATEFILE OUTFILE */
			FILE* bf = fopen(a1, "rb");
			if (!bf) { perror(a1); continue; }
			fseek(bf, 0, SEEK_END); long sz = ftell(bf); fseek(bf, 0, SEEK_SET);
			void* base = malloc(sz);
			if (fread(base, 1, sz, bf) != (size_t)sz) { fclose(bf); free(base); continue; }
			fclose(bf);
			FILE* out = fopen(a2, "w");
			for (int v = 0; v < 1296; v++) {
				int d[4];
				d[0] = v % 6; d[1] = (v / 6) % 6; d[2] = (v / 36) % 6; d[3] = (v / 216) % 6;
				core->loadState(core, base);
				keys = 0; core->setKeys(core, 0);
				for (int s = 0; s < 4; s++) {
					for (int k = 0; k < d[s]; k++) {
						keys |= 1u << GBA_KEY_UP; core->setKeys(core, keys);
						for (int i = 0; i < 6; i++) core->runFrame(core);
						keys &= ~(1u << GBA_KEY_UP); core->setKeys(core, keys);
						for (int i = 0; i < 6; i++) core->runFrame(core);
					}
					if (s < 3) {
						keys |= 1u << GBA_KEY_RIGHT; core->setKeys(core, keys);
						for (int i = 0; i < 6; i++) core->runFrame(core);
						keys &= ~(1u << GBA_KEY_RIGHT); core->setKeys(core, keys);
						for (int i = 0; i < 6; i++) core->runFrame(core);
					}
				}
				keys |= 1u << GBA_KEY_START; core->setKeys(core, keys);
				for (int i = 0; i < 8; i++) core->runFrame(core);
				keys &= ~(1u << GBA_KEY_START); core->setKeys(core, keys);
				for (int i = 0; i < 90; i++) core->runFrame(core);
				uint32_t sid = core->busRead8(core, 0x0300180c);
				uint32_t sid2 = core->busRead8(core, 0x03003654);
				fprintf(out, "%d %d %d %d %u %u\n", d[0], d[1], d[2], d[3], sid, sid2);
				fflush(out);
			}
			fclose(out);
			free(base);
			printf("enum done\n");
		} else if (!strcmp(cmd, "peek16")) {
			uint32_t addr = strtoul(a1, NULL, 0);
			printf("peek16 %08x = %u\n", addr, core->busRead16(core, addr));
		} else if (!strcmp(cmd, "peek")) {
			uint32_t addr = strtoul(a1, NULL, 0);
			printf("peek %08x = %u\n", addr, core->busRead8(core, addr));
		} else if (!strcmp(cmd, "echo")) {
			char rest[900]; rest[0]=0; sscanf(line, "%*s %[^\n]", rest);
			printf("# %s\n", rest);
		} else {
			fprintf(stderr, "unknown cmd %s\n", cmd);
		}
	}
	fclose(s);
	core->deinit(core);
	return 0;
}

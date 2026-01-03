// includes
#include <stdio.h>
#include <gccore.h>
#include "video.h"

// definitions
#define FONT_HEIGHT 16
#define FONT_WIDTH  8

// variables
static void *xfb = NULL;
static GXRModeObj *rmode = NULL;
static const int padding = 20;
static int colsOnScreen;
static int linesOnScreen;

// public
void videoInit(void) {
    VIDEO_Init();
    rmode = VIDEO_GetPreferredMode(NULL);
    xfb = MEM_K0_TO_K1(SYS_AllocateFramebuffer(rmode));
    console_init(xfb,padding,padding,rmode->fbWidth-padding,rmode->xfbHeight-padding,rmode->fbWidth*VI_DISPLAY_PIX_SZ);
    VIDEO_Configure(rmode);
    VIDEO_SetNextFramebuffer(xfb);
    VIDEO_ClearFrameBuffer(rmode, xfb, COLOR_BLACK);
    VIDEO_SetBlack(false);
    VIDEO_Flush();
    VIDEO_WaitVSync();
    if (rmode->viTVMode & VI_NON_INTERLACE)
        VIDEO_WaitVSync();
    colsOnScreen = (rmode->fbWidth - padding) / FONT_WIDTH;
    linesOnScreen = (rmode->xfbHeight - padding) / FONT_HEIGHT;
    printf("nReader 2.5\n");
    for (int i = 0; i < colsOnScreen; i++)
        putchar('-');
    putchar('\n');
    consoleSetWindow(NULL, 1, 3, colsOnScreen, linesOnScreen);
}

void videoWait(int duration) {
    for (int i = 0; i < duration; i++)
        VIDEO_WaitVSync();
}
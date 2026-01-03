// includes
#include <iostream>
#include <gccore.h>
#include "errors.h"
#include "video.h"
#include "nand.h"
#include "net.h"

// definitions
#define DEBUG_MODE false

// main
int main(void) {
    videoInit();
    std::cout << "(C) 2026 hediibl\nLicensed under the MIT\nRunning on IOS" << IOS_GetVersion() << "v" << IOS_GetRevision() << "\n\n";

    if (!DEBUG_MODE) {
        std::cout << "Initializing NAND...";
        executeHandler(nandInit);
    }

    videoWait(55);

    std::cout << "Initializing network...";
    executeHandler(netInit);
    videoWait(55);

    std::cout << "Reading NAND...";
    nandReport report = {};
    executeHandler(nandRead, &report);
    std::cout << "Found " << report.count << " entries.\n";
    videoWait(55);

    std::cout << "Uploading report...";
    executeHandler(netUpload, &report);
    std::cout << "Your report is available at:\nhttps://nreader.eu/pages/nand.php?nand=" << report.serial;
    videoWait(55);
    
    std::cout << "\nThanks you for contributing to Wii history preservation!\nExiting...";
    videoWait(275);
    return 0;

}

#ifndef ERRORS_H
#define ERRORS_H

#include <iostream>
#include <string>
#include <map>
#include <utility>
#include <gccore.h>
#include "video.h"

static const std::map<int, std::string> errorTable = {
    {-1, "UNEXPECTED_MEMORY_ERROR"},
    {-2, "UNEXPECTED_NULL_POINTER"},
    {-101, "AHBPROT_DISABLING_FAILED"},
    {-102, "IOS_PATCHING_FAILED"},
    {-111, "SETTING_OPENING_FAILED"},
    {-112, "SETTING_READING_FAILED"},
    {-113, "SERIAL_EXTRACTING_FAILED"},
    {-121, "TMD_READING_FAILED"},
    {-131, "UID_OPENING_FAILED"},
    {-132, "UID_READING_FAILED"},
    {-201, "NET_DHCP_FAILED"},
    {-202, "NET_DNS_FAILED"},
    {-203, "NET_CONNECT_FAILED"},
    {-211, "NET_SEND_FAILED"},
    {-212, "NET_RCV_FAILED"}
};

template<typename Func, typename... Args>
inline void executeHandler(Func func, Args&&... args) {
    int ret = func(std::forward<Args>(args)...);
    if (ret < 0) {
        auto it = errorTable.find(ret);
        std::string msg = (it != errorTable.end()) ? it->second : "Unhandled exception!";
        std::cout << "failed.\nStop code: " << msg << "\nExiting in 30 seconds." << std::endl;
        videoWait(1650);
        exit(-1);
    }
    std::cout << "success." << std::endl;
}

#endif
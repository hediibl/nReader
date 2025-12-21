# nReader 2.3
# Copyright (C) 2025 hediibl
# Licensed under the GNU GPL v3

import os, platform, configparser, re

def getConfigPath():
    """
    Determine a cross-platform path for the user config file.

    :return: str, full path to the user config file
    """
    systemName = platform.system()
    if systemName == "Windows":
        baseDir = os.getenv("APPDATA", os.path.expanduser("~"))
    elif systemName == "Darwin":
        baseDir = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        baseDir = os.path.expanduser("~/.config")
    configDir = os.path.join(baseDir, "nReader")
    os.makedirs(configDir, exist_ok=True)
    return os.path.join(configDir, "user.ini")

def chooseUsername(currentUsername=None, forcePrompt=False):
    """
    Prompt the user to choose a valid username only if no config exists or if forced.

    :param currentUsername: str, existing username (optional)
    :param forcePrompt: bool, if True, always prompt for username
    :return: str, chosen username (1-32 chars, A-Za-z0-9_-)
    """
    configPath = getConfigPath()
    usernamePattern = re.compile(r'^[A-Za-z0-9_-]{1,32}$')
    if forcePrompt:
        while True:
            prompt = "\nYou have requested to change your username.\nPlease enter your username to continue: "
            name = input(prompt).strip()
            if not name and currentUsername:
                name = currentUsername
            if usernamePattern.match(name):
                return name
            print("Invalid username. Use 1-32 chars, letters, numbers, underscore or dash.")
    if currentUsername:
        return currentUsername
    if os.path.isfile(configPath):
        config = configparser.ConfigParser()
        config.read(configPath)
        if "USER" in config and "username" in config["USER"]:
            return config["USER"]["username"]
    while True:
        prompt = "\nWelcome! It looks like you're using this software for the first time.\nPlease enter your username to continue: "
        name = input(prompt).strip()
        if usernamePattern.match(name):
            return name
        print("Invalid username. Use 1-32 chars, letters, numbers, underscore or dash.")

def rotateLeft32(value):
    """
    Rotate a 32-bit integer left by 1 bit.

    :param value: int, input 32-bit integer
    :return: int, rotated integer
    """
    return ((value << 1) & 0xFFFFFFFF) | (value >> 31)

def xorEncrypt(dataBuffer, isEnc):
    """
    Encrypt or decrypt buffer using a simple XOR-based scheme.
    Only first 256 bytes are affected when decrypting.

    :param dataBuffer: bytes, input data
    :param isEnc: bool, True for encrypt, False for decrypt
    :return: bytes, encrypted or decrypted data
    """
    key = 0x73B5DBFA
    bufferBytes = bytearray(dataBuffer)
    length = len(bufferBytes) if isEnc else min(256, len(bufferBytes))
    for i in range(length):
        bufferBytes[i] ^= key & 0xFF
        key = rotateLeft32(key)
    return bytes(bufferBytes)

def getSerialNumber(settingsPath):
    """
    Extract the serial number from a Wii settings file.

    :param settingsPath: str, path to the settings file
    :return: str, extracted serial number
    """
    if not os.path.isfile(settingsPath):
        raise FileNotFoundError(f"Settings file not found: {settingsPath}")
    with open(settingsPath, "rb") as f:
        encryptedData = f.read()
    decryptedData = xorEncrypt(encryptedData, isEnc=True)
    decodedData = decryptedData.decode("ascii", errors="ignore")
    parameters = [p for p in re.split(r'[\r\n]+', decodedData) if p]
    if len(parameters) < 6:
        raise ValueError("Settings file corrupted or invalid format")
    try:
        part1 = parameters[4].split("=")[1]
        part2 = parameters[5].split("=")[1]
    except IndexError:
        raise ValueError("Serial number fields missing in settings")
    return f"{part1}{part2}"

def validateForcedSerial(serial):
    """
    Validate a user-provided forced serial number.

    :param serial: str, forced serial
    :return: str, uppercase serial if valid
    :raises ValueError: if serial format invalid
    """
    serialUpper = serial.upper()
    pattern = re.compile(r'^[A-Z0-9]{10,14}$')
    if not pattern.match(serialUpper):
        raise ValueError("Forced serial is invalid. Must be 10-14 chars, uppercase letters and digits only.")
    return serialUpper

def writeUserConfig(username):
    """
    Write only the username to the user config file.

    :param username: str, username to save
    """
    configPath = getConfigPath()
    config = configparser.ConfigParser()
    config["USER"] = {"username": username}
    with open(configPath, "w", encoding="utf-8") as f:
        config.write(f)
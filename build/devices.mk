# Try to detect plugged device name
DEVICE_NAME ?= desktop
ADB_DEVICE := $(shell $(ADB) shell getprop ro.product.device)

ifeq ($(TARGET_DEVICE),)
$(warning No TARGET_DEVICE value defined.)
else
DEVICE_NAME := $(TARGET_DEVICE)
endif

ifeq ($(ADB_DEVICE),)
$(warning No device connected.)
else
DEVICE_NAME := $(ADB_DEVICE)
endif

ifneq ($(DEVICE_NAME),)
$(info Producing gaia for '$(DEVICE_NAME)')
endif

ifeq ($(FORCE_DEVICE_NAME),) # User does not knows what he is doing
ifneq ($(DEVICE_NAME),$(ADB_DEVICE)) # Mismatch between what we detect and what we are asked
ifneq ($(ADB_DEVICE),) # Stop only if there is a device connected
$(error Mismatching device name and connected device. Set FORCE_DEVICE_NAME if you know what you are doing.)
endif
endif
endif

ifneq ($(DEVICE_NAME),)
DEVICE_DEFINITIONS := build/devices/$(DEVICE_NAME).mk
$(info Calling $(DEVICE_DEFINITIONS))
include $(DEVICE_DEFINITIONS)
endif

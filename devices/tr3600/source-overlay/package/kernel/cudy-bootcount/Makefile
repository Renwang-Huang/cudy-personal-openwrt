include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/kernel.mk

PKG_NAME:=cudy-bootcount
PKG_RELEASE:=1
PKG_LICENSE:=BSD-3-Clause
PKG_BUILD_DIR:=$(KERNEL_BUILD_DIR)/$(PKG_NAME)

include $(INCLUDE_DIR)/package.mk

define KernelPackage/cudy-bootcount
  SUBMENU:=Other modules
  TITLE:=Cudy TR3600 vendor A/B boot count reset
  DEPENDS:=@TARGET_mediatek_filogic
  FILES:=$(PKG_BUILD_DIR)/cudy_bootcount.ko
  AUTOLOAD:=$(call AutoLoad,80,cudy_bootcount)
endef

define Build/Prepare
	$(INSTALL_DIR) $(PKG_BUILD_DIR)
	$(CP) ./src/* $(PKG_BUILD_DIR)/
endef

define Build/Compile
	+$(KERNEL_MAKE) M="$(PKG_BUILD_DIR)" modules
endef

$(eval $(call KernelPackage,cudy-bootcount))

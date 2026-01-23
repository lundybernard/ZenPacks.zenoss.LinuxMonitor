##############################################################################
#
# Copyright (C) Zenoss, Inc. 2017, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from Products.ZenModel.RRDTemplate import manage_addRRDTemplate

from ZenPacks.zenoss.ZenPackLib import zenpacklib
from ..FileSystem import FileSystem

zenpacklib.enableTesting()


class FileSystemTests(zenpacklib.TestCase):
    def afterSetUp(self):
        super(FileSystemTests, self).afterSetUp()

        dc = self.dmd.Devices.createOrganizer("/Server/SSH/Linux")
        dc.setZenProperty("zPythonClass", "ZenPacks.zenoss.LinuxMonitor.LinuxDevice")

        self.device = dc.createInstance("linux-FileSystemTests")
        self.device.setManageIp("127.0.0.1")
        self.device.setPerformanceMonitor("localhost")

    def test_getRRDTemplates(self):
        boot_fs = FileSystem("boot")
        boot_fs.mount = "/boot"
        boot_fs.type = "ext4"
        self.device.os.filesystems._setObject(boot_fs.id, boot_fs)
        boot_fs = self.device.os.filesystems.boot

        nfs_fs = FileSystem("nfs")
        nfs_fs.mount = "/nfs"
        nfs_fs.type = "nfs"
        self.device.os.filesystems._setObject(nfs_fs.id, nfs_fs)
        nfs_fs = self.device.os.filesystems.nfs

        nfs4_fs = FileSystem("nfs4")
        nfs4_fs.mount = "/nfs4"
        nfs4_fs.type = "nfs4"
        self.device.os.filesystems._setObject(nfs4_fs.id, nfs4_fs)
        nfs4_fs = self.device.os.filesystems.nfs4

        # No templates exist.
        boot_templates = boot_fs.getRRDTemplates()
        self.assertEqual(len(boot_templates), 0)

        nfs_templates = nfs_fs.getRRDTemplates()
        self.assertEqual(len(nfs_templates), 0)

        # Only the FileSystem template exists.
        manage_addRRDTemplate(self.dmd.Devices.rrdTemplates, "FileSystem")

        boot_templates = boot_fs.getRRDTemplates()
        self.assertEqual(len(boot_templates), 1)
        self.assertEqual(boot_templates[0].id, "FileSystem")

        nfs_templates = nfs_fs.getRRDTemplates()
        self.assertEqual(len(nfs_templates), 0)

        # FileSystem and FileSystem_NFS_Client templates exist.
        manage_addRRDTemplate(self.dmd.Devices.rrdTemplates, "FileSystem_NFS_Client")

        boot_templates = boot_fs.getRRDTemplates()
        self.assertEqual(len(boot_templates), 1)
        self.assertEqual(boot_templates[0].id, "FileSystem")

        nfs_templates = nfs_fs.getRRDTemplates()
        self.assertEqual(len(nfs_templates), 1)
        self.assertEqual(nfs_templates[0].id, "FileSystem_NFS_Client")

        nfs4_templates = nfs4_fs.getRRDTemplates()
        self.assertEqual(len(nfs4_templates), 1)
        self.assertEqual(nfs4_templates[0].id, "FileSystem_NFS_Client")

    def test_template_selection_fallback(self):
        nfs_fs = FileSystem("nfs_test")
        nfs_fs.mount = "/nfs_test"
        nfs_fs.type = "nfs"
        self.device.os.filesystems._setObject(nfs_fs.id, nfs_fs)
        nfs_fs = self.device.os.filesystems.nfs_test

        ext4_fs = FileSystem("ext4_test")
        ext4_fs.mount = "/boot"
        ext4_fs.type = "ext4"
        self.device.os.filesystems._setObject(ext4_fs.id, ext4_fs)
        ext4_fs = self.device.os.filesystems.ext4_test

        manage_addRRDTemplate(self.dmd.Devices.rrdTemplates, "FileSystem")
        manage_addRRDTemplate(self.dmd.Devices.rrdTemplates, "FileSystem_NFS_Client")

        self.assertEqual([t.id for t in nfs_fs.getRRDTemplates()], ["FileSystem_NFS_Client"])
        self.assertEqual([t.id for t in ext4_fs.getRRDTemplates()], ["FileSystem"])

        manage_addRRDTemplate(self.dmd.Devices.rrdTemplates, "FileSystem-replacement")

        # For EXT4: Should use the replacement.
        self.assertEqual([t.id for t in ext4_fs.getRRDTemplates()], ["FileSystem-replacement"])

        # For NFS: Should Fallback to FileSystem_NFS_Client.
        self.assertEqual([t.id for t in nfs_fs.getRRDTemplates()], ["FileSystem_NFS_Client"])
        manage_addRRDTemplate(self.dmd.Devices.rrdTemplates, "FileSystem_NFS_Client-replacement")

        # For NFS: Should now find and use the specific NFS replacement.
        self.assertEqual([t.id for t in nfs_fs.getRRDTemplates()], ["FileSystem_NFS_Client-replacement"])
        manage_addRRDTemplate(self.dmd.Devices.rrdTemplates, "FileSystem-addition")
        manage_addRRDTemplate(self.dmd.Devices.rrdTemplates, "FileSystem_NFS_Client-addition")

        # For EXT4: Should have replacement AND addition
        ext4_templates = sorted([t.id for t in ext4_fs.getRRDTemplates()])
        self.assertEqual(ext4_templates, ["FileSystem-addition", "FileSystem-replacement"])

        # For NFS: Should have NFS replacement AND NFS addition
        nfs_templates = sorted([t.id for t in nfs_fs.getRRDTemplates()])
        self.assertEqual(nfs_templates, ["FileSystem_NFS_Client-addition", "FileSystem_NFS_Client-replacement"])

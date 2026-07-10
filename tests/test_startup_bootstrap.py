import types
import unittest


class StartupBootstrapTests(unittest.TestCase):
    def test_auto_mode_disables_wmi_probe_on_windows_python312(self):
        from tools import startup_bootstrap

        fake_platform = types.SimpleNamespace(
            _uname_cache=object(),
            _wmi_query=lambda *_args: ("unexpected",),
            machine=lambda: "before",
        )

        result = startup_bootstrap.apply_startup_patches(
            platform_module=fake_platform,
            environ={"GPT_SOVITS_DISABLE_WMI_PROBE": "auto", "PROCESSOR_ARCHITECTURE": "AMD64"},
            version_info=(3, 12, 3),
            os_name="nt",
            logger=lambda _message: None,
        )

        self.assertTrue(result.wmi_disabled)
        self.assertTrue(result.machine_overridden)
        self.assertIsNone(fake_platform._uname_cache)
        self.assertEqual(fake_platform.machine(), "AMD64")
        with self.assertRaises(OSError):
            fake_platform._wmi_query("OS", "Version")

    def test_false_mode_leaves_platform_untouched(self):
        from tools import startup_bootstrap

        original_query = lambda *_args: ("ok",)
        fake_platform = types.SimpleNamespace(
            _uname_cache="cached",
            _wmi_query=original_query,
            machine=lambda: "before",
        )

        result = startup_bootstrap.apply_startup_patches(
            platform_module=fake_platform,
            environ={"GPT_SOVITS_DISABLE_WMI_PROBE": "0", "PROCESSOR_ARCHITECTURE": "AMD64"},
            version_info=(3, 12, 3),
            os_name="nt",
            logger=lambda _message: None,
        )

        self.assertFalse(result.wmi_disabled)
        self.assertFalse(result.machine_overridden)
        self.assertEqual(fake_platform._uname_cache, "cached")
        self.assertIs(fake_platform._wmi_query, original_query)


if __name__ == "__main__":
    unittest.main()

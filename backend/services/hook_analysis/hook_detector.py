import re


class HookDetector:

    HOOK_PATTERNS = [
        r"@BeforeSuite",
        r"@BeforeMethod",
        r"@AfterMethod",
        r"beforeEach",
        r"afterEach",
        r"pytest.fixture"
    ]

    @staticmethod
    def detect_hooks(file_content: str):
        hooks = []

        for pattern in HookDetector.HOOK_PATTERNS:
            if re.search(pattern, file_content):
                hooks.append(pattern)

        return hooks

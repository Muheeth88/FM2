"""
Standard verification script for Step 9 — Intent Extraction Service.
Tests: Python and Java AST extraction, cross-file resolution, 
Selenium action detection, assertions, and lifecycle hooks.
"""

import sys
import os
import json
import tempfile
import sqlite3
import shutil

# Allow direct execution from backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.intent_extractor_service import (
    IntentExtractorService,
    ASTExtractor,
    IntentNormalizer,
    generate_intent_hash,
)

PASS = 0
FAIL = 0

def check(label, condition):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label}")
        FAIL += 1

# --------------------------------------------------
# 1. Test Java Selenium API Detection
# --------------------------------------------------
print("\n[1] Java Selenium API Detection")
java_code = '''
package com.test;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.testng.Assert;
import org.testng.annotations.Test;

public class MyTest {
    @Test
    public void testLogin() {
        driver.get("https://google.com");
        driver.findElement(By.id("user")).sendKeys("admin");
        driver.findElement(By.xpath("//button")).click();
        Assert.assertEquals(driver.getTitle(), "Dashboard");
    }
}
'''
with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
    f.write(java_code)
    tmp_path = f.name

extractor = ASTExtractor()
raw = extractor.parse_files([tmp_path])
normalizer = IntentNormalizer()
normalized = normalizer.normalize(raw)

steps = normalized.get('steps', [])
check("Java: navigate action detected", any(s['action'] == 'navigate' and s.get('url') == 'https://google.com' for s in steps))
check("Java: type action detected", any(s['action'] == 'type' and s.get('locator', {}).get('value') == 'user' for s in steps))
check("Java: click action detected", any(s['action'] == 'click' and s.get('locator', {}).get('value') == '//button' for s in steps))

assertions = normalized.get('assertions', [])
check("Java: assertion detected", len(assertions) > 0)
check("Java: equals operator detected", any(a['operator'] == 'equals' for a in assertions))

os.unlink(tmp_path)

# --------------------------------------------------
# 2. Test Cross-File Page Object Resolution
# --------------------------------------------------
print("\n[2] Cross-File Page Object Resolution")

# Create a mock workspace
workspace_dir = tempfile.mkdtemp()
page_code = '''
package com.pages;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class LoginPage {
    private By txtUser = By.id("username");
    private By btnLogin = By.xpath("//login");
    
    public void login(String u) {
        driver.findElement(txtUser).sendKeys(u);
        driver.findElement(btnLogin).click();
    }
}
'''
test_code = '''
package com.test;
import com.pages.LoginPage;
import org.testng.annotations.Test;

public class LoginTest {
    @Test
    public void testMe() {
        LoginPage lp = new LoginPage();
        lp.login("myuser");
    }
}
'''
page_path = os.path.join(workspace_dir, "LoginPage.java")
test_path = os.path.join(workspace_dir, "LoginTest.java")

with open(page_path, 'w', encoding='utf-8') as f: f.write(page_code)
with open(test_path, 'w', encoding='utf-8') as f: f.write(test_code)

extractor = ASTExtractor()
extractor.build_workspace_index([page_path, test_path])
raw = extractor.parse_files([test_path])
normalized = normalizer.normalize(raw)

steps = normalized.get('steps', [])
# Should have 2 steps from expansion
check("Expanded steps count", len(steps) == 2)
check("Resolved locator from Po field (type)", any(s['action'] == 'type' and s.get('locator', {}).get('value') == 'username' for s in steps))
check("Resolved locator from Po field (click)", any(s['action'] == 'click' and s.get('locator', {}).get('value') == '//login' for s in steps))
check("Source method trace present", any(s.get('source_method') == 'LoginPage.login' for s in steps))

# Locators repository check
check("Locators repository populated", len(normalized.get('locators', [])) >= 2)

shutil.rmtree(workspace_dir)

# --------------------------------------------------
# 3. Test Lifecycle Hook Detection
# --------------------------------------------------
print("\n[3] Java Lifecycle Hook Detection")
hook_code = '''
import org.testng.annotations.*;

public class Base {
    @BeforeMethod
    public void setup() {
        BrowserFactory.getDriver();
    }
    
    @AfterSuite
    public void tear() {
        driver.quit();
    }
}
'''
with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
    f.write(hook_code)
    tmp_path = f.name

raw = extractor.parse_files([tmp_path])
normalized = normalizer.normalize(raw)
hooks = normalized.get('lifecycle_hooks', [])

check("Lifecycle hooks count", len(hooks) == 2)
check("BeforeMethod -> beforeEach", any(h['type'] == 'beforeEach' and h['action'] == 'driver_init' for h in hooks))
check("AfterSuite -> afterAll", any(h['type'] == 'afterAll' and h['action'] == 'browser_close' for h in hooks))

os.unlink(tmp_path)

# --------------------------------------------------
# 4. Phase 2 Refinements (Filtering, Control Flow, Warnings)
# --------------------------------------------------
print("\n[4] Phase 2: Refinements")

# Test 4.1: Smart Locator Filtering
# Create a Page Object with 3 locators, but only use 1 in the test.
workspace_dir = tempfile.mkdtemp()
page_code = '''
package com.pages;
import org.openqa.selenium.By;

public class FilterPage {
    private By usedLoc = By.id("used");
    private By unusedLoc1 = By.id("unused1");
    private By unusedLoc2 = By.id("unused2");
    
    public void doWork() {
        driver.findElement(usedLoc).click();
    }
}
'''
test_code = '''
package com.test;
import com.pages.FilterPage;
import org.testng.annotations.Test;

public class FilterTest {
    @Test
    public void testFilter() {
        FilterPage fp = new FilterPage();
        fp.doWork();
    }
}
'''
page_path = os.path.join(workspace_dir, "FilterPage.java")
test_path = os.path.join(workspace_dir, "FilterTest.java")
with open(page_path, 'w', encoding='utf-8') as f: f.write(page_code)
with open(test_path, 'w', encoding='utf-8') as f: f.write(test_code)

extractor = ASTExtractor()
extractor.build_workspace_index([page_path, test_path])
raw = extractor.parse_files([test_path])
normalized = normalizer.normalize(raw)

locators = normalized.get('locators', [])
check("Filtering: Only 1 locator present", len(locators) == 1)
check("Filtering: Correct locator present", any(l['field_name'] == 'usedLoc' for l in locators))

# Test 4.2: Control Flow Detection
control_code = '''
public class ControlTest {
    @Test
    public void testFlow() {
        if (true) {
            driver.findElement(By.id("msg")).getText();
        }
        for (int i=0; i<3; i++) {
            System.out.println(i);
        }
    }
}
'''
with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
    f.write(control_code)
    tmp_path = f.name

raw = extractor.parse_files([tmp_path])
normalized = normalizer.normalize(raw)
cf = normalized.get('control_flow', [])
check("Control Flow: if detected", any(c['action'] == 'if' for c in cf))
check("Control Flow: for detected", any(c['action'] == 'for' for c in cf))
os.unlink(tmp_path)

# Test 4.3: Empty Step Warning
empty_code = '''
public class EmptyTest {
    @Test
    public void testNothing() {
        // No selenium actions here
        int x = 1 + 1;
    }
}
'''
with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
    f.write(empty_code)
    tmp_path = f.name

raw = extractor.parse_files([tmp_path])
normalized = normalizer.normalize(raw)
warnings = normalized.get('validation_warnings', [])
check("Empty Warning: warning present", len(warnings) > 0)
check("Empty Warning: correct message", "No executable steps" in warnings[0])
os.unlink(tmp_path)

shutil.rmtree(workspace_dir)

# --------------------------------------------------
# Summary
# --------------------------------------------------
print(f"\n{'='*40}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("All checks passed! [PASS]")
else:
    print("Some checks failed. [FAIL]")
    sys.exit(1)

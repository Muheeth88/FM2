import sys
import os
import json
from unittest.mock import MagicMock

# Allow direct execution from backend/
sys.path.insert(0, os.path.dirname(__file__))

from services.intent_extractor_service import IntentExtractorService

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

def create_dummy_java_file(filename):
    content = """
    public class TestOrder {
        @Test
        public void testLoginFlow() {
            // Statement 1: Chained call
            // Expected: waitHome -> clickLogin
            loginPage.waitForHome().clickLogin();

            // Statement 2: Chained call with arguments
            // Expected: typeEmail -> typePassword -> clickSubmit
            loginPage.typeEmail("test@example.com")
                     .typePassword("password123")
                     .clickSubmit();

            // Statement 3: Separate statements
            // Expected: waitDashboard
            dashboardPage.waitForDashboard();
            
            // Expected: verifyUser
            Assert.assertEquals(dashboardPage.getUserName(), "Test User");
        }
    }
    """
    with open(filename, "w") as f:
        f.write(content)
    return os.path.abspath(filename)

def test_extraction_order():
    global PASS, FAIL
    print("\n[1] Testing AST Extraction Order")
    
    # Setup
    db_path = "test_order.db"
    if os.path.exists(db_path): os.unlink(db_path)
    service = IntentExtractorService(db_path=db_path)
    
    # Create dummy file
    java_file = create_dummy_java_file("TestOrder.java")
    
    try:
        # Parse
        # We need to mock the workspace index to avoid errors if it tries to resolve external classes
        # But for this simple case, the extractor might just treat them as standard method calls if not resolved
        # strict resolution might skip them if not found in workspace, 
        # but the current logic has fallbacks for "unknown" sources or captures them if they match patterns.
        # Let's see if our patterns match.
        # "clickLogin" -> matches "click" pattern if mapped? 
        # Wait, the patterns are regex or substring checks in `_extract_actions_from_body`.
        
        # We need to ensure the method names match the keys in SELENIUM_ACTION_METHODS etc.
        # or we update the dummy file to use standard names/wrappers.
        
        # Updating dummy content to match standard detection patterns better
        content = """
        public class TestOrder {
            @Test
            public void testLoginFlow() {
                // 1. Navigation
                driver.get("http://url.com");
                
                // 2. Chained findElement
                driver.findElement(By.id("user")).sendKeys("admin");
                
                // 3. Wrapper-like calls (assuming mapped in WRAPPER_ACTION_METHODS)
                // Let's use names that are likely mapped: click, type, wait
                
                // Statement 3: Chain
                // loginPage.click(btn) -> type(input) [Hypothetical fluent API]
                // If the extractor executes in order of statement, it should be fine.
                // If it executes in order of chain, it should be a -> b.
                
                // Let's use simple separate statements first to verify statement order
                driver.findElement(By.id("A")).click();
                driver.findElement(By.id("B")).click();
                
                // Now a chain if supported (Java fluent interface)
                // Note: Standard Selenium isn't fluent like this, but frameworks are.
                // Assuming we support method_invocation chaining logic:
                // obj.actionA().actionB()
                
                FluentPage.start()
                    .click(By.id("C"))
                    .type(By.id("D"), "text");
            }
        }
        """
        # Overwrite with better example
        with open("TestOrder.java", "w") as f:
            f.write(content)

        # We need to mock some mappings if they aren't default.
        # IntentExtractorService has standard SELENIUM_ACTION_METHODS.
        # Let's inspect what's available.
        # It supports 'click', 'sendKeys', 'type', etc.
        
        raw_model = service.ast_extractor.parse_files([java_file])
        
        # We expect one feature from the file
        feature = next(iter(raw_model.values()))
        steps = feature['raw_steps']
        
        print(f"Extracted {len(steps)} steps")
        for i, s in enumerate(steps):
            try:
                val = s.get('value')
                if not val and s.get('locator'):
                    val = s['locator'].get('value', 'N/A')
                print(f"  {i}: {s['action']} - {val}")
            except Exception as e:
                print(f"  {i}: {s['action']} - <Error printing value: {e}>")

        # Verification Logic
        # 1. navigate
        check("Step 1 is navigate", steps[0]['action'] == 'navigate')
        
        # 2. findElement...sendKeys
        check("Step 2 is type (sendKeys)", steps[1]['action'] in ('type', 'sendKeys'))
        check("Step 2 value is admin", steps[1].get('value') == "admin")

        # 3. click A
        check("Step 3 is click", steps[2]['action'] == 'click')
        check("Step 3 locator is A", steps[2]['locator']['value'] == "A")

        # 4. click B
        check("Step 4 is click", steps[3]['action'] == 'click')
        check("Step 4 locator is B", steps[3]['locator']['value'] == "B")
        
        # 5. Fluent chain: start() -> click(C) -> type(D)
        # start() might be ignored if not an action.
        # click(C) should be next
        # type(D) should be last
        
        # Note: The extractor logic for `method_invocation` handles chains.
        # It unrolls `start().click().type()` to `[start, click, type]` and visits in order.
        # If `click` matches WRAPPER_ACTION_METHODS, it captures it.
        
        # Depending on how `FluentPage` is resolved, it might go into "Wrapper methods" path (3).
        # We need to ensure `click` and `type` are in WRAPPER_ACTION_METHODS.
        # They usually are.
        
        check("Step 5 is click (Fluent)", steps[4]['action'] == 'click')
        check("Step 5 locator is C", steps[4]['locator']['value'] == '"C"') # String literal usually keeps quotes in some parsers, or stripped.
        # Actually `_resolve_locator_from_args` might handle quotes. 
        # If passed as `By.id("C")`, it might be complex. 
        # If passed as direct arg `click(By.id("C"))`, logic 3 handles it.
        
        check("Step 6 is type (Fluent)", steps[5]['action'] == 'type')
        check("Step 6 value is text", steps[5]['value'] == '"text"') # String literal

    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        FAIL += 1
    finally:
        if os.path.exists("TestOrder.java"): os.unlink("TestOrder.java")
        if os.path.exists(db_path): os.unlink(db_path)

def test_trivial_file():
    global PASS, FAIL
    print("\n[0] Testing Trivial Java File")
    db_path = "test_order_trivial.db"
    if os.path.exists(db_path): os.unlink(db_path)
    service = IntentExtractorService(db_path=db_path)
    
    with open("Trivial.java", "w") as f:
        f.write('public class Trivial { @Test public void testEmpty() {} }')
    
    try:
        raw_model = service.ast_extractor.parse_files([os.path.abspath("Trivial.java")])
        print(f"Extracted {len(raw_model)} features (should be 1)")
        check("Trivial file parsed", len(raw_model) == 1)
    except Exception as e:
        print(f"EXCEPTION in Trivial: {e}")
        import traceback
        traceback.print_exc()
        FAIL += 1
    finally:
        sys.stdout.flush()
        if os.path.exists("Trivial.java"): os.unlink("Trivial.java")
        if os.path.exists(db_path): os.unlink(db_path)

if __name__ == "__main__":
    test_trivial_file()
    test_extraction_order()
    print(f"\nFinal Results: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        sys.exit(1)

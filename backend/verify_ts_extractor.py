import os
import tempfile
import shutil
from pathlib import Path
from services.feature_extraction.ts_extractor import TSFeatureExtractor

def test_ts_extractor():
    # Create a temporary directory for the mock repo
    repo_root = tempfile.mkdtemp()
    try:
        # Create a sample TypeScript test file
        test_file_path = Path(repo_root) / "sample_test.ts"
        test_file_path.write_text("""
        import { test, expect } from '@playwright/test';

        test('basic test', async ({ page }) => {
            await page.goto('https://playwright.dev/');
            const title = page.locator('.navbar__inner .navbar__title');
            await expect(title).toHaveText('Playwright');
        });
        """, encoding="utf-8")

        # Create a sample JavaScript test file
        js_file_path = Path(repo_root) / "sample_test.js"
        js_file_path.write_text("""
        it('should login', () => {
            cy.visit('/login');
            cy.get('#user').type('admin');
        });
        """, encoding="utf-8")

        # Initialize the extractor
        extractor = TSFeatureExtractor(repo_root)
        
        # Extract features
        features = extractor.extract_features()
        
        print(f"Extracted {len(features)} features")
        for f in features:
            print(f"Feature: {f['feature_name']}, Framework: {f['framework']}, Tests: {len(f['tests'])}")
            for t in f['tests']:
                print(f"  Test: {t['name']}")

        assert len(features) == 2
        frameworks = [f['framework'] for f in features]
        assert "Playwright" in frameworks
        assert "Cypress" in frameworks
        
        print("\nSuccess! TSFeatureExtractor is working correctly.")

    finally:
        shutil.rmtree(repo_root)

if __name__ == "__main__":
    test_ts_extractor()

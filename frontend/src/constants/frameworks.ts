export interface FrameworkData {
    framework: string;
    languages: {
        [language: string]: string[];
    };
}

export const FRAMEWORK_DATA: FrameworkData[] = [
    {
        framework: "Selenium",
        languages: {
            "Java": ["JUnit", "TestNG", "Cucumber", "Selenide", "Serenity"],
            "JavaScript": ["NightwatchJS", "WebDriverIO", "TestCafe", "Jest", "Mocha", "Karma", "Jasmine"],
            "C Sharp": ["NUnit", "Specflow", "Reqnroll"],
            "Python": ["Pytest", "Robot", "Behave", "Lettuce"]
        }
    },
    {
        framework: "Cypress",
        languages: {
            "JavaScript": ["Mocha", "Jest"]
        }
    },
    {
        framework: "Playwright",
        languages: {
            "Java": ["JUnit"],
            "JavaScript": ["Jest", "CucumberJS", "PlaywrightTest"],
            "TypeScript": ["Jest", "CucumberJS", "PlaywrightTest"],
            "C Sharp": ["NUnit", "Specflow", "Reqnroll"],
            "Python": ["Pytest", "Robot", "Behave", "Lettuce"]
        }
    },
    {
        framework: "Puppeteer",
        languages: {
            "JavaScript": ["Jest", "Codecept", "Mocha"]
        }
    }
];

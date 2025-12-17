/* Enable UI Customizations */
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);

/* PhazeSearch Start Page */
user_pref("browser.startup.homepage", "file:///opt/phazebrowser/start.html");
user_pref("browser.newtabpage.enabled", true);
user_pref("browser.newtab.url", "file:///opt/phazebrowser/start.html");

/* Visuals */
user_pref("browser.toolbars.bookmarks.visibility", "never");
user_pref("browser.theme.content-theme", 0);
user_pref("browser.theme.toolbar-theme", 0);
user_pref("extensions.activeThemeID", "firefox-compact-dark@mozilla.org");
user_pref("browser.display.background_color", "#0f0f1a");
user_pref("browser.display.foreground_color", "#ffffff");

/* DISABLE SIGNATURE ENFORCEMENT (Fixes 'Invalid Extension' errors) */
user_pref("xpinstall.signatures.required", false);
user_pref("extensions.langpacks.signatures.required", false);

/* Disable Telemetry & Remote Settings Spam */
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("services.settings.server", ""); /* Kill remote settings sync to stop signature errors */
user_pref("messaging-system-ui.enabled", false);
user_pref("app.normandy.enabled", false);
user_pref("app.shield.optoutstudies.enabled", false);

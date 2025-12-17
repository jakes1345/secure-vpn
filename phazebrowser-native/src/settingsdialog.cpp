#include "settingsdialog.h"
#include "datamanager.h"
#include "privacyengine.h"
#include "searchmanager.h"
#include "searchmanager.h"
#include <QFormLayout>
#include <QLabel>
#include <QMessageBox>
#include <QInputDialog>
#include <QFileDialog>
#include <QJsonObject>

SettingsDialog::SettingsDialog(DataManager *dataManager, PrivacyEngine *privacyEngine, SearchManager *searchManager, QWidget *parent)
    : QDialog(parent)
    , dataManager(dataManager)
    , privacyEngine(privacyEngine)
    , searchManager(searchManager)
{
    setWindowTitle("Settings");
    setMinimumSize(600, 500);
    setupUI();
    loadSettings();
}

void SettingsDialog::setupUI()
{
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    
    tabs = new QTabWidget(this);
    
    // Privacy Tab
    QWidget *privacyTab = new QWidget();
    QVBoxLayout *privacyLayout = new QVBoxLayout(privacyTab);
    
    QGroupBox *blockingGroup = new QGroupBox("Content Blocking");
    QVBoxLayout *blockingLayout = new QVBoxLayout(blockingGroup);
    
    adBlockingCheck = new QCheckBox("Ad Blocking");
    trackingProtectionCheck = new QCheckBox("Tracking Protection");
    fingerprintProtectionCheck = new QCheckBox("Fingerprint Protection");
    cookieBlockingCheck = new QCheckBox("Cookie Blocking");
    blockAllCookiesCheck = new QCheckBox("Block ALL Cookies (Ghost Mode)");
    blockFontsCheck = new QCheckBox("Block Font Loading (Prevent Font Fingerprinting)");
    
    blockingLayout->addWidget(adBlockingCheck);
    blockingLayout->addWidget(trackingProtectionCheck);
    blockingLayout->addWidget(fingerprintProtectionCheck);
    blockingLayout->addWidget(cookieBlockingCheck);
    blockingLayout->addWidget(blockAllCookiesCheck);
    blockingLayout->addWidget(blockFontsCheck);
    
    privacyLayout->addWidget(blockingGroup);
    
    QGroupBox *permissionsGroup = new QGroupBox("Permissions");
    QVBoxLayout *permissionsLayout = new QVBoxLayout(permissionsGroup);
    
    blockCameraCheck = new QCheckBox("Block Camera Access");
    blockMicrophoneCheck = new QCheckBox("Block Microphone Access");
    blockGeolocationCheck = new QCheckBox("Block Geolocation");
    blockNotificationsCheck = new QCheckBox("Block Notifications");
    
    permissionsLayout->addWidget(blockCameraCheck);
    permissionsLayout->addWidget(blockMicrophoneCheck);
    permissionsLayout->addWidget(blockGeolocationCheck);
    permissionsLayout->addWidget(blockNotificationsCheck);
    
    privacyLayout->addWidget(permissionsGroup);
    privacyLayout->addStretch();
    
    tabs->addTab(privacyTab, "Privacy");
    
    // Search Tab
    QWidget *searchTab = new QWidget();
    QVBoxLayout *searchLayout = new QVBoxLayout(searchTab);
    
    QFormLayout *searchForm = new QFormLayout();
    
    defaultSearchCombo = new QComboBox();
    if (searchManager) {
        QList<SearchEngine> engines = searchManager->searchEngines();
        for (const SearchEngine &engine : engines) {
            defaultSearchCombo->addItem(engine.name, engine.keyword);
        }
    }
    searchForm->addRow("Default Search Engine:", defaultSearchCombo);
    
    searchLayout->addLayout(searchForm);
    
    QHBoxLayout *searchButtonsLayout = new QHBoxLayout();
    addSearchEngineBtn = new QPushButton("Add Search Engine");
    editSearchEngineBtn = new QPushButton("Edit");
    removeSearchEngineBtn = new QPushButton("Remove");
    
    connect(addSearchEngineBtn, &QPushButton::clicked, [this]() {
        QString name = QInputDialog::getText(this, "Add Search Engine", "Name:");
        QString keyword = QInputDialog::getText(this, "Add Search Engine", "Keyword:");
        QString url = QInputDialog::getText(this, "Add Search Engine", "URL (use %s for query):");
        if (!name.isEmpty() && !keyword.isEmpty() && !url.isEmpty()) {
            SearchEngine engine(name, keyword, url);
            searchManager->addEngine(engine);
            defaultSearchCombo->addItem(name, keyword);
        }
    });
    
    connect(editSearchEngineBtn, &QPushButton::clicked, [this]() {
        // TODO: Edit search engine
    });
    
    connect(removeSearchEngineBtn, &QPushButton::clicked, [this]() {
        QString keyword = defaultSearchCombo->currentData().toString();
        if (!keyword.isEmpty()) {
            searchManager->removeEngine(keyword);
            defaultSearchCombo->removeItem(defaultSearchCombo->currentIndex());
        }
    });
    
    searchButtonsLayout->addWidget(addSearchEngineBtn);
    searchButtonsLayout->addWidget(editSearchEngineBtn);
    searchButtonsLayout->addWidget(removeSearchEngineBtn);
    searchLayout->addLayout(searchButtonsLayout);
    searchLayout->addStretch();
    
    tabs->addTab(searchTab, "Search");
    
    // Appearance Tab
    QWidget *appearanceTab = new QWidget();
    QVBoxLayout *appearanceLayout = new QVBoxLayout(appearanceTab);
    
    QFormLayout *appearanceForm = new QFormLayout();
    
    themeCombo = new QComboBox();
    themeCombo->addItems(QStringList() << "Dark" << "Light" << "System");
    appearanceForm->addRow("Theme:", themeCombo);
    
    fontSizeCombo = new QComboBox();
    fontSizeCombo->addItems(QStringList() << "Small" << "Medium" << "Large");
    appearanceForm->addRow("Font Size:", fontSizeCombo);
    
    appearanceLayout->addLayout(appearanceForm);
    appearanceLayout->addStretch();
    
    tabs->addTab(appearanceTab, "Appearance");
    
    // Advanced Tab
    QWidget *advancedTab = new QWidget();
    QVBoxLayout *advancedLayout = new QVBoxLayout(advancedTab);
    
    QGroupBox *performanceGroup = new QGroupBox("Performance");
    QVBoxLayout *performanceLayout = new QVBoxLayout(performanceGroup);
    
    hardwareAccelCheck = new QCheckBox("Hardware Acceleration");
    javascriptCheck = new QCheckBox("Enable JavaScript");
    pluginsCheck = new QCheckBox("Enable Plugins");
    
    performanceLayout->addWidget(hardwareAccelCheck);
    performanceLayout->addWidget(javascriptCheck);
    performanceLayout->addWidget(pluginsCheck);
    
    advancedLayout->addWidget(performanceGroup);
    advancedLayout->addStretch();
    
    tabs->addTab(advancedTab, "Advanced");
    
    mainLayout->addWidget(tabs);
    
    // Buttons
    QHBoxLayout *buttonLayout = new QHBoxLayout();
    buttonLayout->addStretch();
    
    QPushButton *saveBtn = new QPushButton("Save");
    connect(saveBtn, &QPushButton::clicked, this, &SettingsDialog::onSave);
    buttonLayout->addWidget(saveBtn);
    
    QPushButton *cancelBtn = new QPushButton("Cancel");
    connect(cancelBtn, &QPushButton::clicked, this, &SettingsDialog::onCancel);
    buttonLayout->addWidget(cancelBtn);
    
    mainLayout->addLayout(buttonLayout);
}

void SettingsDialog::loadSettings()
{
    QJsonObject settings = dataManager->getSettings();
    
    // Privacy settings
    adBlockingCheck->setChecked(settings.value("adBlocking").toBool(true));
    trackingProtectionCheck->setChecked(settings.value("trackingProtection").toBool(true));
    fingerprintProtectionCheck->setChecked(settings.value("fingerprintProtection").toBool(true));
    cookieBlockingCheck->setChecked(settings.value("cookieBlocking").toBool(true));
    blockAllCookiesCheck->setChecked(settings.value("blockAllCookies").toBool(true));
    blockFontsCheck->setChecked(settings.value("blockFonts").toBool(true));
    blockCameraCheck->setChecked(settings.value("blockCamera").toBool(true));
    blockMicrophoneCheck->setChecked(settings.value("blockMicrophone").toBool(true));
    blockGeolocationCheck->setChecked(settings.value("blockGeolocation").toBool(true));
    blockNotificationsCheck->setChecked(settings.value("blockNotifications").toBool(true));
    
    // Appearance
    QString theme = settings.value("theme").toString("dark");
    if (theme == "dark") themeCombo->setCurrentIndex(0);
    else if (theme == "light") themeCombo->setCurrentIndex(1);
    else themeCombo->setCurrentIndex(2);
}

void SettingsDialog::saveSettings()
{
    QJsonObject settings;
    
    // Privacy
    settings["adBlocking"] = adBlockingCheck->isChecked();
    settings["trackingProtection"] = trackingProtectionCheck->isChecked();
    settings["fingerprintProtection"] = fingerprintProtectionCheck->isChecked();
    settings["cookieBlocking"] = cookieBlockingCheck->isChecked();
    settings["blockAllCookies"] = blockAllCookiesCheck->isChecked();
    settings["blockFonts"] = blockFontsCheck->isChecked();
    settings["blockCamera"] = blockCameraCheck->isChecked();
    settings["blockMicrophone"] = blockMicrophoneCheck->isChecked();
    settings["blockGeolocation"] = blockGeolocationCheck->isChecked();
    settings["blockNotifications"] = blockNotificationsCheck->isChecked();
    
    // Appearance
    QString theme = themeCombo->currentText().toLower();
    settings["theme"] = theme;
    
    dataManager->setSettings(settings);
    
    // Apply privacy settings
    if (privacyEngine) {
        privacyEngine->setAdBlocking(adBlockingCheck->isChecked());
        privacyEngine->setTrackingProtection(trackingProtectionCheck->isChecked());
        privacyEngine->setFingerprintProtection(fingerprintProtectionCheck->isChecked());
        privacyEngine->setCookieBlocking(cookieBlockingCheck->isChecked());
        privacyEngine->setBlockAllCookies(blockAllCookiesCheck->isChecked());
        privacyEngine->setBlockFonts(blockFontsCheck->isChecked());
        privacyEngine->setBlockCamera(blockCameraCheck->isChecked());
        privacyEngine->setBlockMicrophone(blockMicrophoneCheck->isChecked());
        privacyEngine->setBlockGeolocation(blockGeolocationCheck->isChecked());
        privacyEngine->setBlockNotifications(blockNotificationsCheck->isChecked());
    }
    
    // Apply search engine
    if (searchManager) {
        QString keyword = defaultSearchCombo->currentData().toString();
        if (!keyword.isEmpty()) {
            searchManager->setDefaultEngine(keyword);
        }
    }
}

void SettingsDialog::onSave()
{
    saveSettings();
    accept();
}

void SettingsDialog::onCancel()
{
    reject();
}

void SettingsDialog::onPrivacyChanged()
{
    // Update privacy engine in real-time
}

void SettingsDialog::onSearchEngineChanged()
{
    // Update search manager
}

#ifndef SETTINGSDIALOG_H
#define SETTINGSDIALOG_H

#include <QDialog>
#include <QTabWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QCheckBox>
#include <QComboBox>
#include <QLineEdit>
#include <QPushButton>
#include <QGroupBox>
#include <QSpinBox>
#include <QSlider>
#include "datamanager.h"
#include "privacyengine.h"
#include "searchmanager.h"

class SettingsDialog : public QDialog
{
    Q_OBJECT

public:
    explicit SettingsDialog(DataManager *dataManager, PrivacyEngine *privacyEngine, SearchManager *searchManager, QWidget *parent = nullptr);

private slots:
    void onSave();
    void onCancel();
    void onPrivacyChanged();
    void onSearchEngineChanged();

private:
    void setupUI();
    void loadSettings();
    void saveSettings();
    
    DataManager *dataManager;
    PrivacyEngine *privacyEngine;
    SearchManager *searchManager;
    
    QTabWidget *tabs;
    
    // Privacy tab
    QCheckBox *adBlockingCheck;
    QCheckBox *trackingProtectionCheck;
    QCheckBox *fingerprintProtectionCheck;
    QCheckBox *cookieBlockingCheck;
    QCheckBox *blockAllCookiesCheck;
    QCheckBox *blockFontsCheck;
    QCheckBox *blockCameraCheck;
    QCheckBox *blockMicrophoneCheck;
    QCheckBox *blockGeolocationCheck;
    QCheckBox *blockNotificationsCheck;
    
    // Search tab
    QComboBox *defaultSearchCombo;
    QPushButton *addSearchEngineBtn;
    QPushButton *editSearchEngineBtn;
    QPushButton *removeSearchEngineBtn;
    
    // Appearance tab
    QComboBox *themeCombo;
    QComboBox *fontSizeCombo;
    
    // Advanced tab
    QCheckBox *hardwareAccelCheck;
    QCheckBox *javascriptCheck;
    QCheckBox *pluginsCheck;
};

#endif // SETTINGSDIALOG_H

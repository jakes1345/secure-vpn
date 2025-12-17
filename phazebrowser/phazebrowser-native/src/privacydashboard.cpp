#include "privacydashboard.h"
#include "privacyengine.h"
#include <QJsonObject>
#include <QHeaderView>
#include <QTimer>
#include <QMessageBox>

PrivacyDashboard::PrivacyDashboard(PrivacyEngine *privacyEngine, QWidget *parent)
    : QDialog(parent)
    , privacyEngine(privacyEngine)
{
    setWindowTitle("Privacy Dashboard");
    setMinimumSize(700, 600);
    setupUI();
    
    updateStats();
    
    // Auto-update every 2 seconds
    updateTimer = new QTimer(this);
    connect(updateTimer, &QTimer::timeout, this, &PrivacyDashboard::updateStats);
    updateTimer->start(2000);
}

void PrivacyDashboard::setupUI()
{
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    
    // Header
    QLabel *header = new QLabel("👻 Privacy Dashboard");
    QFont headerFont = header->font();
    headerFont.setPointSize(18);
    headerFont.setBold(true);
    header->setFont(headerFont);
    mainLayout->addWidget(header);
    
    // Stats section
    QGroupBox *statsGroup = new QGroupBox("Privacy Statistics");
    QGridLayout *statsLayout = new QGridLayout(statsGroup);
    
    adsBlockedLabel = new QLabel("0");
    trackersBlockedLabel = new QLabel("0");
    cookiesBlockedLabel = new QLabel("0");
    requestsBlockedLabel = new QLabel("0");
    domainsBlockedLabel = new QLabel("0");
    
    statsLayout->addWidget(new QLabel("🚫 Ads Blocked:"), 0, 0);
    statsLayout->addWidget(adsBlockedLabel, 0, 1);
    statsLayout->addWidget(new QLabel("🛡️ Trackers Blocked:"), 1, 0);
    statsLayout->addWidget(trackersBlockedLabel, 1, 1);
    statsLayout->addWidget(new QLabel("🍪 Cookies Blocked:"), 2, 0);
    statsLayout->addWidget(cookiesBlockedLabel, 2, 1);
    statsLayout->addWidget(new QLabel("🚫 Requests Blocked:"), 3, 0);
    statsLayout->addWidget(requestsBlockedLabel, 3, 1);
    statsLayout->addWidget(new QLabel("🌐 Domains Blocked:"), 4, 0);
    statsLayout->addWidget(domainsBlockedLabel, 4, 1);
    
    mainLayout->addWidget(statsGroup);
    
    // Protection status
    QGroupBox *protectionGroup = new QGroupBox("Active Protections");
    QVBoxLayout *protectionLayout = new QVBoxLayout(protectionGroup);
    
    adBlockingStatus = new QLabel("✅ Ad Blocking: ON");
    trackingProtectionStatus = new QLabel("✅ Tracking Protection: ON");
    fingerprintProtectionStatus = new QLabel("✅ Fingerprint Protection: ON");
    cookieBlockingStatus = new QLabel("✅ Cookie Blocking: ON");
    
    protectionLayout->addWidget(adBlockingStatus);
    protectionLayout->addWidget(trackingProtectionStatus);
    protectionLayout->addWidget(fingerprintProtectionStatus);
    protectionLayout->addWidget(cookieBlockingStatus);
    
    mainLayout->addWidget(protectionGroup);
    
    // Blocked domains
    QGroupBox *domainsGroup = new QGroupBox("Blocked Domains");
    QVBoxLayout *domainsLayout = new QVBoxLayout(domainsGroup);
    
    domainsTable = new QTableWidget(this);
    domainsTable->setColumnCount(1);
    domainsTable->setHorizontalHeaderLabels(QStringList() << "Domain");
    domainsTable->horizontalHeader()->setStretchLastSection(true);
    domainsTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    domainsTable->setStyleSheet(
        "QTableWidget { background: #1e1e1e; color: white; gridline-color: #404040; }"
        "QHeaderView::section { background: #2d2d2d; color: white; padding: 8px; }"
    );
    domainsLayout->addWidget(domainsTable);
    
    mainLayout->addWidget(domainsGroup);
    
    // Buttons
    QHBoxLayout *buttonLayout = new QHBoxLayout();
    buttonLayout->addStretch();
    
    QPushButton *resetBtn = new QPushButton("🔄 Reset Stats");
    connect(resetBtn, &QPushButton::clicked, this, &PrivacyDashboard::onResetStats);
    buttonLayout->addWidget(resetBtn);
    
    QPushButton *closeBtn = new QPushButton("Close");
    connect(closeBtn, &QPushButton::clicked, this, &QDialog::accept);
    buttonLayout->addWidget(closeBtn);
    
    mainLayout->addLayout(buttonLayout);
}

void PrivacyDashboard::updateStats()
{
    QJsonObject stats = privacyEngine->getPrivacyStats();
    
    adsBlockedLabel->setText(QString::number(stats["adsBlocked"].toInt()));
    trackersBlockedLabel->setText(QString::number(stats["trackersBlocked"].toInt()));
    cookiesBlockedLabel->setText(QString::number(stats["cookiesBlocked"].toInt()));
    requestsBlockedLabel->setText(QString::number(stats["requestsBlocked"].toInt()));
    domainsBlockedLabel->setText(QString::number(stats["domainsBlocked"].toInt()));
    
    // Update blocked domains table (placeholder - need to get actual domains from privacy engine)
    // TODO: Get actual blocked domains list
}

void PrivacyDashboard::onResetStats()
{
    int ret = QMessageBox::question(this, "Reset Stats", "Are you sure you want to reset all privacy statistics?");
    if (ret == QMessageBox::Yes) {
        privacyEngine->resetStats();
        updateStats();
    }
}
